"""Offline fake-clock regressions; no physical transport is constructed."""
import pathlib,sys,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from protocol import Protocol,Session
from read_only import QueryOnlyTransport
from simulator import SimulatorTransport
from transport import WindowsSerialTransport,TCPTransport,PosixSerialTransport

class Clock:
 def __init__(self):self.now=0.;self.sleeps=[]
 def monotonic(self):return self.now
 def sleep(self,seconds):self.sleeps.append(seconds);self.now+=seconds
class Wire:
 def __init__(self,clock,replies,interval=0):self.clock=clock;self.replies=list(replies);self.query_interval=interval;self.writes=[];self.reads=[]
 def write(self,data):self.writes.append((self.clock.now,data))
 def read(self,timeout):
  self.reads.append(timeout)
  if self.replies:
   elapsed,data=self.replies.pop(0);self.clock.now+=elapsed;return data
  self.clock.now+=timeout;return b''
 def close(self):pass

class TimingTests(unittest.TestCase):
 def setUp(self):
  self.clock=Clock();self.mono=patch('protocol.time.monotonic',side_effect=self.clock.monotonic);self.sleep=patch('protocol.time.sleep',side_effect=self.clock.sleep);self.mono.start();self.sleep.start()
 def tearDown(self):self.sleep.stop();self.mono.stop()
 def test_complete_reply_returned_by_final_read_is_inspected(self):
  w=Wire(self.clock,[(.251,b'^PWF0;')]);p=Protocol(w)
  self.assertEqual(p.query('PWF'),'^PWF0;');self.assertEqual(len(w.reads),1);self.assertEqual([d for _,d in w.writes],[b'^PWF;'])
 def test_reply_exactly_at_deadline_is_inspected(self):
  self.assertEqual(Protocol(Wire(self.clock,[(.25,b'^PWR0;')])).query('PWR'),'^PWR0;')
 def test_split_reply_completed_by_final_read(self):
  w=Wire(self.clock,[(.24,b'^PW'),(.02,b'F0;')]);self.assertEqual(Protocol(w).query('PWF'),'^PWF0;');self.assertEqual(len(w.reads),2)
 def test_partial_final_read_times_out_without_extra_read_or_replay(self):
  w=Wire(self.clock,[(.251,b'^PW')]);p=Protocol(w)
  with self.assertRaisesRegex(TimeoutError,'No response to PWF'):p.query('PWF')
  self.assertEqual(len(w.reads),1);self.assertEqual(len(w.writes),1)
 def test_unrelated_final_frame_does_not_extend_deadline(self):
  w=Wire(self.clock,[(.251,b'^OTHER0;')])
  with self.assertRaises(TimeoutError):Protocol(w).query('PWF')
  self.assertEqual(len(w.reads),1)
 def test_empty_reads_remain_bounded(self):
  w=Wire(self.clock,[])
  with self.assertRaises(TimeoutError):Protocol(w).query('PWF')
  self.assertAlmostEqual(self.clock.now,.25);self.assertTrue(all(0<t<=.05 for t in w.reads));self.assertEqual(len(w.writes),1)
 def test_error_frame_from_final_read_is_not_hidden_by_timeout(self):
  with self.assertRaisesRegex(ValueError,'not supported'):Protocol(Wire(self.clock,[(.251,b'^?;')])).query('PWF')
 def test_oversized_response_is_rejected_before_parsing(self):
  with self.assertRaisesRegex(ValueError,'oversized'):Protocol(Wire(self.clock,[(.251,b'x'*4097+b'^PWF0;')])).query('PWF')
 def test_windows_usb_declares_pacing_without_constructing_transport(self):
  self.assertEqual(WindowsSerialTransport.query_interval,.05)
  self.assertFalse(hasattr(TCPTransport,'query_interval'));self.assertFalse(hasattr(PosixSerialTransport,'query_interval'))
 def test_gap_is_measured_from_query_completion(self):
  w=Wire(self.clock,[(.02,b'^PWF0;'),(.02,b'^PWR0;')],.05);p=Protocol(w);p.query('PWF');p.query('PWR')
  self.assertAlmostEqual(w.writes[1][0],.07);self.assertEqual(len(self.clock.sleeps),1)
 def test_elapsed_idle_time_counts_toward_gap(self):
  w=Wire(self.clock,[(.01,b'^PWF0;'),(.01,b'^PWR0;')],.05);p=Protocol(w);p.query('PWF');self.clock.now+=.03;p.query('PWR')
  self.assertAlmostEqual(self.clock.sleeps[0],.02)
 def test_timeout_is_not_retried_and_next_query_is_paced(self):
  w=Wire(self.clock,[(.251,b'')],.05);p=Protocol(w)
  with self.assertRaises(TimeoutError):p.query('PWF')
  w.replies=[(.01,b'^PWR0;')];p.query('PWR');self.assertAlmostEqual(w.writes[1][0],.301);self.assertEqual([d for _,d in w.writes],[b'^PWF;',b'^PWR;'])
 def test_read_only_wrapper_preserves_gap_and_exact_write_allowlist(self):
  w=Wire(self.clock,[(.01,b'^PWF0;'),(.01,b'^PWR0;')],.05);guard=QueryOnlyTransport(w);p=Protocol(guard);p.query('PWF');p.query('PWR')
  self.assertAlmostEqual(w.writes[1][0],.06)
  for data in [b'^OS1;',b'^ON1;',b'^FT;',b';;;',b'^PWF;^OS1;']:
   with self.assertRaises(ValueError):guard.write(data)
  self.assertEqual(len(w.writes),2)
 def test_unconfigured_transport_and_simulator_are_not_paced(self):
  w=Wire(self.clock,[(0,b'^PWF0;'),(0,b'^PWR0;')]);p=Protocol(w);p.query('PWF');p.query('PWR');self.assertFalse(self.clock.sleeps)
  self.assertEqual(Protocol(SimulatorTransport()).query_interval,0)
 def test_direct_setter_is_not_paced_or_replayed(self):
  w=Wire(self.clock,[(.01,b'^OS0;'),(.01,b'^OS1;')],.05);p=Protocol(w);p.query('OS');p.send('^OS1;');self.assertAlmostEqual(w.writes[1][0],.01);p.query('OS')
  self.assertEqual([d for _,d in w.writes],[b'^OS;',b'^OS1;',b'^OS;']);self.assertAlmostEqual(w.writes[2][0],.06)
 def test_unconfirmed_control_with_pacing_sends_setter_once(self):
  class IgnoredOperate(SimulatorTransport):
   query_interval=.05
   def write(self,data):
    if data==b'^OS1;':self.writes.append(data.decode());return
    super().write(data)
  w=IgnoredOperate();s=Session(w);s.identify();s.poll(True);self.assertEqual(s.action('operate')['status'],'unconfirmed');self.assertEqual(w.writes.count('^OS1;'),1)

if __name__=='__main__':unittest.main()
