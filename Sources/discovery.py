"""User-requested, bounded identification only. Never sends operating commands."""
import concurrent.futures,ipaddress,subprocess,threading
from protocol import Protocol
from transport import SerialTransport,TCPTransport,BAUDS

def local_targets():
 """At most 254 addresses on the default local IPv4 interface; no routed scan."""
 route=subprocess.run(['/sbin/route','-n','get','default'],capture_output=True,text=True,timeout=2,check=True).stdout
 interface=next((line.split(':',1)[1].strip() for line in route.splitlines() if line.strip().startswith('interface:')),None)
 if not interface or not interface.isalnum():raise ValueError('No local network interface found. Use manual connection settings.')
 def read(key):return subprocess.run(['/usr/sbin/ipconfig',key,interface],capture_output=True,text=True,timeout=2,check=True).stdout.strip()
 address=ipaddress.IPv4Address(read('getifaddr'));mask=subprocess.run(['/usr/sbin/ipconfig','getoption',interface,'subnet_mask'],capture_output=True,text=True,timeout=2,check=True).stdout.strip()
 network=ipaddress.IPv4Network(str(address)+'/'+mask,strict=False)
 if network.prefixlen<24:network=ipaddress.IPv4Network(str(address)+'/24',strict=False)
 return [str(host) for host in network.hosts() if host!=address]

def identify(candidate,cancel,serial_factory=SerialTransport,tcp_factory=TCPTransport):
 if cancel.is_set():return None
 transport=None
 try:
  transport=serial_factory(candidate['port'],candidate['baud']) if candidate['mode']=='usb' else tcp_factory(candidate['host'],candidate['tcp_port'])
  if cancel.is_set():return None
  protocol=Protocol(transport)
  for attempt in range(3):
   if cancel.is_set():return None
   try:
    if protocol.query('I',.6).upper()=='^KPA1500;':return dict(candidate)
    return None
   except TimeoutError:
    if attempt==2:return None
 except (OSError,ValueError,UnicodeError):pass
 finally:
  if transport is not None:transport.close()
 return None

class Discovery:
 def __init__(self):self.lock=threading.RLock();self.cancel=threading.Event();self.running=False;self.results=[];self.message='';self.thread=None
 def snapshot(self):
  with self.lock:return dict(running=self.running,results=list(self.results),message=self.message)
 def start(self,usb_ports,baud,tcp_port):
  if type(baud) is not int or baud not in BAUDS:raise ValueError('Choose a supported USB baud rate.')
  if type(tcp_port) is not int or not 1<=tcp_port<=65535:raise ValueError('Choose a TCP port from 1 to 65535.')
  with self.lock:
   if self.running:raise ValueError('Discovery is already running.')
   self.running=True;self.results=[];self.message='Searching USB and the local network…';self.cancel=threading.Event()
   self.thread=threading.Thread(target=self.run,args=(list(usb_ports)[:16],baud,tcp_port),daemon=True);self.thread.start()
  return self.snapshot()
 def stop(self):self.cancel.set();return self.snapshot()
 def run(self,usb_ports,baud,tcp_port):
  warning='';failures=0
  try:
   candidates=[dict(mode='usb',port=p,baud=baud) for p in usb_ports]
   try:candidates += [dict(mode='tcp',host=h,tcp_port=tcp_port) for h in local_targets()]
   except (OSError,ValueError,subprocess.SubprocessError):warning=' Local network discovery unavailable; use manual IP settings.'
   with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
    pending=[pool.submit(identify,c,self.cancel) for c in candidates]
    for future in concurrent.futures.as_completed(pending):
     try:result=future.result()
     except Exception:
      failures+=1;continue
     if result and not self.cancel.is_set():
      with self.lock:self.results.append(result)
     if self.cancel.is_set():
      for item in pending:item.cancel()
      break
  except Exception:
   warning+=' Discovery could not finish. Try again or use manual connection settings.'
  finally:
   if failures:warning+=' Some connections could not be checked. If your amplifier is in the list, select it and click Connect. If it is missing, search again or enter its connection details manually.'
   with self.lock:self.running=False;self.message=('Discovery cancelled.' if self.cancel.is_set() else 'Discovery complete. Select a result, then click Connect.' if self.results else 'No available KPA1500 found. Check power, cabling, USB baud and other clients.')+warning
