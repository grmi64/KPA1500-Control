"""One amplifier owner in an isolated worker process; HTTP reads cached state only."""
import glob,json,multiprocessing,queue,threading,time,uuid,signal
from pathlib import Path
from protocol import Session
from transport import SerialTransport,BAUDS
from simulator import SimulatorTransport
ACTIONS={'operate','standby','antenna_1','antenna_2','antenna_next','atu_in','atu_bypass','tune','cancel_tune','clear_fault','demo_tx_on','demo_tx_off'}
def ports():return sorted(set(glob.glob('/dev/cu.usbserial*')+glob.glob('/dev/cu.usbmodem*')))
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
  demo=config['mode']=='simulator';transport=SimulatorTransport() if demo else SerialTransport(config['port'],config['baud'])
  amp=Session(transport,cancelled=stop.is_set);amp.identify();slow_at=0
  while not stop.is_set():
   now=time.monotonic();amp.poll(slow=now>=slow_at)
   if now>=slow_at:slow_at=now+4
   events.put(('state',dict(amp.snapshot(),demo=demo)))
   if amp.last_live and time.time()-amp.last_live>8:raise TimeoutError('Amplifier stopped responding. Connection closed; reconnect when ready.')
   for _ in range(4):
    if stop.is_set():break
    try:item=commands.get_nowait()
    except queue.Empty:break
    try:
     if time.time()>item['expires']:raise ValueError('Request expired; no command sent.')
     name=item['action']
     if name.startswith('demo_tx_'):
      if not demo:raise ValueError('Simulation control is unavailable on USB.')
      transport.tx=name=='demo_tx_on';result={'status':'confirmed','message':'Simulator transmit state changed.'}
     else:result=amp.action(name)
     result.update(id=item['id'],action=name)
    except (ValueError,OSError,TimeoutError) as exc:result={'id':item['id'],'action':item['action'],'status':'failed','message':str(exc)}
    events.put(('action',result));events.put(('state',dict(amp.snapshot(),demo=demo)))
   stop.wait(.25)
 except Exception as exc:events.put(('error',str(exc)))
 finally:
  if transport:transport.close()

class Controller:
 def __init__(self,settings):
  self.settings=Path(settings);self.guard=threading.RLock();self.operation=threading.Lock();self.worker=None;self.events=None;self.commands=None;self.stop=None;self.generation=uuid.uuid4().hex;self.received=0;self.state={};self.action_log=[];self.fault_log=[];self.last_fault=None
  self.config={'mode':'usb','port':'','baud':230400,'auto_connect':False}
  try:
   saved=json.loads(self.settings.read_text());self.config.update({k:saved[k] for k in ('port','baud') if k in saved});self.config['auto_connect']=saved.get('auto_connect') is True
  except (OSError,ValueError):pass
  self.clear('disconnected','Choose the amplifier’s Host PC USB port and click Connect, or try Simulator.')
 def clear(self,status,message):self.state={'status':status,'message':message,'demo':False};self.received=0
 def save_settings(self,value):
  port=value.get('port','');baud=value.get('baud',230400);automatic=value.get('auto_connect',False)
  if type(automatic) is not bool or type(baud) is not int or baud not in BAUDS:raise ValueError('Invalid startup connection settings.')
  if not isinstance(port,str) or (port and (not port.startswith('/dev/cu.') or '/' in port[8:])) or (automatic and not port):raise ValueError('Select the amplifier Host PC USB port before enabling auto-connect.')
  self.settings.parent.mkdir(parents=True,exist_ok=True);tmp=self.settings.with_suffix('.tmp');tmp.write_text(json.dumps(dict(port=port,baud=baud,auto_connect=automatic)));tmp.replace(self.settings)
  self.config['auto_connect']=automatic
 def startup(self):
  if self.config['auto_connect']:
   try:self.connect(dict(self.config,mode='usb'))
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
 def connect(self,value):
  mode=value.get('mode');port=value.get('port','');baud=value.get('baud',230400)
  if mode not in ('usb','simulator'):raise ValueError('Choose USB or Simulator. TCP/IP will be added later.')
  if type(baud) is not int or baud not in BAUDS:raise ValueError('Select a supported baud rate.')
  if mode=='usb' and (not isinstance(port,str) or not port.startswith('/dev/cu.') or '/' in port[8:]):raise ValueError('Select the amplifier Host PC USB port.')
  with self.operation:
   self._disconnect();self.config={'mode':mode,'port':port,'baud':baud,'auto_connect':self.config['auto_connect']}
   if mode=='usb':
    self.save_settings(self.config)
   self.events=multiprocessing.Queue();self.commands=multiprocessing.Queue(maxsize=8);self.stop=StopFlag()
   with self.guard:self.clear('connecting','Identifying amplifier…');self.state['demo']=mode=='simulator'
   self.worker=multiprocessing.Process(target=worker_main,args=(self.config,self.events,self.commands,self.stop),daemon=True);self.worker.start()
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
    elif kind=='error':self.clear('error',data)
  if self.worker and not self.worker.is_alive() and self.state['status'] not in ('error','disconnected'):self.clear('error','Amplifier reader stopped. Reconnect when ready.')
 def snapshot(self):
  with self.guard:
   self.pump();state=dict(self.state)
   age=state.get('age_seconds')
   if age is not None:state['age_seconds']=age+max(0,time.time()-self.received)
   if state.get('status')=='live' and state.get('age_seconds',99)>=2.5:state.update(status='stale',message='Amplifier readings are stale.')
   if state.get('status')!='live':
    for key in ('forward_watts','reflected_watts','swr','temperature_c','input_watts','voltage_v','current_a','transmitting','operate','antenna','atu_enabled','atu_inline','tuning'):state[key]=None
   return dict(schema_version=1,model='KPA1500',generation=self.generation,state=state,connection=dict(self.config),actions=list(self.action_log),faults=list(self.fault_log))
 def action(self,value):
  with self.guard:
   snapshot=self.snapshot();name=value.get('action')
   if name not in ACTIONS:raise ValueError('Unknown operating control.')
   if value.get('generation')!=self.generation:raise ValueError('Connection changed. Refresh before sending another command.')
   if not self.worker or snapshot['state']['status']!='live':raise ValueError('A live connection is required.')
   if any(a['status']=='queued' for a in self.action_log):raise ValueError('An operating request is already pending.')
   item={'id':uuid.uuid4().hex,'action':name,'expires':time.time()+3}
   try:self.commands.put_nowait(item)
   except queue.Full:raise ValueError('Amplifier request queue is busy.')
   result={'id':item['id'],'action':name,'status':'queued','message':'Checking amplifier and sending request…'};self.action_log=[result]+self.action_log[:29];return result
