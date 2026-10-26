"""Local, token-protected UI service. No radio/CAT sockets; opt-in USB startup."""
import argparse,json,multiprocessing,secrets,signal,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from engine import Controller,ports
ROOT=Path(__file__).parent

def handler_for(controller,token):
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
   if path=='/api/v1/telemetry':
    try:return self.reply(200,controller.telemetry())
    except PermissionError as exc:return self.reply(403,{'error':str(exc)})
   if not path.startswith(prefix):return self.reply(404,{'error':'Not found.'})
   name=path[len(prefix):]
   if name=='state':return self.reply(200,controller.snapshot())
   if name=='ports':return self.reply(200,{'ports':ports()})
   assets={'':('index.html','text/html; charset=utf-8'),'measurements.js':('measurements.js','text/javascript; charset=utf-8'),'app.js':('app.js','text/javascript; charset=utf-8'),'app.css':('app.css','text/css; charset=utf-8'),'kpa_meter_colors.js':('kpa_meter_colors.js','text/javascript; charset=utf-8')}
   if name not in assets:return self.reply(404,{'error':'Not found.'})
   filename,mime=assets[name];return self.reply(200,(ROOT/filename).read_bytes(),mime)
  def do_POST(self):
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
    if action=='settings':
     with controller.operation:controller.save_settings(value)
     result=controller.snapshot()
    elif action=='connect':result=controller.connect(value)
    elif action=='disconnect':controller.disconnect();result=controller.snapshot()
    elif action=='control':result=controller.action(value)
    else:return self.reply(404,{'error':'Unknown operation.'})
    return self.reply(200,result)
   except (OSError,ValueError,RuntimeError,TypeError) as exc:return self.reply(400,{'error':str(exc)})
 return Handler

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--http-port',type=int,default=51980);parser.add_argument('--no-browser',action='store_true');parser.add_argument('--demo',action='store_true');parser.add_argument('--settings',type=Path,default=Path.home()/'Library/Application Support/com.grmi64.KPA1500Control/connection.json');args=parser.parse_args()
 controller=Controller(args.settings);token=secrets.token_urlsafe(24);server=ThreadingHTTPServer(('127.0.0.1',args.http_port),handler_for(controller,token));server.daemon_threads=True
 if args.demo:controller.connect({'mode':'simulator'})
 else:controller.startup()
 # SIGTERM closes USB worker too; Quit should not leave a reader behind.
 def shutdown(signum,frame):raise KeyboardInterrupt
 signal.signal(signal.SIGTERM,shutdown)
 print('KPA1500 Control:',f'http://127.0.0.1:{server.server_port}/{token}/',flush=True)
 try:server.serve_forever(poll_interval=.2)
 except KeyboardInterrupt:pass
 finally:server.server_close();controller.disconnect()
if __name__=='__main__':multiprocessing.freeze_support();main()
