"""Offline worker-exit regressions: synthetic transports only, no wake/network/device I/O."""
import pathlib,sys,tempfile,queue,unittest,multiprocessing,time
from unittest.mock import patch,Mock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
import engine,power

class DroppedEvents:
 def cancel_join_thread(self):pass
 def put(self,item):pass
 def get_nowait(self):raise queue.Empty

def offline_failed_worker(config,events,commands,stop):
 # Drop all telemetry-queue events to reproduce teardown loss deterministically.
 with patch('engine.wake_connect',side_effect=OSError('Synthetic wake TCP timeout')),patch('socket.socket',side_effect=AssertionError('Network access forbidden')):
  engine.worker_main(config,DroppedEvents(),commands,stop)

def offline_shutdown_worker(config,events,commands,stop):
 from simulator import SimulatorTransport
 transport=SimulatorTransport();local_commands=queue.Queue()
 local_commands.put(dict(id='shutdown',action='power_off',expires=time.time()+10))
 with patch('engine.TCPTransport',return_value=transport),patch('socket.socket',side_effect=AssertionError('Network access forbidden')):
  engine.worker_main(config,DroppedEvents(),local_commands,stop)
 assert transport.writes.count('^ON0;')==1
 assert not any(x in transport.writes for x in ('^ON1;','^OS1;','^OS0;','^FT;'))

def offline_late_failure_worker(config,events,commands,stop):
 from protocol import Session
 from simulator import SimulatorTransport
 class FailsAfterStartup(Session):
  def poll(self,slow=False):raise OSError('Synthetic telemetry lost after confirmed startup')
 with patch('engine.wake_connect',return_value=SimulatorTransport()),patch('engine.Session',FailsAfterStartup),patch('socket.socket',side_effect=AssertionError('Network access forbidden')):
  engine.worker_main(config,DroppedEvents(),commands,stop)

class StartupExitTests(unittest.TestCase):
 def test_launch_failure_cleans_resources_reports_error_and_allows_manual_recovery(self):
  for failure_phase in ('constructor','start'):
   with self.subTest(failure_phase=failure_phase),tempfile.TemporaryDirectory() as directory:
    c=engine.Controller(pathlib.Path(directory)/'settings.json',offline_only=True);queues=[];pipes=[]
    original_queue=engine.multiprocessing.Queue;original_pipe=engine.multiprocessing.Pipe
    def make_queue(*a,**kw):
     q=original_queue(*a,**kw);queues.append(q);return q
    def make_pipe(*a,**kw):
     ends=original_pipe(*a,**kw);pipes.extend(ends);return ends
    worker=Mock();worker.pid=None;worker.start.side_effect=OSError('Synthetic launch failure')
    try:
     with patch('engine.multiprocessing.Queue',side_effect=make_queue),patch('engine.multiprocessing.Pipe',side_effect=make_pipe),patch('engine.multiprocessing.Process',side_effect=OSError('Synthetic launch failure') if failure_phase=='constructor' else None,return_value=worker) as process,patch('socket.socket',side_effect=AssertionError('Network access forbidden')):
      with self.assertRaisesRegex(OSError,'Synthetic launch failure'):c.connect(dict(mode='simulator'))
      snap=c.snapshot();self.assertEqual(snap['state']['status'],'error');self.assertIn('Synthetic launch failure',snap['state']['message']);self.assertTrue(snap['state']['demo'])
      self.assertIsNone(c.worker);self.assertIsNone(c.events);self.assertIsNone(c.commands);self.assertIsNone(c.completion);self.assertIsNone(c.stop)
      self.assertTrue(all(q._closed for q in queues));self.assertTrue(all(x.closed for x in pipes));process.assert_called_once();self.assertEqual(snap['actions'],[])
     c.connect(dict(mode='simulator'));deadline=time.monotonic()+5
     while c.snapshot()['state']['status']!='live' and time.monotonic()<deadline:time.sleep(.02)
     self.assertEqual(c.snapshot()['state']['status'],'live')
    finally:c.disconnect()
 def test_confirmed_startup_survives_later_telemetry_failure_with_dropped_queue(self):
  with tempfile.TemporaryDirectory() as directory:
   c=engine.Controller(pathlib.Path(directory)/'settings.json');c.config.update(mode='tcp',host='192.0.2.18',tcp_port=1500,wake_mac='54:10:EC:14:75:22')
   try:
    with patch('engine.worker_main',offline_late_failure_worker):c.action(dict(action='power_on',generation=c.generation))
    c.worker.join(10);self.assertFalse(c.worker.is_alive());s=c.snapshot()
    self.assertEqual(s['state']['status'],'error');self.assertIn('Synthetic telemetry lost',s['state']['message'])
    self.assertEqual(len(s['actions']),1);self.assertEqual(s['actions'][0]['action'],'power_on');self.assertEqual(s['actions'][0]['status'],'confirmed');self.assertIn('startup confirmed',s['actions'][0]['message'])
    self.assertEqual(c.snapshot()['actions'],s['actions']);self.assertIsNone(s['state']['forward_watts'])
   finally:c.disconnect()
 def test_original_startup_error_survives_dropped_queue_in_spawned_worker(self):
  with tempfile.TemporaryDirectory() as directory:
   c=engine.Controller(pathlib.Path(directory)/'settings.json')
   c.config.update(mode='tcp',host='192.0.2.18',tcp_port=1500,wake_mac='54:10:EC:14:75:22')
   try:
    with patch('engine.worker_main',offline_failed_worker):
     c.action(dict(action='power_on',generation=c.generation))
    c.worker.join(10);self.assertFalse(c.worker.is_alive())
    s=c.snapshot()
    self.assertEqual(s['state']['status'],'error')
    self.assertIn('Synthetic wake TCP timeout',s['state']['message'])
    self.assertEqual(s['actions'][0]['status'],'failed')
    self.assertIn('Synthetic wake TCP timeout',s['actions'][0]['message'])
    self.assertIsNone(s['state']['forward_watts'])
    self.assertEqual(c.snapshot()['actions'],s['actions'])
   finally:c.disconnect()
 def test_shutdown_completion_survives_dropped_queue_and_late_states(self):
  with tempfile.TemporaryDirectory() as directory:
   c=engine.Controller(pathlib.Path(directory)/'settings.json')
   try:
    with patch('engine.worker_main',offline_shutdown_worker):c.connect(dict(mode='tcp',host='192.0.2.18'))
    c.worker.join(10);self.assertEqual(c.worker.exitcode,0)
    s=c.snapshot();self.assertEqual(s['state']['status'],'powered_off');self.assertEqual(s['actions'][0]['status'],'confirmed')
    # A late telemetry message must never overwrite authoritative completion.
    c.events.put(('state',dict(status='live',powered_on=True)))
    time.sleep(.02);self.assertEqual(c.snapshot()['state']['status'],'powered_off')
    self.assertIsNone(c.completion)
    c.disconnect();self.assertFalse(c.worker_finished)
    c.connect(dict(mode='simulator'))
    deadline=time.monotonic()+5
    while c.snapshot()['state']['status']!='live' and time.monotonic()<deadline:time.sleep(.02)
    self.assertEqual(c.snapshot()['state']['status'],'live')
   finally:c.disconnect()
 def test_fast_success_during_connect_is_not_replaced_with_queued(self):
  with tempfile.TemporaryDirectory() as directory:
   c=engine.Controller(pathlib.Path(directory)/'settings.json');c.config.update(mode='tcp',wake_mac='54:10:EC:14:75:22')
   def connect(value,power_request=None):c.action_log=[dict(id=power_request,action='power_on',status='confirmed',message='Synthetic startup confirmed')]
   with patch.object(c,'connect',side_effect=connect):r=c.action(dict(action='power_on',generation=c.generation))
   self.assertEqual(r['status'],'confirmed');self.assertEqual(c.action_log,[r])
 def test_cancel_after_one_wake_never_repeats_packet_or_connect(self):
  cfg=dict(wake_mac='54:10:EC:14:75:22',wake_broadcast='255.255.255.255',host='192.0.2.18',tcp_port=1500)
  cancelled=Mock(side_effect=[False,True,True]);connect=Mock()
  with patch('power.wake') as wake:
   with self.assertRaisesRegex(ValueError,'after one wake packet'):power.wake_connect(cfg,cancelled,connect,lambda _:None)
   wake.assert_called_once();connect.assert_not_called()
 def test_fast_result_during_connect_is_not_replaced_with_queued(self):
  with tempfile.TemporaryDirectory() as directory:
   c=engine.Controller(pathlib.Path(directory)/'settings.json');c.config.update(mode='tcp',wake_mac='54:10:EC:14:75:22')
   def connect(value,power_request=None):
    c.action_log=[dict(id=power_request,action='power_on',status='failed',message='Immediate synthetic startup failure')]
    c.clear('error','Immediate synthetic startup failure')
   with patch.object(c,'connect',side_effect=connect):r=c.action(dict(action='power_on',generation=c.generation))
   self.assertEqual(r['status'],'failed');self.assertEqual(c.action_log,[r])
 def test_abrupt_worker_exit_fails_pending_request_without_retry(self):
  with tempfile.TemporaryDirectory() as directory:
   c=engine.Controller(pathlib.Path(directory)/'settings.json');c.worker=Mock();c.worker.is_alive.return_value=False;c.worker.exitcode=7
   c.clear('connecting','Waiting');c.action_log=[dict(id='x',action='power_on',status='queued',message='Waiting')]
   s=c.snapshot();self.assertEqual(s['actions'][0]['status'],'failed');self.assertIn('7',s['state']['message'])
   self.assertEqual(c.snapshot()['actions'],s['actions']);c.worker=None
 def test_wake_timeout_preserves_last_connection_error_and_sends_once(self):
  cfg=dict(wake_mac='54:10:EC:14:75:22',wake_broadcast='255.255.255.255',host='192.0.2.18',tcp_port=1500)
  connect=Mock(side_effect=OSError('Synthetic network unreachable'))
  with patch('power.wake') as wake,patch('power.time.monotonic',side_effect=[0,16]):
   with self.assertRaisesRegex(OSError,'Synthetic network unreachable'):power.wake_connect(cfg,lambda:False,connect,lambda _:None)
   wake.assert_called_once();connect.assert_called_once()

if __name__=='__main__':unittest.main()
