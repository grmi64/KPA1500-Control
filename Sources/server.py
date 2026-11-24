"""Local, token-protected UI service. No radio/CAT sockets; opt-in USB startup."""
import argparse,json,multiprocessing,secrets,signal,threading,re
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from engine import Controller,ports
from discovery import Discovery
from platform_paths import data_directory
ROOT=Path(__file__).parent

def handler_for(controller,token,activate=None,simulate_discovery=False):
 discovery=Discovery(offline=simulate_discovery);dispatch=threading.Lock()
 control_token=secrets.token_urlsafe(32);control_requests={}
 prefix='/'+token+'/'
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def reply(self,status,data,mime='application/json'):
   if mime=='application/json':data=json.dumps(data).encode()
   try:
    self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'self'; base-uri 'none'");self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
   except (BrokenPipeError,ConnectionResetError):pass
  def host_ok(self):return self.headers.get('Host')=='127.0.0.1:'+str(self.server.server_port)
  def do_GET(self):
   if not self.host_ok():return self.reply(403,{'error':'Loopback host required.'})
   path=urlparse(self.path).path
   if path=='/api/v1/power':
    if self.headers.get('Origin'):return self.reply(403,{'error':'Backend requests only.'})
    try:return self.reply(200,dict(controller.shared_power(),control_token=control_token))
    except PermissionError as exc:return self.reply(403,{'error':str(exc)})
   if path=='/api/v1/controls':
    if self.headers.get('Origin'):return self.reply(403,{'error':'Backend requests only.'})
    try:return self.reply(200,dict(controller.shared_controls(),control_token=control_token))
    except PermissionError as exc:return self.reply(403,{'error':str(exc)})
   if path=='/api/v1/telemetry':
    try:return self.reply(200,controller.telemetry())
    except PermissionError as exc:return self.reply(403,{'error':str(exc)})
   if not path.startswith(prefix):return self.reply(404,{'error':'Not found.'})
   name=path[len(prefix):]
   if name=='state':return self.reply(200,controller.snapshot())
   if name=='discovery':return self.reply(200,discovery.snapshot())
   if name=='ports':return self.reply(200,{'ports':[] if controller.offline_only else ports()})
   assets={'':('index.html','text/html; charset=utf-8'),'measurements.js':('measurements.js','text/javascript; charset=utf-8'),'app.js':('app.js','text/javascript; charset=utf-8'),'app.css':('app.css','text/css; charset=utf-8'),'kpa_meter_colors.js':('kpa_meter_colors.js','text/javascript; charset=utf-8')}
   if name not in assets:return self.reply(404,{'error':'Not found.'})
   filename,mime=assets[name];return self.reply(200,(ROOT/filename).read_bytes(),mime)
  def do_POST(self):
   with dispatch:self.post()
  def post(self):
   if urlparse(self.path).path in ('/api/v1/controls','/api/v1/power'):return self.control_post()
   if not self.host_ok() or self.headers.get('X-Amp-Token')!=token:return self.reply(403,{'error':'Local session token required.'})
   origin=self.headers.get('Origin')
   if origin and origin!='http://127.0.0.1:'+str(self.server.server_port):return self.reply(403,{'error':'Foreign origin rejected.'})
   path=urlparse(self.path).path
   if not path.startswith(prefix):return self.reply(404,{'error':'Not found.'})
   try:
    length=int(self.headers.get('Content-Length','0'))
    if not 0<length<=4096:raise ValueError('Invalid request size.')
    value=json.loads(self.rfile.read(length))
    if not isinstance(value,dict):raise ValueError('Expected an object.')
    action=path[len(prefix):]
    if action=='discover':
     if controller.offline_only and not simulate_discovery:raise ValueError('Discovery is disabled in offline simulation. No device or network probes sent.')
     with controller.operation:
      if controller.launch_pending:raise ValueError('A launch mode change is pending. No discovery started.')
      if controller.snapshot()['state']['status'] not in ('disconnected','error'):raise ValueError('Disconnect the amplifier before discovery.')
      result=discovery.start([] if controller.offline_only else ports(),value.get('baud',230400),value.get('tcp_port',1500))
    elif action=='activate' and activate is not None:activate();result={'activated':True}
    elif action=='cancel-discovery':result=discovery.stop()
    elif action in ('connect','control') and discovery.snapshot()['running']:raise ValueError('Wait for discovery to finish or cancel it first.')
    elif action=='settings':
     with controller.operation:controller.save_settings(value)
     result=controller.snapshot()
    elif action=='connect':result=controller.connect(value)
    elif action=='disconnect':controller.disconnect();result=controller.snapshot()
    elif action=='control':result=controller.action(value)
    else:return self.reply(404,{'error':'Unknown operation.'})
    return self.reply(200,result)
   except (OSError,ValueError,RuntimeError,TypeError) as exc:return self.reply(400,{'error':str(exc)})
  def control_post(self):
   supplied=self.headers.get('X-KPA-Feed-Token','')
   if not self.host_ok() or self.headers.get('Origin') or not secrets.compare_digest(supplied,control_token):
    return self.reply(403,{'error':'Local backend control token required.'})
   try:
    length=int(self.headers.get('Content-Length','0'))
    if not 0<length<=1024:raise ValueError('Invalid control request size.')
    value=json.loads(self.rfile.read(length))
    if not isinstance(value,dict) or not isinstance(value.get('id'),str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,80}',value['id']):
     raise ValueError('A unique request ID is required.')
    power=urlparse(self.path).path=='/api/v1/power'
    if power:controller.shared_power()
    else:controller.shared_controls()
    if discovery.snapshot()['running']:raise ValueError('Finish discovery before changing amplifier controls.')
    key=value['id'];fingerprint=(urlparse(self.path).path,value)
    if key in control_requests:
     previous,result=control_requests[key]
     if previous!=fingerprint:raise ValueError('Request ID already used for different values.')
     return self.reply(200,result)
    # Keep spent IDs for this token's entire lifetime. When the bounded map
    # is full, reject new IDs instead of evicting a receipt and replaying it.
    # Duplicates above still return their original receipt at capacity.
    if len(control_requests)>=128:
     raise ValueError('Shared-control receipt capacity reached. Restart KPA1500 Control before sending a new shared request.')
    # Reserve before execution, including uncertain failures. Never retry.
    result={'queued':False,'error':'Receipt uncertain. Check the amplifier; no retry was sent.'}
    control_requests[key]=(fingerprint,result)
    action=controller.shared_power_action(value) if power else controller.shared_control_action(value)
    result=dict(queued=action.get('status')=='queued',action=action)
    control_requests[key]=(fingerprint,result)
    return self.reply(200,result)
   except PermissionError as exc:return self.reply(403,{'error':str(exc)})
   except (OSError,ValueError,RuntimeError,TypeError) as exc:return self.reply(400,{'error':str(exc)})
 Handler.discovery=discovery
 return Handler

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--http-port',type=int,default=51980);parser.add_argument('--no-browser',action='store_true');parser.add_argument('--demo',action='store_true');parser.add_argument('--settings',type=Path,default=data_directory()/'connection.json');args=parser.parse_args()
 controller=Controller(args.settings,offline_only=args.demo);token=secrets.token_urlsafe(24);server=ThreadingHTTPServer(('127.0.0.1',args.http_port),handler_for(controller,token));server.daemon_threads=True
 if args.demo:controller.connect({'mode':'simulator'})
 else:controller.startup()
 # SIGTERM closes USB worker too; Quit should not leave a reader behind.
 def shutdown(signum,frame):raise KeyboardInterrupt
 signal.signal(signal.SIGTERM,shutdown)
 print('KPA1500 Control:',f'http://127.0.0.1:{server.server_port}/{token}/',flush=True)
 try:server.serve_forever(poll_interval=.2)
 except KeyboardInterrupt:pass
 finally:
  server.RequestHandlerClass.discovery.stop()
  thread=server.RequestHandlerClass.discovery.thread
  if thread:thread.join(5)
  server.server_close();controller.disconnect()
if __name__=='__main__':multiprocessing.freeze_support();main()
