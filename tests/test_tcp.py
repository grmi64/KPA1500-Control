import contextlib,json,pathlib,socket,sys,tempfile,threading,time,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from transport import TCPTransport,tcp_endpoint
from protocol import Session,Protocol
from simulator import SimulatorTransport
from engine import Controller

class FakeAmp:
 def __enter__(self):
  self.listener=socket.socket();self.listener.bind(('127.0.0.1',0));self.listener.listen();self.listener.settimeout(.05);self.port=self.listener.getsockname()[1];self.stop=threading.Event();self.writes=[];self.clients=[];self.silent=False
  self.thread=threading.Thread(target=self.serve,daemon=True);self.thread.start();return self
 def serve(self):
  while not self.stop.is_set():
   try:client,_=self.listener.accept()
   except socket.timeout:continue
   except OSError:return
   self.clients.append(client);sim=SimulatorTransport();buf=b'';client.settimeout(.05)
   try:
    while not self.stop.is_set():
     try:data=client.recv(4096)
     except socket.timeout:continue
     if not data:break
     buf+=data
     while b';' in buf:
      cmd,_,buf=buf.partition(b';');cmd+=b';';self.writes.append(cmd.decode());sim.write(cmd);reply=sim.read(.01)
      if reply and not self.silent:
       client.sendall(reply[:2]);time.sleep(.001);client.sendall(reply[2:])
   except OSError:pass
   finally:client.close()
 def __exit__(self,*args):
  self.stop.set();self.listener.close()
  for c in self.clients:
   with contextlib.suppress(OSError):c.shutdown(socket.SHUT_RDWR)
  self.thread.join(2)

class TCPTests(unittest.TestCase):
 def test_endpoint_validation(self):
  self.assertEqual(tcp_endpoint(' 192.168.0.18 ',1500),('192.168.0.18',1500))
  self.assertEqual(tcp_endpoint('::1',1500),('::1',1500))
  for host,port in [('http://localhost',1500),('',1500),('192.168.0.999',1500),('127.0.0.1',True),('127.0.0.1',0),('127.0.0.1',65536)]:
   with self.assertRaises(ValueError):tcp_endpoint(host,port)
 def test_fragmented_replies_guarded_controls_and_eof(self):
  with FakeAmp() as fake:
   transport=TCPTransport('127.0.0.1',fake.port)
   try:
    amp=Session(transport);amp.identify();amp.poll(True);self.assertEqual(amp.snapshot()['status'],'live')
    self.assertFalse(any(c in fake.writes for c in ['^OS1;','^FT;','^ON0;','^ON1;']))
    self.assertEqual(amp.action('operate')['status'],'confirmed')
    fake.clients[0].shutdown(socket.SHUT_RDWR)
    with self.assertRaises(OSError):transport.read(.2)
   finally:transport.close();transport.close()
 def test_duplicate_endpoint_lock_and_clean_reconnect(self):
  with FakeAmp() as fake:
   a=TCPTransport('127.0.0.1',fake.port)
   try:
    with self.assertRaisesRegex(OSError,'already in use'):TCPTransport('127.0.0.1',fake.port)
   finally:a.close()
   b=TCPTransport('127.0.0.1',fake.port)
   try:self.assertEqual(Protocol(b).query('I'),'^KPA1500;')
   finally:b.close()
 def test_failed_connect_releases_endpoint_lock(self):
  with FakeAmp() as fake:
   with patch('socket.create_connection',side_effect=TimeoutError('test timeout')):
    with self.assertRaises(TimeoutError):TCPTransport('127.0.0.1',fake.port)
   a=TCPTransport('127.0.0.1',fake.port);a.close()
 def test_tcp_and_usb_settings_survive_restart(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'settings.json';c=Controller(p)
   c.save_settings(dict(mode='tcp',host='192.168.0.18',tcp_port=1500,auto_connect=True,port=('COM235' if sys.platform=='win32' else '/dev/cu.test'),baud=115200))
   restored=Controller(p)
   with patch.object(restored,'connect') as connect:
    restored.startup();connect.assert_called_once();self.assertEqual(connect.call_args.args[0]['mode'],'tcp')
   restored.save_settings({'share_readings':True});self.assertEqual(json.loads(p.read_text())['mode'],'tcp')
   restored.save_settings({'mode':'usb'});again=Controller(p);self.assertEqual(again.config['mode'],'usb');self.assertEqual(again.config['host'],'192.168.0.18');self.assertEqual(again.config['baud'],115200)
   before=p.read_text()
   for value in [dict(mode='tcp',host='bad'),dict(mode='tcp',tcp_port=0),dict(mode='simulator')]:
    with self.assertRaises(ValueError):again.save_settings(value)
    self.assertEqual(p.read_text(),before)
 def test_controller_tcp_live_disconnect_and_reconnect(self):
  with tempfile.TemporaryDirectory() as d,FakeAmp() as fake:
   c=Controller(pathlib.Path(d)/'settings.json')
   try:
    for _ in range(2):
     c.connect(dict(mode='tcp',host='127.0.0.1',tcp_port=fake.port))
     end=time.monotonic()+5
     while time.monotonic()<end and c.snapshot()['state']['status']!='live':time.sleep(.05)
     self.assertEqual(c.snapshot()['state']['status'],'live');c.disconnect();self.assertIsNone(c.worker)
    self.assertFalse(any(x in fake.writes for x in ['^OS1;','^FT;','^ON1;']))
   finally:c.disconnect()

 def test_nonresponding_tcp_query_is_bounded(self):
  with FakeAmp() as fake:
   fake.silent=True;t=TCPTransport('127.0.0.1',fake.port)
   try:
    start=time.monotonic()
    with self.assertRaises(TimeoutError):Protocol(t).query('I',timeout=.1)
    self.assertLess(time.monotonic()-start,.5)
    self.assertEqual(fake.writes,['^I;'])
   finally:t.close()
 def test_invalid_tcp_request_preserves_existing_connection(self):
  with tempfile.TemporaryDirectory() as d:
   c=Controller(pathlib.Path(d)/'settings.json')
   with patch.object(c,'_disconnect') as disconnect:
    with self.assertRaises(ValueError):c.connect(dict(mode='tcp',host='bad',tcp_port=1500))
    disconnect.assert_not_called();self.assertFalse(c.settings.exists())
