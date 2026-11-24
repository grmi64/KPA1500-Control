import json,pathlib,sys,tempfile,threading,time,unittest
from unittest.mock import patch,Mock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from windows_network import targets_from_records
from windows_preferences import Preferences,validate
from windows_instance import Instance
from engine import Controller
from server import handler_for
from discovery import Discovery
from http.server import ThreadingHTTPServer

class NetworkProviderTests(unittest.TestCase):
 def record(self,**kw):return dict(address='192.0.2.10',prefix=24,gateway='192.0.2.1',metric=10,**kw)
 def test_default_interface_and_24_cap(self):
  a=dict(address='10.3.4.10',prefix=16,gateway='10.3.0.1',metric=5)
  b=self.record();result=targets_from_records([b,a])
  self.assertEqual(len(result),253);self.assertNotIn('10.3.4.10',result);self.assertTrue(all(x.startswith('10.3.4.') for x in result))
 def test_narrow_network_never_expands_to_other_subnet(self):
  result=targets_from_records([dict(address='192.0.2.10',prefix=29,gateway='192.0.2.9',metric=1)])
  self.assertEqual(result,['192.0.2.9','192.0.2.11','192.0.2.12','192.0.2.13','192.0.2.14'])
 def test_invalid_routes_fail_closed(self):
  for changes in ({'prefix':0},{'prefix':32},{'gateway':'198.51.100.1'},{'gateway':'192.0.2.10'},{'address':'127.0.0.1'},{'metric':True},{'address':'not an IP'}):
   record=self.record();record.update(changes)
   with self.assertRaises(ValueError):targets_from_records([record])
 def test_fixed_configuration_command_is_bounded_and_hidden(self):
  import windows_network
  with patch('windows_network.subprocess.run',return_value=Mock(stdout=json.dumps([self.record()]))) as run:
   self.assertEqual(len(windows_network.local_targets()),253)
   argv=run.call_args.args[0];self.assertIn('Get-NetRoute',argv[-1]);self.assertIn('Get-NetIPAddress',argv[-1]);self.assertEqual(run.call_args.kwargs['timeout'],15);self.assertEqual(run.call_args.kwargs['stdin'],__import__('subprocess').DEVNULL)


 def test_slow_configuration_process_exceeds_old_limit_but_finishes_once(self):
  import subprocess,windows_network
  real_run=subprocess.run;reply='import time;time.sleep(6);print('+repr(json.dumps([self.record()]))+')'
  def delayed(old_limit):
   def launch(argv,**kw):
    if old_limit:kw['timeout']=5
    return real_run([sys.executable,'-c',reply],**kw)
   return launch
  with patch('windows_network.subprocess.run',side_effect=delayed(True)) as old:
   with self.assertRaises(subprocess.TimeoutExpired):windows_network.local_targets()
   old.assert_called_once()
  with patch('windows_network.subprocess.run',side_effect=delayed(False)) as current:
   self.assertEqual(len(windows_network.local_targets()),253);current.assert_called_once()

 @unittest.skipUnless(sys.platform=='win32','Windows GUI standard-handle regression.')
 def test_gui_invalid_stdin_fails_without_explicit_handle_and_provider_succeeds(self):
  # Run in an isolated process: never alter the test runner's standard handles.
  # A fixed synthetic reply replaces PowerShell; no network config/probes needed.
  import subprocess
  code="""
import ctypes,json,subprocess,sys
from unittest.mock import patch
sys.path.insert(0,'Sources')
import windows_network
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.GetStdHandle.argtypes=[ctypes.c_ulong];kernel.GetStdHandle.restype=ctypes.c_void_p
kernel.SetStdHandle.argtypes=[ctypes.c_ulong,ctypes.c_void_p];kernel.SetStdHandle.restype=ctypes.c_int
key=(-10)&0xffffffff;original=kernel.GetStdHandle(key)
assert kernel.SetStdHandle(key,ctypes.c_void_p(-1))
real_run=subprocess.run;results=[]
try:
 for reproduce_old in (True,False):
  def route_reply(argv,**kw):
   if reproduce_old:kw.pop('stdin',None)
   return real_run([sys.executable,'-c',REPLY],**kw)
  try:
   with patch('windows_network.subprocess.run',side_effect=route_reply):hosts=windows_network.local_targets()
   results.append(['ok',len(hosts)])
  except OSError as error:results.append(['error',error.winerror])
finally:kernel.SetStdHandle(key,original)
print(json.dumps(results))
""".replace('REPLY',repr('print('+repr(json.dumps([self.record()]))+')'))
  result=subprocess.run([sys.executable,'-B','-c',code],cwd=pathlib.Path(__file__).resolve().parents[1],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=15,check=True)
  self.assertEqual(json.loads(result.stdout),[['error',6],['ok',253]])


class NetworkProbeTests(unittest.TestCase):
 def test_route_config_is_checked_without_device_probes(self):
  import windows_network_probe
  with tempfile.TemporaryDirectory() as directory,patch('windows_network_probe.read_records',return_value=[NetworkProviderTests().record()]):
   path=pathlib.Path(directory)/'result.json'
   self.assertEqual(windows_network_probe.run(path,renderer_ready=True),0)
   report=json.loads(path.read_text());self.assertEqual(report['target_count'],253);self.assertTrue(report['renderer_ready']);self.assertTrue(report['discovery_supported'])
 def test_no_default_route_is_a_valid_offline_configuration(self):
  import windows_network_probe
  with tempfile.TemporaryDirectory() as directory,patch('windows_network_probe.read_records',return_value=[]):
   path=pathlib.Path(directory)/'result.json'
   self.assertEqual(windows_network_probe.run(path,renderer_ready=True),0)
   report=json.loads(path.read_text());self.assertEqual(report['status'],'passed');self.assertFalse(report['discovery_supported']);self.assertEqual(report['target_count'],0)
 def test_helper_failure_cannot_be_reported_as_a_pass(self):
  import windows_network_probe,subprocess
  with tempfile.TemporaryDirectory() as directory,patch('windows_network_probe.read_records',side_effect=subprocess.TimeoutExpired('fixed local query',5)):
   path=pathlib.Path(directory)/'result.json'
   self.assertEqual(windows_network_probe.run(path,renderer_ready=True),1)
   report=json.loads(path.read_text());self.assertEqual(report['status'],'failed');self.assertEqual(report['exception'],'TimeoutExpired');self.assertIn('timed out',report['message'])

class DiscoveryTests(unittest.TestCase):
 def test_interface_failure_is_distinct_from_no_amplifier_and_retry_clears_it(self):
  import subprocess
  with patch('discovery.WINDOWS',True),patch('discovery.local_targets',side_effect=subprocess.TimeoutExpired('fixed local query',5)),patch('discovery.identify',side_effect=AssertionError('No probes permitted')) as identify:
   d=Discovery();d.start([],230400,1500);d.thread.join(2);state=d.snapshot()
   identify.assert_not_called();self.assertEqual(state['total'],0);self.assertIn('No network scan performed',state['message']);self.assertIn('timed out after 5 seconds',state['message']);self.assertEqual(state['configuration_error']['type'],'TimeoutExpired')
  with patch('discovery.WINDOWS',True),patch('discovery.local_targets',return_value=['192.0.2.1']),patch('discovery.identify',return_value={'mode':'tcp','host':'192.0.2.1','tcp_port':1500}):
   d.start([],230400,1500);d.thread.join(2);state=d.snapshot();self.assertIsNone(state['configuration_error']);self.assertEqual(len(state['results']),1)

 def test_synthetic_discovery_cancel_and_completion_no_io(self):
  with patch('discovery.local_targets',side_effect=AssertionError('network config read')),patch('discovery.identify',side_effect=AssertionError('device opened')):
   d=Discovery(offline=True);d.start(['COM10'],230400,1500)
   self.assertTrue(d.snapshot()['running']);d.stop();d.thread.join(2);self.assertEqual(d.snapshot()['results'],[]);self.assertIn('cancelled',d.snapshot()['message'])
   d.start([],230400,1500);d.thread.join(2);state=d.snapshot();self.assertEqual(state['checked'],4);self.assertEqual(state['total'],4);self.assertEqual(state['results'],[dict(mode='simulator',demo=True)])
 def test_real_windows_discovery_queries_tcp_only_and_is_bounded(self):
  seen=[]
  def probe(candidate,cancel):seen.append(candidate);return candidate
  with patch('discovery.WINDOWS',True),patch('discovery.local_targets',return_value=['192.0.2.1']),patch('discovery.identify',side_effect=probe):
   d=Discovery();d.start(['COM10'],230400,1500);d.thread.join(2)
   self.assertEqual([c['mode'] for c in seen],['tcp']);self.assertEqual(d.snapshot()['checked'],1)
 def test_cancellation_waits_for_active_probe_close_and_skips_queued(self):
  began=threading.Event();closed=threading.Event()
  def probe(candidate,cancel):began.set();cancel.wait(2);closed.set();return None
  with patch('discovery.WINDOWS',True),patch('discovery.local_targets',return_value=['192.0.2.'+str(i) for i in range(1,100)]),patch('discovery.identify',side_effect=probe):
   d=Discovery();d.start([],230400,1500);self.assertTrue(began.wait(1));d.stop();d.thread.join(3)
   self.assertFalse(d.snapshot()['running']);self.assertTrue(closed.is_set());self.assertLess(d.snapshot()['checked'],100)

class PreferenceTests(unittest.TestCase):
 def test_isolated_atomic_roundtrip_and_validation(self):
  with tempfile.TemporaryDirectory() as folder:
   path=pathlib.Path(folder)/'review.window.json';p=Preferences(path)
   p.save(dict(compact=True,top=True,theme='light',measurement='frequency',callsign='review',sections={'faults':False},full_size=[900,800],position=[-900,20],host='secret',auto_connect=True))
   self.assertEqual(Preferences(path).snapshot()['callsign'],'REVIEW');self.assertNotIn('host',p.snapshot());self.assertNotIn('auto_connect',p.snapshot());self.assertFalse(path.with_suffix('.tmp').exists())
   p.save(dict(theme='bad',full_size=[1,1],compact='true'));self.assertTrue(p.snapshot()['compact']);self.assertEqual(p.snapshot()['theme'],'light');self.assertEqual(p.snapshot()['full_size'],[900,800])
 def test_corrupt_preferences_and_unknown_objects(self):
  self.assertEqual(validate([]),{})
  with tempfile.TemporaryDirectory() as folder:
   path=pathlib.Path(folder)/'view.json';path.write_text('broken');self.assertEqual(Preferences(path).snapshot(),{})

class InstanceTests(unittest.TestCase):
 def test_metadata_path_is_stable_when_frozen_host_changes_directory(self):
  self.assertTrue(Instance('relative-review.json').path.is_absolute())

 def test_second_launch_activates_existing_session_and_releases(self):
  with tempfile.TemporaryDirectory() as folder,patch('endpoint_lock.lock_directory',return_value=pathlib.Path(folder)/'locks'):
   settings=pathlib.Path(folder)/'settings.json';first=Instance(settings);self.assertTrue(first.acquire());activated=threading.Event();c=Controller(settings,offline_only=True)
   server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(c,'activation-unit-test',activate=activated.set));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   first.publish(f'http://127.0.0.1:{server.server_port}/activation-unit-test/','activation-unit-test')
   try:
    second=Instance(settings);self.assertFalse(second.acquire());self.assertTrue(activated.is_set());self.assertIsNone(c.worker);second.close();self.assertTrue(first.path.exists())
   finally:server.shutdown();server.server_close();thread.join();first.close()
   self.assertFalse(first.path.exists());third=Instance(settings);self.assertTrue(third.acquire());third.close()
 def test_activation_metadata_cannot_redirect_token_to_external_host(self):
  with tempfile.TemporaryDirectory() as folder,patch('endpoint_lock.lock_directory',return_value=pathlib.Path(folder)/'locks'):
   path=pathlib.Path(folder)/'review.json';first=Instance(path);first.acquire();first.publish('http://example.test/secret/','secret')
   try:
    with patch('windows_instance.time.sleep'),patch('windows_instance.http.client.HTTPConnection') as opener:
     with self.assertRaises(RuntimeError):Instance(path).acquire()
     opener.assert_not_called()
   finally:first.close()
