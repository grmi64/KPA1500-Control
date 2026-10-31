"""Launch policy and read-only safeguards: mocks/simulator only, no hardware."""
import json,pathlib,sys,tempfile,threading,time,types,unittest,io
from unittest.mock import Mock,MagicMock,patch
from contextlib import redirect_stderr
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
import engine,windows_app,windows_launch
from read_only import QueryOnlyTransport,QUERIES
from simulator import SimulatorTransport
from protocol import Session
from server import handler_for

def fail_simulator_reader(config,events,commands,stop):
 with patch('engine.Session.poll',side_effect=OSError('Synthetic reader failure')):engine.worker_main(config,events,commands,stop)

class LaunchTests(unittest.TestCase):
 def test_ordinary_launch_uses_hardware_but_review_and_smoke_remain_offline(self):
  self.assertEqual(windows_launch.initial_mode(),'hardware')
  self.assertEqual(windows_launch.initial_mode(frozen=True,executable='KPA1500 Control.exe'),'hardware')
  self.assertEqual(windows_launch.initial_mode(frozen=True,executable='KPA1500 Control Review.exe'),'simulation')
  self.assertEqual(windows_launch.initial_mode(smoke=True),'simulation')
  self.assertEqual(windows_launch.initial_mode(demo=True),'simulation')
  self.assertEqual(windows_launch.initial_mode(read_only=True),'read-only')
  self.assertEqual(windows_launch.initial_mode(hardware=True,frozen=True,executable='KPA1500 Control Review.exe'),'hardware')
 def value(self,mode='read-only'):return dict(mode=mode,confirmed=True,connection=dict(mode='tcp',host='192.0.2.18',tcp_port=1500,baud=230400))
 def state(self):return dict(state=dict(status='disconnected'),actions=[])
 def test_modes_are_explicit_validated_and_profiles_are_distinct(self):
  with tempfile.TemporaryDirectory() as folder:
   base=pathlib.Path(folder)/'sim.json';paths=[windows_launch.mode_settings(base,m) for m in windows_launch.MODES]
   self.assertEqual(len(set(paths)),3);self.assertEqual(paths[0],base.resolve())
   for mode,flag in [('simulation','--demo'),('read-only','--read-only'),('hardware','--hardware')]:
    argv=windows_launch.prepare_reopen(self.value(mode),self.state(),base)
    self.assertEqual(argv[0],flag);self.assertIn('--settings='+str(base.resolve()),argv)
    if mode!='simulation':self.assertIn('--host=192.0.2.18',argv)
   for change in [dict(confirmed=False),dict(mode='bad'),dict(connection=dict(mode='tcp',host='--hardware',tcp_port=1500)),dict(connection=dict(mode='tcp',host='192.0.2.1',tcp_port=True)),dict(connection=dict(mode='usb',port='COM1;evil',baud=230400))]:
    value=self.value();value.update(change)
    with self.assertRaises(ValueError):windows_launch.prepare_reopen(value,self.state(),base)
   value=self.value();value['connection']=dict(mode='usb',port='',baud=230400)
   argv=windows_launch.prepare_reopen(value,self.state(),base);self.assertIn('--connection-type=usb',argv)
 def test_mode_switch_requires_disconnect_no_scan_no_pending_and_no_duplicate(self):
  with tempfile.TemporaryDirectory() as folder:
   c=engine.Controller(pathlib.Path(folder)/'sim.json',offline_only=True);d=Mock();d.snapshot.return_value={'running':False}
   w=windows_launch.LaunchWorkflow(c,d,c.settings,'simulation')
   with patch('socket.socket',side_effect=AssertionError('network forbidden')),patch('engine.SerialTransport',side_effect=AssertionError('USB forbidden')):
    c.worker=Mock()
    with self.assertRaises(ValueError):w.request(self.value())
    c.worker=None;d.snapshot.return_value={'running':True}
    with self.assertRaises(ValueError):w.request(self.value())
    d.snapshot.return_value={'running':False};c.action_log=[dict(status='queued')]
    with self.assertRaises(ValueError):w.request(self.value())
    c.action_log=[];c.operation.acquire()
    try:
     with self.assertRaises(ValueError):w.request(self.value())
    finally:c.operation.release()
    self.assertTrue(w.request(self.value())['reopening']);self.assertIsNone(c.worker)
    with self.assertRaises(ValueError):w.request(self.value('hardware'))
   self.assertFalse(c.settings.exists())
 def test_confirmed_handoff_blocks_late_connections_controls_and_settings(self):
  with tempfile.TemporaryDirectory() as folder:
   c=engine.Controller(pathlib.Path(folder)/'sim.json',offline_only=True);d=Mock();d.snapshot.return_value={'running':False}
   w=windows_launch.LaunchWorkflow(c,d,c.settings,'simulation');w.request(self.value())
   with patch('engine.SimulatorTransport',side_effect=AssertionError('late transport forbidden')):
    with self.assertRaises(ValueError):c.connect(dict(mode='simulator'))
    with self.assertRaises(ValueError):c.action(dict(action='power_on',generation=c.generation))
    with self.assertRaises(ValueError):c.save_settings(dict(share_readings=False))
   self.assertIsNone(c.worker);self.assertTrue(c.launch_pending)
 def test_smoke_cannot_request_hardware_or_any_mode_restart(self):
  with tempfile.TemporaryDirectory() as folder:
   c=engine.Controller(pathlib.Path(folder)/'sim.json',offline_only=True);w=windows_launch.LaunchWorkflow(c,Mock(),c.settings,'simulation',restricted=True)
   for mode in windows_launch.MODES:
    with self.assertRaises(ValueError):w.request(self.value(mode))
   self.assertIsNone(w.pending)
 def test_relaunch_is_structured_own_executable_only(self):
  with patch('windows_launch.subprocess.Popen') as launch,patch.object(windows_launch.sys,'frozen',True,create=True):
   windows_launch.launch_replacement(['--demo','--settings=/path with spaces/review.json'])
   call=launch.call_args;self.assertEqual(call.args[0],[sys.executable,'--demo','--settings=/path with spaces/review.json']);self.assertFalse(call.kwargs['shell']);self.assertEqual(call.kwargs['env']['PYINSTALLER_RESET_ENVIRONMENT'],'1')
 def test_cli_rejects_smoke_hardware_conflicts_before_gui_or_transport(self):
  with patch('windows_app.configure_process_dpi') as dpi,redirect_stderr(io.StringIO()):
   for argv in (['--hardware','--smoke-test'],['--read-only','--smoke-test'],['--demo','--hardware'],['--host=192.0.2.1'],['--smoke-reopen']):
    with self.assertRaises(SystemExit):windows_app.main(argv)
   dpi.assert_not_called()
 def test_hardware_modes_start_disconnected_without_even_enumerating_ports(self):
  with tempfile.TemporaryDirectory() as folder:
   base=pathlib.Path(folder)/'sim.json'
   for flags,mode in [([], 'hardware'),(['--read-only'],'read-only'),(['--hardware'],'hardware')]:
    profile=windows_launch.mode_settings(base,mode);profile.write_text(json.dumps(dict(mode='tcp',host='192.0.2.18',tcp_port=1500,auto_connect=True,share_readings=False)))
    server=MagicMock();server.server_port=12345;server.RequestHandlerClass.discovery.thread=None
    view=types.SimpleNamespace(__file__=str(pathlib.Path(folder)/'webview/__init__.py'),settings={},create_window=Mock(return_value=MagicMock()),start=Mock())
    with patch.object(windows_app.sys,'platform','win32'),patch.dict('sys.modules',{'webview':view}),patch('windows_forms.install'),patch('windows_app.configure_process_dpi'),patch('windows_app.ensure_webview2_runtime'),patch('windows_app.Instance') as instance,patch('windows_app.ThreadingHTTPServer',return_value=server),patch('socket.socket',side_effect=AssertionError('network forbidden')),patch('engine.SerialTransport',side_effect=AssertionError('USB forbidden')),patch('engine.ports',side_effect=AssertionError('enumeration forbidden')),patch.object(engine.Controller,'connect',side_effect=AssertionError('startup connect forbidden')):
     instance.return_value.acquire.return_value=True
     self.assertEqual(windows_app.main(flags+['--settings',str(base)]),0)
     instance.return_value.close.assert_called_once();self.assertIn(windows_launch.MODES[mode],view.create_window.call_args.args[0]);view.start.assert_called_once()
 def test_endpoint_launch_and_handoff_refuse_existing_target_without_activation(self):
  from windows_instance import Instance
  from http.server import ThreadingHTTPServer
  with tempfile.TemporaryDirectory() as folder:
   base=pathlib.Path(folder)/'simulation.json';target=windows_launch.mode_settings(base,'read-only')
   current=engine.Controller(target,offline_only=True,read_only=True,manual_connect=True)
   current.config.update(mode='tcp',host='192.0.2.19',tcp_port=1500)
   current.clear('live','Synthetic cached session, no hardware transport.')
   activated=threading.Event();owner=Instance(target);self.assertTrue(owner.acquire())
   server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(current,'target-session-test',activate=activated.set));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   owner.publish(f'http://127.0.0.1:{server.server_port}/target-session-test/','target-session-test')
   try:
    with patch.object(windows_app.sys,'platform','win32'),patch('windows_app.configure_process_dpi'),patch('windows_app.Controller',side_effect=AssertionError('New controller forbidden')):
     with self.assertRaisesRegex(RuntimeError,'already open'):windows_app.main(['--read-only','--settings',str(base),'--connection-type=tcp','--host=192.0.2.18','--tcp-port','1500'])
     with self.assertRaisesRegex(RuntimeError,'already open'):windows_app.main(['--read-only','--settings',str(base),'--mode-handoff'])
    self.assertFalse(activated.is_set());self.assertEqual(current.config['host'],'192.0.2.19');self.assertEqual(current.state['status'],'live')
    # Ordinary duplicate launch retains its existing activation behavior.
    duplicate=Instance(target);self.assertFalse(duplicate.acquire());duplicate.close();self.assertTrue(activated.is_set())
   finally:server.shutdown();server.server_close();thread.join(2);owner.close();current.disconnect()
 def test_failed_reader_can_disconnect_then_switch_modes_without_reconnecting(self):
  with tempfile.TemporaryDirectory() as folder:
   c=engine.Controller(pathlib.Path(folder)/'sim.json',offline_only=True,manual_connect=True)
   try:
    with patch('engine.worker_main',fail_simulator_reader):c.connect(dict(mode='simulator'))
    c.worker.join(5);self.assertFalse(c.worker.is_alive());snapshot=c.snapshot()
    self.assertEqual(snapshot['state']['status'],'error');self.assertTrue(snapshot['reader_present'])
    d=Mock();d.snapshot.return_value={'running':False};w=windows_launch.LaunchWorkflow(c,d,c.settings,'simulation')
    with self.assertRaises(ValueError):w.request(self.value('simulation'))
    c.disconnect();self.assertFalse(c.snapshot()['reader_present']);self.assertEqual(c.snapshot()['state']['status'],'disconnected')
    self.assertTrue(w.request(self.value('simulation'))['reopening']);self.assertIsNone(c.worker)
   finally:c.disconnect()
 def test_abrupt_reader_exit_keeps_state_api_responsive_and_fails_pending_request(self):
  from http.server import ThreadingHTTPServer
  import http.client
  with tempfile.TemporaryDirectory() as folder:
   c=engine.Controller(pathlib.Path(folder)/'sim.json',offline_only=True,manual_connect=True);server=None;thread=None
   try:
    c.connect(dict(mode='simulator'));deadline=time.monotonic()+5
    while c.snapshot()['state']['status']!='live' and time.monotonic()<deadline:time.sleep(.02)
    self.assertEqual(c.snapshot()['state']['status'],'live')
    c.action_log=[dict(id='not-sent',action='operate',status='queued',message='Synthetic queued record only')]
    c.worker.terminate();c.worker.join(5);self.assertFalse(c.worker.is_alive())
    snapshot=c.snapshot();self.assertEqual(snapshot['state']['status'],'error');self.assertIsNone(snapshot['state']['forward_watts'])
    self.assertEqual(snapshot['actions'][0]['status'],'failed');self.assertIsNone(c.completion)
    server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(c,'reader-exit-test'));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=2)
    connection.request('GET','/reader-exit-test/state');response=connection.getresponse();self.assertEqual(response.status,200);self.assertEqual(json.loads(response.read())['state']['status'],'error')
    connection.request('POST','/reader-exit-test/disconnect','{}',{'X-Amp-Token':'reader-exit-test','Content-Type':'application/json'});response=connection.getresponse();self.assertEqual(response.status,200);self.assertEqual(json.loads(response.read())['state']['status'],'disconnected');connection.close()
    self.assertIsNone(c.worker);self.assertEqual(c.action_log,[])
   finally:
    if server:server.shutdown();server.server_close();thread.join(2)
    c.disconnect()
 def test_manual_connect_ignores_saved_autoconnect_and_rejects_enabling_it(self):
  with tempfile.TemporaryDirectory() as folder:
   path=pathlib.Path(folder)/'settings.json';path.write_text(json.dumps(dict(mode='tcp',host='192.0.2.18',tcp_port=1500,auto_connect=True)))
   c=engine.Controller(path,manual_connect=True)
   with patch.object(c,'connect',side_effect=AssertionError('startup connect forbidden')):c.startup()
   self.assertFalse(c.config['auto_connect'])
   with self.assertRaises(ValueError):c.save_settings(dict(auto_connect=True))

class ReadOnlyTests(unittest.TestCase):
 def test_exact_queries_only_and_normal_poll_identify_are_supported(self):
  transport=SimulatorTransport();wrapped=QueryOnlyTransport(transport);s=Session(wrapped)
  s.identify();s.read('MA');s.read('WL');s.poll(slow=True);self.assertEqual(s.snapshot()['status'],'live')
  for query in QUERIES:wrapped.write(query)
  writes=list(transport.writes)
  for data in (b';;;',b'^ON1;',b'^ON0;',b'^OS1;',b'^OS0;',b'^FT;',b'^FE;',b'^FLC;',b'^FC1;',b'^AMI;',b'^AMB;',b'^AN1;',b'^PWF;^ON1;',b'^PWF;^OS;',b'^PWF;\n',b'',b'^FAKE;','^PWF;'):
   with self.assertRaises(ValueError):wrapped.write(data)
  self.assertEqual(transport.writes,writes)
 def test_all_controller_actions_are_blocked_before_wake_or_transport(self):
  with tempfile.TemporaryDirectory() as folder:
   c=engine.Controller(pathlib.Path(folder)/'read.json',read_only=True,manual_connect=True)
   with patch('engine.wake_connect',side_effect=AssertionError('wake forbidden')),patch('engine.SerialTransport',side_effect=AssertionError('USB forbidden')),patch('engine.TCPTransport',side_effect=AssertionError('TCP forbidden')):
    for action in engine.ACTIONS:
     with self.assertRaisesRegex(ValueError,'Read-only'):c.action(dict(action=action,generation=c.generation,confirm_power_off=True))
   self.assertTrue(c.snapshot()['read_only']);self.assertIsNone(c.worker)
 def test_worker_rejects_injected_startup_before_opening_any_transport(self):
  import queue
  for key in ('power_request','wake_request'):
   events=Mock();events.cancel_join_thread=Mock();stop=Mock();stop.is_set.return_value=False
   with patch('engine.wake_connect',side_effect=AssertionError('wake forbidden')),patch('engine.SerialTransport',side_effect=AssertionError('USB forbidden')),patch('engine.TCPTransport',side_effect=AssertionError('TCP forbidden')):
    engine.worker_main(dict(mode='tcp',read_only=True,**{key:'injected'}),events,queue.Queue(),stop)
   self.assertTrue(any(call.args[0][0]=='error' and 'Read-only' in call.args[0][1] for call in events.put.call_args_list))
 def test_worker_blocks_injected_command_queue_but_keeps_query_telemetry(self):
  import queue
  commands=queue.Queue();commands.put(dict(id='injected',action='power_off',expires=time.time()+10));stop=engine.StopFlag();transport=SimulatorTransport();seen=[]
  events=Mock()
  def record(event):
   seen.append(event)
   if event[0]=='action':stop.set()
  events.put.side_effect=record
  with patch('engine.SimulatorTransport',return_value=transport):engine.worker_main(dict(mode='simulator',read_only=True),events,commands,stop)
  self.assertTrue(any(kind=='action' and data['status']=='failed' for kind,data in seen));self.assertTrue(transport.writes);self.assertTrue(all(frame.encode('ascii') in QUERIES for frame in transport.writes))
 def test_spawned_read_only_simulator_reports_telemetry_and_releases_worker(self):
  with tempfile.TemporaryDirectory() as folder:
   c=engine.Controller(pathlib.Path(folder)/'read.json',read_only=True,manual_connect=True)
   try:
    c.connect(dict(mode='simulator'));deadline=time.monotonic()+5
    while c.snapshot()['state']['status']!='live' and time.monotonic()<deadline:time.sleep(.02)
    self.assertEqual(c.snapshot()['state']['status'],'live');self.assertTrue(c.snapshot()['read_only'])
    with self.assertRaises(ValueError):c.action(dict(action='operate',generation=c.generation))
   finally:c.disconnect()
   self.assertIsNone(c.worker)
 def test_finish_reopen_requires_confirmed_pending_request(self):
  bridge=windows_app.DisplayBridge();bridge._launch=Mock(pending=None)
  with self.assertRaises(ValueError):bridge.finish_launch_mode()
 def test_direct_local_http_control_is_rejected(self):
  from http.server import ThreadingHTTPServer
  import http.client
  with tempfile.TemporaryDirectory() as folder:
   c=engine.Controller(pathlib.Path(folder)/'read.json',read_only=True);server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(c,'offline-token'));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   try:
    connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=2)
    connection.request('POST','/offline-token/control',json.dumps(dict(action='power_on',generation=c.generation)),{'X-Amp-Token':'offline-token','Content-Type':'application/json'})
    response=connection.getresponse();self.assertEqual(response.status,400);self.assertIn('Read-only',response.read().decode());connection.close();self.assertIsNone(c.worker)
   finally:server.shutdown();server.server_close();thread.join(2)
