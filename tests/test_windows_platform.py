import json,os,pathlib,subprocess,sys,tempfile,threading,types,unittest,urllib.request,urllib.error,uuid
from unittest.mock import patch,Mock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
import platform_paths,endpoint_lock,transport
from engine import Controller
from server import handler_for
from http.server import ThreadingHTTPServer

class PlatformTests(unittest.TestCase):
 def test_windows_imports_do_not_load_posix_modules(self):
  if sys.platform!='win32':self.skipTest('Windows import boundary')
  code="import sys; sys.path.insert(0,'Sources'); import server; assert not any(x in sys.modules for x in ('termios','fcntl'))"
  subprocess.run([sys.executable,'-B','-c',code],cwd=pathlib.Path(__file__).resolve().parents[1],check=True)
 def test_com_names_and_rejected_paths(self):
  with patch('platform_paths.WINDOWS',True):
   self.assertEqual(platform_paths.serial_port('com10'),'COM10')
   for value in ('COM0','COM01','COM1/../../radio','COM1:','COM1;','/dev/cu.test',None):
    with self.assertRaises(ValueError):platform_paths.serial_port(value)
 def test_passive_enumeration_never_opens_ports(self):
  listing=Mock();listing.comports.return_value=[types.SimpleNamespace(device=p) for p in ['COM10','com2','COM2','invalid']]
  with patch('platform_paths.WINDOWS',True),patch.dict(sys.modules,{'serial':types.ModuleType('serial'),'serial.tools':types.SimpleNamespace(list_ports=listing)}):
   self.assertEqual(platform_paths.ports(),['COM2','COM10'])
  listing.comports.assert_called_once_with()
 def test_app_specific_settings_directory(self):
  with patch('platform_paths.WINDOWS',True),patch.dict(os.environ,{'LOCALAPPDATA':str(pathlib.Path('isolated').absolute())}):
   self.assertEqual(platform_paths.data_directory().name,'KPA1500 Control')
   self.assertNotIn('OM Power',str(platform_paths.data_directory()))

class FakeSerial:
 def __init__(self,**kwargs):self.options=kwargs;self.in_waiting=0;self.closed=False;self.writes=[];self.reset=False
 def reset_input_buffer(self):self.reset=True
 def read(self,count):return b''
 def write(self,data):self.writes.append(data);return len(data)
 def close(self):self.closed=True

@unittest.skipUnless(sys.platform=='win32','Windows serial adapter and OS byte-range lease')
class SerialTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.key='offline-platform:'+uuid.uuid4().hex
  self.p=patch('endpoint_lock.lock_directory',return_value=pathlib.Path(self.temp.name));self.p.start()
  # Fake-serial tests must not contend with an actual user's COM lease.
  self.native=patch('port_lock.EndpointLock',side_effect=lambda key:endpoint_lock.EndpointLock(self.key+':'+key));self.native.start()
 def tearDown(self):self.native.stop();self.p.stop();self.temp.cleanup()
 def test_com10_exclusion_bounded_io_and_reconnect(self):
  t=transport.WindowsSerialTransport('com10',230400,FakeSerial);wire=t.serial
  try:
   self.assertEqual(wire.options,dict(port='COM10',baudrate=230400,timeout=.05,write_timeout=.5))
   self.assertTrue(wire.reset);self.assertEqual(wire.writes,[])
   with self.assertRaisesRegex(OSError,'already in use'):transport.WindowsSerialTransport('COM10',230400,FakeSerial)
   t.write(b'^I;');self.assertEqual(wire.writes,[b'^I;']);self.assertEqual(t.read(.1),b'');self.assertEqual(wire.timeout,.1)
  finally:t.close();t.close()
  self.assertTrue(wire.closed);transport.WindowsSerialTransport('COM10',230400,FakeSerial).close()
 def test_failed_driver_open_releases_lease(self):
  factory=Mock(side_effect=OSError('Driver busy'))
  with self.assertRaisesRegex(OSError,'Driver busy'):transport.WindowsSerialTransport('COM10',230400,factory)
  transport.WindowsSerialTransport('COM10',230400,FakeSerial).close()
 def test_short_write_never_replays(self):
  t=transport.WindowsSerialTransport('COM11',230400,FakeSerial)
  try:
   with patch.object(t.serial,'write',return_value=1) as send:
    with self.assertRaises(TimeoutError):t.write(b'^OS1;')
    send.assert_called_once_with(b'^OS1;')
  finally:t.close()
 def test_lease_excludes_another_process(self):
  lease=endpoint_lock.EndpointLock(self.key);lease.acquire()
  code="import sys;sys.path.insert(0,'Sources');from pathlib import Path;import endpoint_lock;endpoint_lock.lock_directory=lambda:Path(sys.argv[1]);endpoint_lock.EndpointLock(sys.argv[2]).acquire()"
  try:
   child=subprocess.run([sys.executable,'-B','-c',code,self.temp.name,self.key],cwd=pathlib.Path(__file__).resolve().parents[1],capture_output=True,text=True)
   self.assertNotEqual(child.returncode,0);self.assertIn('already in use',child.stderr)
  finally:lease.release()

class OfflineTests(unittest.TestCase):
 def test_saved_auto_connect_and_sharing_cannot_escape_demo(self):
  with tempfile.TemporaryDirectory() as folder:
   path=pathlib.Path(folder)/'demo.json';original=json.dumps({'mode':'tcp','host':'192.0.2.10','auto_connect':True,'share_readings':True});path.write_text(original)
   c=Controller(path,offline_only=True)
   self.assertFalse(c.config['auto_connect']);self.assertFalse(c.config['share_readings'])
   with patch.object(c,'connect') as connect:c.startup();connect.assert_not_called()
   for config in ({'mode':'tcp','host':'192.0.2.10'},{'mode':'usb','port':'COM10'}):
    with self.assertRaisesRegex(ValueError,'offline simulation'):c.connect(config)
   for config in ({'auto_connect':True},{'share_readings':True}):
    with self.assertRaises(ValueError):c.save_settings(config)
   self.assertEqual(path.read_text(),original);self.assertIsNone(c.worker)
 def test_http_demo_rejects_hardware_and_discovery_before_any_io(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Controller(pathlib.Path(folder)/'demo.json',offline_only=True);h=handler_for(c,'offline-test');s=ThreadingHTTPServer(('127.0.0.1',0),h)
   thread=threading.Thread(target=s.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(s.server_port)+'/offline-test/'
   def post(action,data):return urllib.request.urlopen(urllib.request.Request(base+action,json.dumps(data).encode(),headers={'X-Amp-Token':'offline-test'}),timeout=2)
   try:
    with patch('server.ports',side_effect=AssertionError('enumerated')),patch.object(h.discovery,'start',side_effect=AssertionError('discovered')):
     self.assertEqual(json.load(urllib.request.urlopen(base+'ports'))['ports'],[])
     for action,data in [('discover',{}),('connect',{'mode':'tcp','host':'192.0.2.10'})]:
      with self.assertRaises(urllib.error.HTTPError) as error:post(action,data)
      self.assertEqual(error.exception.code,400)
    self.assertIsNone(c.worker);self.assertFalse(c.settings.exists())
   finally:s.shutdown();s.server_close();thread.join();c.disconnect()
 def test_windows_discovery_never_probes_passive_usb_ports(self):
  import discovery
  with patch('discovery.WINDOWS',True),patch('discovery.local_targets',return_value=[]),patch('discovery.identify',side_effect=AssertionError('USB probe')) as probe:
   d=discovery.Discovery();d.start(['COM10'],230400,1500);d.thread.join(2)
   probe.assert_not_called();self.assertFalse(d.snapshot()['running']);self.assertIn('passively',d.snapshot()['message'])

class NativeBoundaryTests(unittest.TestCase):
 def test_bridge_does_not_expose_native_objects_to_javascript(self):
  from windows_app import DisplayBridge
  self.assertTrue(all(key.startswith('_') for key in vars(DisplayBridge())))
 def test_window_recovery_handles_missing_monitor_and_small_workarea(self):
  from windows_app import fit_bounds
  self.assertEqual(fit_bounds((3000,-100,1020,850),(0,0,800,600)),(0,0,800,600))
  self.assertEqual(fit_bounds((-900,20,410,540),(-1920,0,1920,1040)),(-900,20,410,540))
