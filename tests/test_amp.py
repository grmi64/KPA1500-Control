import io,json,os,pathlib,queue,signal,subprocess,sys,tempfile,threading,time,unittest,urllib.error,urllib.request
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from protocol import parse,Protocol,Session
from simulator import SimulatorTransport
from engine import Controller
from server import handler_for
from http.server import ThreadingHTTPServer

class ProtocolTests(unittest.TestCase):
 def session(self):
  transport=SimulatorTransport();amp=Session(transport);amp.identify();amp.poll(True);return amp,transport
 def test_documented_units_and_distinct_readings(self):
  self.assertEqual(parse('^VI513 061;'),{'voltage_v':51.3,'current_a':61})
  self.assertEqual(parse('^PWI24;'),{'input_watts':24})
  self.assertEqual(parse('^PWR4;'),{'reflected_watts':4})
  self.assertEqual(parse('^SW014;'),{'swr':1.4})
  self.assertEqual(parse('^SB024;'),{'bypass_swr':2.4})
  self.assertEqual(parse('^FL40;')['fault_code'],'40')
  self.assertEqual(parse('^AN32;'),{'antenna':32})
  self.assertEqual(parse('^BN05;'),{'band':'20m'})
 def test_invalid_and_out_of_range_frames(self):
  for raw in ['^AN00;','^BN99;','^PWFnan;','^PWI-1;','^OS2;','^TM999;','^SW99999;','garbage','^FC6;']:
   with self.assertRaises(ValueError,msg=raw):parse(raw)
 def test_tx_unknown_is_not_rx(self):
  self.assertIsNone(parse('^VG unknown;')['transmitting'])
  self.assertTrue(parse('^VG TR_STATE_RX 3T:0 KeyIn:1;')['transmitting'])
  self.assertFalse(parse('^VG TR_STATE_RX 3T:0 KeyIn:0;')['transmitting'])
 def test_hardware_standby_idle_and_transmit_guards(self):
  frame='^VG TR inhibit x01 TR_STATE_PA_BYPASSED_3R_ON 3R:1 3T:0 Bias:0 PA STBY KeyIn:0  MODE_STBY;'
  self.assertFalse(parse(frame)['transmitting'])
  self.assertTrue(parse(frame.replace('KeyIn:0','KeyIn:1'))['transmitting'])
  self.assertTrue(parse(frame.replace('3T:0','3T:1'))['transmitting'])
  self.assertIsNone(parse(frame.replace('Bias:0','Bias:1'))['transmitting'])
  self.assertIsNone(parse(frame.replace('KeyIn:0',''))['transmitting'])
  self.assertTrue(parse('^VG TR_STATE_RX TR_STATE_TX 3T:0 KeyIn:0;')['transmitting'])
 def test_no_operating_writes_on_connect_or_poll(self):
  amp,transport=self.session()
  self.assertTrue(all(command in ['^I;','^SN;','^RVM;','^ON;']+['^'+tag+';' for tag in __import__('protocol').FAST+__import__('protocol').SLOW] for command in transport.writes))
  self.assertEqual(amp.snapshot()['status'],'live')
 def test_controls_verified(self):
  amp,transport=self.session()
  for action,key,value in [('operate','operate',True),('standby','operate',False),('antenna_2','antenna',2),('antenna_next','antenna',1),('atu_bypass','atu_enabled',False),('atu_in','atu_enabled',True),('tune','tuning',True),('cancel_tune','tuning',False)]:
   self.assertEqual(amp.action(action)['status'],'confirmed',action);self.assertEqual(amp.values[key],value)
 def test_tx_blocks_writes_at_worker_even_with_previous_rx(self):
  amp,transport=self.session();transport.tx=True;start=len(transport.writes)
  for action in ('operate','standby','antenna_1','atu_bypass','tune','clear_fault'):
   with self.assertRaisesRegex(ValueError,'transmitting'):amp.action(action)
  self.assertFalse(any(x in ('^OS1;','^OS0;','^AN1;','^AMB;','^FT;','^FLC;') for x in transport.writes[start:]))
 def test_unknown_rx_blocks_and_fault_does_not_auto_clear(self):
  amp,transport=self.session();transport.fault='20'
  with self.assertRaisesRegex(ValueError,'fault'):amp.action('operate')
  self.assertNotIn('^OS1;',transport.writes)
  self.assertEqual(amp.action('clear_fault')['status'],'confirmed')
  transport.fault='40';self.assertEqual(amp.action('clear_fault')['status'],'unconfirmed')
  transport.write(b'^VG;') # remove test response before patch
  transport.read(0)
  original=amp.read
  def unknown(tag):
   values=original(tag)
   if tag=='VG':amp.values['transmitting']=None
   return values
  with patch.object(amp,'read',side_effect=unknown):
   with self.assertRaises(ValueError):amp.action('antenna_1')
 def test_stale_clears_measurements(self):
  amp,_=self.session();amp.last_live=time.time()-4
  self.assertIsNone(amp.snapshot()['forward_watts']);self.assertEqual(amp.snapshot()['status'],'stale')
 def test_split_and_unsolicited_frames(self):
  class Split:
   def write(self,data):self.parts=iter([b'^OTHER0;^PW',b'F12;'])
   def read(self,timeout):return next(self.parts,b'')
  self.assertEqual(Protocol(Split()).query('PWF'),'^PWF12;')
 def test_bad_identity_never_enables_controls(self):
  class Wrong(SimulatorTransport):
   def write(self,data):
    if data==b'^I;':self.buffer+=b'^OTHER;'
    else:super().write(data)
  with self.assertRaises(ValueError):Session(Wrong()).identify()

class ControllerTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.controller=Controller(pathlib.Path(self.temp.name)/'connection.json')
 def tearDown(self):self.controller.disconnect();self.temp.cleanup()
 def live(self):
  self.controller.connect({'mode':'simulator'})
  for _ in range(80):
   state=self.controller.snapshot()
   if state['state']['status']=='live':return state
   time.sleep(.05)
  self.fail('Simulator did not become live')
 def test_starts_disconnected_and_usb_never_auto_opens(self):
  self.assertIsNone(self.controller.worker);self.assertEqual(self.controller.snapshot()['state']['status'],'disconnected')
  with self.assertRaises(ValueError):self.controller.connect({'mode':'tcp'})
  with self.assertRaises(ValueError):self.controller.connect({'mode':'usb','port':'/dev/cu.bad/../../radio'})
 def test_expired_generation_cannot_send_after_reconnect(self):
  first=self.live();second=self.live();self.assertNotEqual(first['generation'],second['generation'])
  with self.assertRaisesRegex(ValueError,'Connection changed'):self.controller.action({'action':'operate','generation':first['generation']})
 def test_shared_state_actions_and_worker_shutdown(self):
  snap=self.live();pid=self.controller.worker.pid
  queued=self.controller.action({'action':'operate','generation':snap['generation']})
  for _ in range(60):
   current=self.controller.snapshot()
   if current['actions'] and current['actions'][0]['status']!='queued':break
   time.sleep(.05)
  self.assertEqual(current['actions'][0]['status'],'confirmed');self.assertTrue(current['state']['operate']);self.assertEqual(pid,self.controller.worker.pid)
  self.controller.disconnect();self.assertEqual(self.controller.snapshot()['state']['status'],'disconnected')
 def test_cached_snapshot_fast_when_worker_is_slow(self):
  self.live();start=time.monotonic()
  for _ in range(50):self.controller.snapshot()
  self.assertLess(time.monotonic()-start,.1)
 def test_http_token_host_origin_and_assets(self):
  token='unit-test-token';server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(self.controller,token));threading.Thread(target=server.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(server.server_port)
  try:
   self.assertEqual(json.load(urllib.request.urlopen(base+'/'+token+'/state'))['model'],'KPA1500')
   with self.assertRaises(urllib.error.HTTPError) as denied:urllib.request.urlopen(base+'/api/v1/telemetry')
   self.assertEqual(denied.exception.code,403)
   self.controller.save_settings({'share_readings':True})
   feed=json.load(urllib.request.urlopen(base+'/api/v1/telemetry'))
   self.assertEqual(feed['model'],'KPA1500');self.assertNotIn('connection',feed);self.assertNotIn('actions',feed)
   self.assertIsNone(self.controller.worker)
   saved=Controller(self.controller.settings);self.assertTrue(saved.config['share_readings'])
   with self.assertRaises(ValueError):saved.save_settings({'share_readings':'yes'})
   self.controller.save_settings({'share_readings':False})
   with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(base+'/api/v1/telemetry')
   for asset in ['','app.js','app.css']:
    with urllib.request.urlopen(base+'/'+token+'/'+asset) as response:self.assertEqual(response.status,200)
   for headers in [{},{'X-Amp-Token':token,'Origin':'https://foreign.test'},{'X-Amp-Token':token,'Host':'evil.test'}]:
    request=urllib.request.Request(base+'/'+token+'/connect',data=b'{"mode":"simulator"}',headers=headers)
    with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(request)
    self.assertEqual(error.exception.code,403)
   self.assertIsNone(self.controller.worker)
  finally:server.shutdown();server.server_close()

if __name__=='__main__':unittest.main()

class PortProtectionTests(unittest.TestCase):
 def test_cooperative_lock_excludes_second_controller(self):
  from port_lock import PortLock
  with tempfile.TemporaryDirectory() as directory,patch('port_lock.Path.home',return_value=pathlib.Path(directory)):
   a=PortLock(('COM234' if sys.platform=='win32' else '/dev/cu.unit-test'));b=PortLock(('COM234' if sys.platform=='win32' else '/dev/cu.unit-test'))
   with patch.object(a,'check_owners'),patch.object(b,'check_owners'):
    a.acquire()
    try:
     with self.assertRaises(OSError):b.acquire()
    finally:a.release()
    b.acquire();b.release()
 @unittest.skipIf(sys.platform=="win32","POSIX pseudo-terminal only; Windows fake-serial and endpoint exclusion tests cover the adapter.")
 def test_kernel_exclusivity_on_test_terminal(self):
  import pty,termios
  from port_lock import exclusive
  master,slave=pty.openpty();name=os.ttyname(slave)
  try:
   exclusive(slave)
   try:extra=os.open(name,os.O_RDWR|os.O_NOCTTY)
   except OSError:pass
   else:
    os.close(extra);self.skipTest('macOS pseudo-terminal does not enforce USB serial exclusivity; verify on hardware.')
  finally:os.close(slave);os.close(master)

class DisconnectGuardTests(unittest.TestCase):
 def test_disconnect_requested_before_set_blocks_control(self):
  transport=SimulatorTransport();amp=Session(transport,cancelled=lambda:True);amp.identify()
  with self.assertRaisesRegex(ValueError,'closing'):amp.action('operate')
  self.assertNotIn('^OS1;',transport.writes)

class ShutdownTests(unittest.TestCase):
 @unittest.skipIf(sys.platform=="win32","Windows TerminateProcess is not SIGTERM; native host graceful-close test is separate.")
 def test_service_sigterm_exits_with_connected_reader_and_queued_state(self):
  with tempfile.TemporaryDirectory() as directory:
   for _ in range(3):
    process=subprocess.Popen([sys.executable,str(pathlib.Path(__file__).resolve().parents[1]/'Sources/server.py'),'--demo','--no-browser','--http-port','0','--settings',str(pathlib.Path(directory)/'settings.json')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
     line=process.stdout.readline();self.assertIn('http://127.0.0.1:',line)
     url=line.split('http://',1)[1].strip();url='http://'+url+'state'
     for _ in range(40):
      if json.load(urllib.request.urlopen(url))['state']['status']=='live':break
      time.sleep(.05)
     # Stop polling so shutdown also covers undrained state messages.
     time.sleep(.5);started=time.monotonic();process.terminate();process.wait(timeout=5)
     self.assertEqual(process.returncode,0);self.assertLess(time.monotonic()-started,4)
    finally:
     if process.poll() is None:process.kill();process.wait()
     process.stdout.close();process.stderr.close()

class StartupTests(unittest.TestCase):
 def test_default_off_and_saved_usb_startup_once(self):
  with tempfile.TemporaryDirectory() as directory:
   path=pathlib.Path(directory)/'settings.json';controller=Controller(path)
   with patch.object(controller,'connect') as connect:
    controller.startup();connect.assert_not_called()
   controller.save_settings({'auto_connect':True,'port':('COM234' if sys.platform=='win32' else '/dev/cu.unit-test'),'baud':230400})
   self.assertIsNone(controller.worker)
   restored=Controller(path)
   with patch.object(restored,'connect',side_effect=OSError('Port unavailable')) as connect:
    restored.startup();connect.assert_called_once();self.assertEqual(connect.call_args.args[0]['mode'],'usb');self.assertEqual(restored.state['status'],'error')
   restored.save_settings({'auto_connect':False,'port':('COM234' if sys.platform=='win32' else '/dev/cu.unit-test'),'baud':230400})
   self.assertFalse(Controller(path).config['auto_connect'])
 def test_startup_setting_rejects_missing_port_and_invalid_values(self):
  with tempfile.TemporaryDirectory() as directory:
   controller=Controller(pathlib.Path(directory)/'settings.json')
   for value in ({'auto_connect':True,'port':''},{'auto_connect':'true','port':('COM235' if sys.platform=='win32' else '/dev/cu.test')},{'auto_connect':True,'port':'/dev/cu.x/../radio'},{'auto_connect':True,'port':('COM235' if sys.platform=='win32' else '/dev/cu.test'),'baud':1}):
    with self.assertRaises(ValueError):controller.save_settings(value)
   self.assertIsNone(controller.worker)
