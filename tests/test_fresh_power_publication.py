"""Offline publication-latency regressions; synthetic transports and clocks only."""
import pathlib,queue,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
import engine
from protocol import Session,FAST,SLOW
from simulator import SimulatorTransport
from read_only import QUERIES

class Clock:
 def __init__(self):self.now=1000.
 def time(self):return self.now
 def monotonic(self):return self.now
 def sleep(self,seconds):self.now+=seconds
class TimedSimulator(SimulatorTransport):
 query_interval=.05
 def __init__(self,clock):super().__init__();self.clock=clock;self.tag=None;self.drop=set();self.before_read=None;self.closed=False
 def write(self,data):
  self.tag=data
  if data in self.drop:self.writes.append(data.decode());return
  super().write(data)
 def read(self,timeout):
  self.clock.sleep(min(.04,timeout))
  if self.before_read:self.before_read(self.tag)
  return super().read(0) if self.buffer else b''
 def close(self):self.closed=True;super().close()
class Stop:
 def __init__(self):self.done=False
 def is_set(self):return self.done
 def wait(self,seconds):self.done=True
class Events:
 def __init__(self,wire,fail_first=False):self.wire=wire;self.rows=[];self.fail_first=fail_first
 def cancel_join_thread(self):pass
 def put(self,item):
  if item[0]=='state' and self.fail_first:self.fail_first=False;raise OSError('Synthetic state queue failure')
  self.rows.append((item,list(self.wire.writes)))

class FreshPowerPublicationTests(unittest.TestCase):
 def setUp(self):
  self.clock=Clock();self.patches=[patch('protocol.time.time',side_effect=self.clock.time),patch('protocol.time.monotonic',side_effect=self.clock.monotonic),patch('protocol.time.sleep',side_effect=self.clock.sleep)]
  for p in self.patches:p.start()
 def tearDown(self):
  for p in reversed(self.patches):p.stop()
 def session(self,wire=None,publish=None):
  wire=wire or TimedSimulator(self.clock);amp=Session(wire);amp.on_power=publish;return amp,wire
 def test_fresh_cache_is_visible_while_later_query_is_still_running(self):
  with tempfile.TemporaryDirectory() as d:
   c=engine.Controller(pathlib.Path(d)/'settings.json',offline_only=True);c.events=queue.Queue();c.state=dict(status='live',age_seconds=2.3,forward_watts=0,demo=True);c.received=self.clock.now;observed=[]
   amp,wire=self.session(publish=lambda state:c.events.put(('state',dict(state,demo=True))))
   def during_read(tag):
    if tag==b'^PWR;' and not observed:
     self.assertGreater(2.3+self.clock.now-1000,2.5) # The former cache would already be stale.
     s=c.snapshot()['state'];self.assertEqual(s['status'],'live');self.assertEqual(s['forward_watts'],0);self.assertLess(s['age_seconds'],.2);observed.append(s)
   wire.before_read=during_read; amp.poll(True);self.assertEqual(len(observed),1);c.events=None
 def test_callback_precedes_remaining_queries_without_changing_order_or_count(self):
  published=[];amp,wire=self.session();amp.on_power=lambda state:published.append((state,self.clock.now,list(wire.writes)));amp.poll(True)
  self.assertEqual(len(published),1);state,stamp,writes=published[0];self.assertEqual(writes,['^ON;','^VG;','^PWF;']);self.assertEqual(state['forward_watts'],0);self.assertEqual(state['age_seconds'],0);self.assertEqual(amp.last_live,stamp)
  self.assertEqual(wire.writes,['^'+tag+';' for tag in ('ON',)+FAST+SLOW])
 def test_failed_power_read_never_publishes_or_refreshes_and_next_poll_recovers(self):
  published=[];amp,wire=self.session(publish=published.append);amp.last_live=self.clock.now-3;old_stamp=amp.last_live;wire.drop.add(b'^PWF;');amp.poll()
  self.assertEqual(published,[]);self.assertEqual(amp.last_live,old_stamp);self.assertEqual(wire.writes.count('^PWF;'),1);self.assertEqual(amp.snapshot()['status'],'stale');self.assertIsNone(amp.snapshot()['forward_watts'])
  wire.drop.clear();amp.poll();self.assertEqual(len(published),1);self.assertEqual(wire.writes.count('^PWF;'),2);self.assertNotIn('PWF',published[0]['errors'])
 def test_genuine_staleness_still_clears_at_existing_boundary(self):
  published=[];amp,_=self.session(publish=published.append);amp.poll();stamp=amp.last_live;self.clock.now=stamp+2.5
  self.assertEqual(amp.snapshot()['status'],'stale');self.assertIsNone(amp.snapshot()['forward_watts']);self.assertEqual(amp.last_live,stamp);self.assertEqual(len(published),1)
 def test_later_timeout_does_not_mutate_already_published_snapshot(self):
  published=[];amp,wire=self.session(publish=published.append);wire.drop.add(b'^PWR;');amp.poll();self.assertEqual(len(published),1);self.assertEqual(published[0]['errors'],{});self.assertIn('PWR',amp.errors);self.assertEqual(wire.writes.count('^PWR;'),1)
 def test_cancelled_session_does_not_publish_early(self):
  published=[];wire=TimedSimulator(self.clock);amp=Session(wire,cancelled=lambda:True,on_power=published.append);amp.poll();self.assertEqual(published,[])
 def test_control_preflight_never_triggers_poll_callback_or_replays_setter(self):
  published=[];amp,wire=self.session(publish=published.append);amp.identify();amp.poll(True);published.clear();self.assertEqual(amp.action('operate')['status'],'confirmed');self.assertEqual(published,[]);self.assertEqual(wire.writes.count('^OS1;'),1)
 def test_powered_off_poll_does_not_publish_live_or_query_other_tags(self):
  published=[];wire=TimedSimulator(self.clock);wire.power=False;amp,_=self.session(wire,published.append);amp.poll(True);self.assertEqual(published,[]);self.assertEqual(wire.writes,['^ON;']);self.assertEqual(amp.snapshot()['status'],'powered_off')
 def run_worker(self,drop_power=False,fail_event=False):
  wire=TimedSimulator(self.clock)
  if drop_power:wire.drop.add(b'^PWF;')
  events=Events(wire,fail_event)
  with patch('engine.TCPTransport',return_value=wire),patch('engine.signal.signal'),patch('socket.socket',side_effect=AssertionError('No networking allowed')):
   engine.worker_main(dict(mode='tcp',host='192.0.2.18',tcp_port=1500,read_only=True),events,queue.Queue(),Stop())
  self.assertTrue(wire.closed);self.assertTrue(all(w.encode() in QUERIES for w in wire.writes));return wire,events
 def test_read_only_worker_publishes_early_and_final_states_with_mode_identity(self):
  wire,events=self.run_worker();states=[(item[1],writes) for item,writes in events.rows if item[0]=='state'];self.assertEqual(len(states),2);self.assertEqual(states[0][1][-1],'^PWF;');self.assertNotIn('^PWR;',states[0][1]);self.assertEqual(states[1][1][-1],'^FS;');self.assertTrue(all(s['demo'] is False and s['status']=='live' for s,_ in states));self.assertEqual(wire.writes.count('^PWF;'),1)
 def test_delayed_early_state_cannot_make_old_reading_live_on_arrival(self):
  _,events=self.run_worker();state=next(item[1] for item,_ in events.rows if item[0]=='state');stamp=state['_power_observed_at']
  with tempfile.TemporaryDirectory() as d:
   c=engine.Controller(pathlib.Path(d)/'settings.json',offline_only=True);c.events=queue.Queue();self.clock.now=stamp+3;c.events.put(('state',state));snapshot=c.snapshot()['state'];self.assertEqual(snapshot['status'],'stale');self.assertEqual(snapshot['age_seconds'],3);self.assertIsNone(snapshot['forward_watts']);self.assertNotIn('_power_observed_at',snapshot);self.assertIn('_power_observed_at',state);c.events=None
 def test_repeated_queued_updates_preserve_original_power_timestamp(self):
  _,events=self.run_worker();states=[item[1] for item,_ in events.rows if item[0]=='state'];stamp=states[0]['_power_observed_at'];self.assertEqual(states[-1]['_power_observed_at'],stamp)
  with tempfile.TemporaryDirectory() as d:
   c=engine.Controller(pathlib.Path(d)/'settings.json',offline_only=True);c.events=queue.Queue()
   for delay,state in zip((3,5),states):
    self.clock.now=stamp+delay;c.events.put(('state',state));snapshot=c.snapshot()['state'];self.assertEqual(snapshot['status'],'stale');self.assertEqual(snapshot['age_seconds'],delay);self.assertIsNone(snapshot['forward_watts'])
   c.events=None
 def test_worker_retains_final_stale_error_snapshot_after_failed_power_read(self):
  wire,events=self.run_worker(drop_power=True);states=[item[1] for item,_ in events.rows if item[0]=='state'];self.assertEqual(len(states),1);self.assertEqual(states[0]['status'],'stale');self.assertIn('PWF',states[0]['errors']);self.assertIsNone(states[0]['forward_watts']);self.assertEqual(wire.writes.count('^PWF;'),1)
 def test_early_queue_failure_closes_transport_and_preserves_error(self):
  wire,events=self.run_worker(fail_event=True);errors=[item[1] for item,_ in events.rows if item[0]=='error'];self.assertEqual(errors,['Synthetic state queue failure']);self.assertNotIn('^PWR;',wire.writes);self.assertEqual(wire.writes.count('^PWF;'),1)

if __name__=='__main__':unittest.main()
