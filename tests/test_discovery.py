import pathlib,sys,threading,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from discovery import Discovery,identify,local_targets
class Wire:
 def __init__(self,reply=b'^KPA1500;'):self.reply=reply;self.writes=[];self.closed=False
 def write(self,data):self.writes.append(data)
 def read(self,timeout):reply=self.reply;self.reply=b'';return reply
 def close(self):self.closed=True
class Tests(unittest.TestCase):
 def test_identity_only_and_close(self):
  for mode in ('usb','tcp'):
   wire=Wire();c=dict(mode=mode,port='/dev/cu.test',baud=230400,host='192.168.1.2',tcp_port=1500)
   self.assertEqual(identify(c,threading.Event(),lambda *a:wire,lambda *a:wire),c);self.assertEqual(wire.writes,[b'^I;']);self.assertTrue(wire.closed)
 def test_wrong_device(self):
  wire=Wire(b'^IOTHER;');self.assertIsNone(identify(dict(mode='usb',port='x',baud=230400),threading.Event(),lambda *a:wire));self.assertTrue(wire.closed)
 def test_cancel_no_open(self):
  stop=threading.Event();stop.set()
  self.assertIsNone(identify({},stop,lambda *a:self.fail('opened port')))
 def test_busy_port(self):
  def busy(*a):raise OSError('in use')
  self.assertIsNone(identify(dict(mode='usb',port='x',baud=230400),threading.Event(),busy))
 def test_validation(self):
  for baud,port in [(1,1500),(230400,0),(True,1500),(230400,True)]:
   with self.assertRaises(ValueError):Discovery().start([],baud,port)
 def test_local_scope(self):
  class Result:
   def __init__(self,stdout):self.stdout=stdout
  with patch('discovery.subprocess.run',side_effect=[Result(' interface: en0\n'),Result('192.168.1.10'),Result('255.255.0.0')]):
   targets=local_targets();self.assertEqual(len(targets),253);self.assertNotIn('192.168.1.10',targets);self.assertTrue(all(h.startswith('192.168.1.') for h in targets))
 def test_no_automatic_connect(self):
  with patch('discovery.local_targets',return_value=['192.168.1.2']),patch('discovery.identify',side_effect=lambda c,stop:c):
   d=Discovery();d.start([],230400,1500);d.thread.join(2);state=d.snapshot();self.assertFalse(state['running']);self.assertEqual(len(state['results']),1)

 def test_delayed_identity_retries_read_only(self):
  class Delayed(Wire):
   def read(self,timeout):
    if len(self.writes)<2:return b''
    return super().read(timeout)
  wire=Delayed();candidate=dict(mode='usb',port='x',baud=230400)
  self.assertEqual(identify(candidate,threading.Event(),lambda *a:wire),candidate)
  self.assertEqual(wire.writes,[b'^I;',b'^I;']);self.assertTrue(wire.closed)
 def test_probe_exception_preserves_other_results(self):
  def probe(candidate,stop):
   if candidate['host'].endswith('.1'):raise RuntimeError('probe failure')
   return candidate
  with patch('discovery.local_targets',return_value=['192.168.1.1','192.168.1.2']),patch('discovery.identify',side_effect=probe):
   d=Discovery();d.start([],230400,1500);d.thread.join(3);state=d.snapshot()
   self.assertFalse(state['running']);self.assertEqual(len(state['results']),1);self.assertIn('Some connections could not be checked',state['message'])

if __name__=='__main__':unittest.main()

class ServiceTests(unittest.TestCase):
 def test_discovery_routes_and_connect_guard(self):
  import json,tempfile,urllib.request,urllib.error
  from http.server import ThreadingHTTPServer
  from server import handler_for
  from engine import Controller
  with tempfile.TemporaryDirectory() as folder:
   controller=Controller(pathlib.Path(folder)/'settings.json');handler=handler_for(controller,'discovery-test')
   server=ThreadingHTTPServer(('127.0.0.1',0),handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   base='http://127.0.0.1:'+str(server.server_port)+'/discovery-test/'
   def post(name,data):
    request=urllib.request.Request(base+name,json.dumps(data).encode(),headers={'Content-Type':'application/json','X-Amp-Token':'discovery-test'})
    return json.load(urllib.request.urlopen(request,timeout=2))
   try:
    with patch.object(handler.discovery,'start',return_value={'running':True}) as start,patch('server.ports',return_value=[]):
     self.assertTrue(post('discover',{'baud':230400,'tcp_port':1500})['running']);start.assert_called_once_with([],230400,1500)
    handler.discovery.running=True
    with patch.object(controller,'connect') as connect:
     with self.assertRaises(urllib.error.HTTPError) as error:post('connect',{'mode':'simulator'})
     self.assertEqual(error.exception.code,400);connect.assert_not_called()
    post('cancel-discovery',{});self.assertTrue(handler.discovery.cancel.is_set())
    handler.discovery.running=False;controller.connect({'mode':'simulator'})
    with patch.object(handler.discovery,'start') as start:
     with self.assertRaises(urllib.error.HTTPError):post('discover',{'baud':230400,'tcp_port':1500})
     start.assert_not_called()
    self.assertFalse((pathlib.Path(folder)/'settings.json').exists(),'Discovery must not save settings')
   finally:server.shutdown();server.server_close();thread.join();controller.disconnect()
