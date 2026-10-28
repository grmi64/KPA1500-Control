"""Explicit Windows launch modes. This module never opens a transport."""
import os,subprocess,sys,threading
from pathlib import Path
from platform_paths import serial_port,settings_path
from transport import BAUDS,tcp_endpoint
MODES={'simulation':'Simulation','read-only':'Read-only telemetry','hardware':'Hardware control'}
def mode_settings(base,mode):
 if mode not in MODES:raise ValueError('Choose Simulation, Read-only or Hardware control.')
 base=settings_path(base)
 return base if mode=='simulation' else base.with_name(base.stem+'.'+mode+base.suffix)
def prepare_reopen(value,snapshot,base):
 if not isinstance(value,dict) or value.get('mode') not in MODES:raise ValueError('Choose Simulation, Read-only or Hardware control.')
 if snapshot['state']['status']!='disconnected' or any(a.get('status')=='queued' for a in snapshot['actions']):raise ValueError('Disconnect before changing launch mode.')
 mode=value['mode']
 if value.get('confirmed') is not True:raise ValueError('Confirm reopening in the selected launch mode.')
 args=[{'simulation':'--demo','read-only':'--read-only','hardware':'--hardware'}[mode],'--mode-handoff','--http-port','0','--settings='+str(settings_path(base))]
 if mode!='simulation':
  connection=value.get('connection')
  if not isinstance(connection,dict) or connection.get('mode') not in ('usb','tcp'):raise ValueError('Select USB or TCP/IP and enter its connection details above.')
  baud=connection.get('baud',230400)
  if type(baud) is not int or baud not in BAUDS:raise ValueError('Select a supported baud rate.')
  args+=['--connection-type='+connection['mode'],'--baud',str(baud)]
  if connection['mode']=='usb':
   if connection.get('port'):args+=['--usb-port='+serial_port(connection['port'])]
  else:
   host,port=tcp_endpoint(connection.get('host'),connection.get('tcp_port'))
   args+=['--host='+host,'--tcp-port',str(port)]
 return args
class LaunchWorkflow:
 def __init__(self,controller,discovery,base,mode,restricted=False):
  self.controller=controller;self.discovery=discovery;self.base=base;self.mode=mode;self.restricted=restricted;self.pending=None;self.lock=threading.Lock()
 def info(self):return dict(mode=self.mode,label=MODES[self.mode],allowed=not self.restricted)
 def request(self,value):
  with self.lock,self.controller.guard:
   if not self.controller.operation.acquire(blocking=False):raise ValueError('A connection change is in progress. Wait for it to finish.')
   try:
    if self.restricted:raise ValueError('Launch mode changes are disabled in automated smoke tests.')
    if self.pending is not None:raise ValueError('A mode change is already pending.')
    if self.controller.worker is not None or self.discovery.snapshot()['running']:raise ValueError('Disconnect and finish discovery before changing launch mode.')
    args=prepare_reopen(value,self.controller.snapshot(),self.base)
    self.controller.launch_pending=True;self.pending=args
    return {'reopening':True}
   finally:self.controller.operation.release()
def launch_replacement(args):
 command=[sys.executable]
 if not getattr(sys,'frozen',False):command.append(str(Path(__file__).with_name('windows_app.py')))
 subprocess.Popen(command+args,shell=False,close_fds=True,env={**os.environ,'PYINSTALLER_RESET_ENVIRONMENT':'1'})
