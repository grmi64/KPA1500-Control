"""One amplifier owner in an isolated worker process; HTTP reads cached state only."""
import glob,json,multiprocessing,queue,threading,time,uuid,signal
from pathlib import Path
from protocol import Session
from version import VERSION
from transport import SerialTransport,TCPTransport,tcp_endpoint,BAUDS
from simulator import SimulatorTransport
from platform_paths import ports,serial_port
from power import mac_address,wake_address,wake_connect
ACTIONS={'power_on','power_off','operate','standby','antenna_1','antenna_2','antenna_next','atu_in','atu_bypass','tune','cancel_tune','clear_fault','demo_tx_on','demo_tx_off'}
ACTIONS.update('fan_'+str(n) for n in range(6))
class StopFlag:
 # No process-shared condition lock can be stranded by a terminating reader.
 def __init__(self):self.value=multiprocessing.Value('b',0,lock=False)
 def set(self):self.value.value=1
 def is_set(self):return bool(self.value.value)
 def wait(self,seconds):
  deadline=time.monotonic()+seconds
  while not self.is_set() and time.monotonic()<deadline:time.sleep(min(.025,max(0,deadline-time.monotonic())))
  return self.is_set()
def worker_main(config,events,commands,stop):
 signal.signal(signal.SIGINT,signal.SIG_IGN)
 signal.signal(signal.SIGTERM,signal.SIG_DFL)
 # State is disposable on shutdown; never wait for an undrained UI queue.
 events.cancel_join_thread()
 transport=None
 try:
  demo=config['mode']=='simulator'
  if demo:transport=SimulatorTransport()
  elif config['mode']=='tcp':transport=wake_connect(config,stop.is_set,TCPTransport,stop.wait) if config.get('wake_request') else TCPTransport(config['host'],config['tcp_port'])
  else:transport=SerialTransport(config['port'],config['baud'])
  amp=Session(transport,cancelled=stop.is_set)
  if config.get('wake_request'):
   amp.read('MA')
   if amp.values.get('mac_address')!=config['wake_mac']:raise ValueError('Wake connection MAC address did not match the selected amplifier. No power command sent.')
  if config.get('power_request'):
   result=amp.power_on(usb=config['mode']=='usb',wake_only=config.get('wake_request',False))
   result.update(id=config['power_request'],action='power_on');events.put(('action',result))
  amp.read('ON')
  if amp.values.get('powered_on') is not False:amp.identify()
  amp.read('MA');amp.read('WL')
  if not demo and amp.values.get('mac_address'):events.put(('identity',amp.values['mac_address']))
  slow_at=0
  while not stop.is_set():
   now=time.monotonic();amp.poll(slow=now>=slow_at)
   if now>=slow_at:slow_at=now+4
   events.put(('state',dict(amp.snapshot(),demo=demo)))
   if amp.snapshot()['status']!='powered_off' and amp.last_live and time.time()-amp.last_live>8:raise TimeoutError('Amplifier stopped responding. Connection closed; reconnect when ready.')
   for _ in range(4):
    if stop.is_set():break
    try:item=commands.get_nowait()
    except queue.Empty:break
    try:
     if time.time()>item['expires']:raise ValueError('Request expired; no command sent.')
     name=item['action']
     if name.startswith('demo_tx_'):
      if not demo:raise ValueError('Simulation control is unavailable on hardware connections.')
      transport.tx=name=='demo_tx_on';result={'status':'confirmed','message':'Simulator transmit state changed.'}
     elif name=='power_on':result=amp.power_on(usb=config['mode']=='usb')
     else:result=amp.action(name)
     result.update(id=item['id'],action=name)
    except (ValueError,OSError,TimeoutError) as exc:result={'id':item['id'],'action':item['action'],'status':'failed','message':str(exc)}
    events.put(('action',result));events.put(('state',dict(amp.snapshot(),demo=demo)))
    if item['action']=='power_off' and result['status'] in ('confirmed','unconfirmed') and config['mode']=='tcp':
     events.put(('terminal',dict(status='powered_off' if result['status']=='confirmed' else 'disconnected',powered_on=False if result['status']=='confirmed' else None,message=result['message'],demo=False)));return
   stop.wait(.25)
 except Exception as exc:
  if config.get('power_request'):events.put(('action',{'id':config['power_request'],'action':'power_on','status':'failed','message':str(exc)}))
  events.put(('error',str(exc)))
 finally:
  if transport:transport.close()

class Controller:
 def __init__(self,settings,offline_only=False):
  self.offline_only=offline_only
  self.settings=Path(settings);self.guard=threading.RLock();self.operation=threading.Lock();self.worker=None;self.events=None;self.commands=None;self.stop=None;self.generation=uuid.uuid4().hex;self.received=0;self.state={};self.action_log=[];self.fault_log=[];self.last_fault=None
  self.config={'mode':'usb','port':'','baud':230400,'auto_connect':False,'share_readings':False,'host':'','tcp_port':1500,'wake_mac':'','wake_broadcast':'255.255.255.255'}
  try:
   saved=json.loads(self.settings.read_text());saved=saved if isinstance(saved,dict) else {};self.config.update({k:saved[k] for k in ('port','baud','host','tcp_port','wake_mac','wake_broadcast') if k in saved});self.config['auto_connect']=saved.get('auto_connect') is True;self.config['share_readings']=saved.get('share_readings') is True
  except (OSError,ValueError):saved={}
  self.startup_mode=saved.get('mode','usb') if isinstance(saved,dict) else 'usb'
  if self.startup_mode not in ('usb','tcp'):self.startup_mode='usb'
  if self.offline_only:self.config.update(auto_connect=False,share_readings=False)
  self.config['mode']=self.startup_mode
  self.clear('disconnected','Choose USB or TCP/IP and click Connect, or try Simulator.')
 def clear(self,status,message):self.state={'status':status,'message':message,'demo':self.offline_only};self.received=0
 def save_settings(self,value):
  port=value.get('port',self.config['port']);baud=value.get('baud',self.config['baud']);automatic=value.get('auto_connect',self.config['auto_connect']);sharing=value.get('share_readings',self.config['share_readings'])
  mode=value.get('mode',self.startup_mode);host=value.get('host',self.config['host']);tcp_port=value.get('tcp_port',self.config['tcp_port'])
  if mode not in ('usb','tcp'):raise ValueError('Choose USB or TCP/IP for startup.')
  if type(sharing) is not bool:raise ValueError('Choose whether to share amplifier readings.')
  if type(automatic) is not bool or type(baud) is not int or baud not in BAUDS:raise ValueError('Invalid startup connection settings.')
  if port:port=serial_port(port)
  if automatic and mode=='usb' and not port:raise ValueError('Select the amplifier Host PC USB port before enabling auto-connect.')
  if self.offline_only and (automatic or sharing):raise ValueError('Offline simulation cannot enable startup connections or sharing.')
  if host or mode=='tcp':host,tcp_port=tcp_endpoint(host,tcp_port)
  elif type(tcp_port) is not int or not 1<=tcp_port<=65535:raise ValueError('Enter a TCP port from 1 to 65535.')
  mac=value.get('wake_mac',self.config['wake_mac']);broadcast=value.get('wake_broadcast',self.config['wake_broadcast'])
  if host!=self.config['host'] and mac==self.config.get('wake_mac'):mac=''
  if mac:mac=mac_address(mac)
  broadcast=wake_address(broadcast)
  saved=dict(wake_mac=mac,wake_broadcast=broadcast,mode=mode,port=port,baud=baud,host=host,tcp_port=tcp_port,auto_connect=automatic,share_readings=sharing)
  self.settings.parent.mkdir(parents=True,exist_ok=True);tmp=self.settings.with_suffix('.tmp');tmp.write_text(json.dumps(saved));tmp.replace(self.settings)
  self.startup_mode=mode;self.config.update({k:v for k,v in saved.items() if k!='mode'})
  if self.worker is None:self.config['mode']=mode
 def startup(self):
  if self.offline_only:return
  if self.config['auto_connect']:
   try:self.connect(dict(self.config,mode=self.startup_mode))
   except (ValueError,OSError) as exc:self.clear('error','Startup connection failed: '+str(exc)+'. Connect manually when ready.')
 def disconnect(self):
  with self.operation:self._disconnect()
 def _disconnect(self):
  if self.worker:
   self.stop.set();self.worker.join(timeout=2)
   if self.worker.is_alive():self.worker.terminate();self.worker.join(timeout=1)
   if self.worker.is_alive():self.worker.kill();self.worker.join(timeout=1)
   if self.worker.is_alive():raise RuntimeError('Amplifier worker did not stop. Close the app before reconnecting.')
   self.worker=None
  for channel in (self.events,self.commands):
   if channel:channel.cancel_join_thread();channel.close()
  self.events=None;self.commands=None
  with self.guard:
   self.generation=uuid.uuid4().hex;self.clear('disconnected','Amplifier disconnected.');self.action_log=[]
 def connect(self,value,power_request=None):
  mode=value.get('mode');port=value.get('port',self.config['port']);baud=value.get('baud',self.config['baud']);host=value.get('host',self.config['host']);tcp_port=value.get('tcp_port',self.config['tcp_port'])
  if mode not in ('usb','tcp','simulator'):raise ValueError('Choose USB, TCP/IP or Simulator.')
  if mode=='tcp':host,tcp_port=tcp_endpoint(host,tcp_port)
  if type(baud) is not int or baud not in BAUDS:raise ValueError('Select a supported baud rate.')
  if self.offline_only and mode!='simulator':raise ValueError('This session is offline simulation only. No hardware connection is allowed.')
  if mode=='usb':port=serial_port(port)
  with self.operation:
   if mode!='simulator':self.save_settings(dict(mode=mode,port=port,baud=baud,host=host,tcp_port=tcp_port))
   self._disconnect();self.config.update(mode=mode,port=port,baud=baud,host=host,tcp_port=tcp_port)
   self.events=multiprocessing.Queue();self.commands=multiprocessing.Queue(maxsize=8);self.stop=StopFlag()
   with self.guard:self.clear('connecting','Identifying amplifier…');self.state['demo']=mode=='simulator'
   worker_config=dict(self.config,power_request=power_request,wake_request=bool(power_request and mode=='tcp'))
   self.worker=multiprocessing.Process(target=worker_main,args=(worker_config,self.events,self.commands,self.stop),daemon=True);self.worker.start()
  return self.snapshot()
 def pump(self):
  if self.events:
   for _ in range(100):
    try:kind,data=self.events.get_nowait()
    except queue.Empty:break
    if kind=='state':
     self.state=data;self.received=time.time()
     fault=data.get('fault_code')
     if fault and fault!='00' and fault!=self.last_fault:self.fault_log=([{'code':fault,'message':data.get('fault','Unknown fault'),'at':time.time()}]+self.fault_log)[:30]
     self.last_fault=fault
    elif kind=='action':
     self.action_log=[data]+[a for a in self.action_log if a['id']!=data['id']];self.action_log=self.action_log[:30]
    elif kind=='identity':
     try:
      mac=mac_address(data)
      if mac!=self.config.get('wake_mac'):self.save_settings({'wake_mac':mac})
     except (OSError,ValueError):pass
    elif kind=='terminal':self.state=data;self.received=time.time()
    elif kind=='error':self.clear('error',data)
  if self.worker and not self.worker.is_alive() and self.state['status'] not in ('error','disconnected','powered_off'):self.clear('error','Amplifier reader stopped. Reconnect when ready.')
 def snapshot(self):
  with self.guard:
   self.pump();state=dict(self.state)
   age=state.get('age_seconds')
   if age is not None:state['age_seconds']=age+max(0,time.time()-self.received)
   if state.get('status')=='live' and state.get('age_seconds',99)>=2.5:state.update(status='stale',message='Amplifier readings are stale.')
   if state.get('status')!='live':
    for key in ('forward_watts','reflected_watts','swr','temperature_c','input_watts','voltage_v','current_a','transmitting','operate','antenna','atu_enabled','atu_inline','tuning','fan_minimum','fan_speed'):state[key]=None
   return dict(app_version=VERSION,schema_version=1,offline_only=self.offline_only,model='KPA1500',generation=self.generation,state=state,connection=dict(self.config),actions=list(self.action_log),faults=list(self.fault_log))
 def telemetry(self):
  # Only cached state crosses this boundary; no USB reads or operating commands.
  if not self.config['share_readings']:raise PermissionError('Enable Share readings with DX Caliber in KPA1500 Control.')
  state=self.snapshot()['state']
  keys=('status','age_seconds','forward_watts','reflected_watts','swr','temperature_c','operate','antenna','atu_enabled','demo')
  return dict(schema_version=1,model='KPA1500',**{key:state.get(key) for key in keys})
 def action(self,value):
  with self.guard:
   snapshot=self.snapshot();name=value.get('action')
   if name not in ACTIONS:raise ValueError('Unknown operating control.')
   if name=='power_off' and value.get('confirm_power_off') is not True:raise ValueError('Confirm Power Off before sending the request.')
   if value.get('generation')!=self.generation:raise ValueError('Connection changed. Refresh before sending another command.')
   if name=='power_on' and snapshot['state']['status'] in ('disconnected','error','powered_off') and (not self.worker or not self.worker.is_alive()):
    if any(a['status']=='queued' for a in self.action_log):raise ValueError('An operating request is already pending.')
    if self.config['mode']=='tcp' and not self.config['wake_mac']:raise ValueError('Save the amplifier MAC address in Connection before Ethernet Power On.')
    request_id=uuid.uuid4().hex
    self.connect(dict(self.config),power_request=request_id)
    result={'id':request_id,'action':name,'status':'queued','message':'Power on requested; waiting for amplifier confirmation. Startup mode follows amplifier settings.'};self.action_log=[result];return result
   if not self.worker or (snapshot['state']['status']!='live' and not (name=='power_on' and snapshot['state']['status']=='powered_off')):raise ValueError('A live connection is required.')
   if any(a['status']=='queued' for a in self.action_log):raise ValueError('An operating request is already pending.')
   item={'id':uuid.uuid4().hex,'action':name,'expires':time.time()+3}
   try:self.commands.put_nowait(item)
   except queue.Full:raise ValueError('Amplifier request queue is busy.')
   result={'id':item['id'],'action':name,'status':'queued','message':'Checking amplifier and sending request…'};self.action_log=[result]+self.action_log[:29];return result
