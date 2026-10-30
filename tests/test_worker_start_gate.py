"""Deterministic process-start races; fake processes/channels, no device I/O."""
import contextlib,pathlib,queue,sys,tempfile,threading,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
import engine
class Channel(queue.Queue):
 def cancel_join_thread(self):pass
 def close(self):self.closed=True
class End:
 def poll(self):return False
 def close(self):self.closed=True
class DelayedProcess:
 def __init__(self,stop,mode='live'):
  self.stop=stop;self.mode=mode;self.entered=threading.Event();self.release=threading.Event();self.pid=None;self.exitcode=None;self.alive=False;self.starts=0
 def start(self):
  self.starts+=1;self.entered.set()
  if not self.release.wait(10):raise RuntimeError('Test did not release process startup')
  if self.mode=='failure':raise OSError('Synthetic delayed start failure')
  self.pid=4242;self.alive=self.mode=='live';self.exitcode=None if self.alive else 7
 def is_alive(self):return self.alive
 def join(self,timeout=None):
  if self.stop.is_set():self.alive=False;self.exitcode=0
 def terminate(self):self.alive=False;self.exitcode=-15
 def kill(self):self.alive=False;self.exitcode=-9
class WorkerStartGateTests(unittest.TestCase):
 @contextlib.contextmanager
 def controller(self,mode='live'):
  with tempfile.TemporaryDirectory() as folder:
   c=engine.Controller(pathlib.Path(folder)/'settings.json',offline_only=True,manual_connect=True);stop=threading.Event();p=DelayedProcess(stop,mode);errors=[]
   def connect():
    try:c.connect(dict(mode='simulator'))
    except BaseException as exc:errors.append(exc)
   with patch('engine.multiprocessing.Queue',side_effect=Channel),patch('engine.multiprocessing.Pipe',side_effect=lambda **kw:(End(),End())),patch('engine.StopFlag',return_value=stop),patch('engine.multiprocessing.Process',return_value=p) as factory:
    thread=threading.Thread(target=connect);thread.start()
    try:
     self.assertTrue(p.entered.wait(3));yield c,p,thread,errors,factory
    finally:
     p.release.set();thread.join(3);c.disconnect();self.assertFalse(thread.is_alive())
 def test_snapshots_remain_connecting_while_process_start_has_no_pid(self):
  with self.controller() as (c,p,thread,errors,factory):
   for _ in range(20):
    s=c.snapshot();self.assertEqual(s['state']['status'],'connecting');self.assertNotIn('exit code None',s['state']['message']);self.assertTrue(s['reader_present'])
   self.assertIsNone(p.pid);self.assertTrue(thread.is_alive());p.release.set();thread.join(3);self.assertEqual(errors,[])
   c.events.put(('state',dict(status='live',age_seconds=0,demo=True,forward_watts=0)))
   self.assertEqual(c.snapshot()['state']['status'],'live');self.assertEqual(p.starts,1);factory.assert_called_once()
 def test_delayed_start_failure_keeps_original_error_without_retry(self):
  with self.controller('failure') as (c,p,thread,errors,factory):
   self.assertEqual(c.snapshot()['state']['status'],'connecting');p.release.set();thread.join(3)
   self.assertEqual(len(errors),1);self.assertIsInstance(errors[0],OSError);s=c.snapshot();self.assertEqual(s['state']['status'],'error');self.assertIn('Synthetic delayed start failure',s['state']['message']);self.assertFalse(s['reader_present'])
   self.assertIsNone(c.events);self.assertIsNone(c.commands);self.assertIsNone(c.completion);factory.assert_called_once()
 def test_started_worker_exit_still_reports_actual_exit_code(self):
  with self.controller('exited') as (c,p,thread,errors,factory):
   p.release.set();thread.join(3);self.assertEqual(errors,[]);s=c.snapshot();self.assertEqual(s['state']['status'],'error');self.assertIn('exit code 7',s['state']['message']);self.assertTrue(s['reader_present']);factory.assert_called_once()
 def test_disconnect_waits_for_start_and_releases_worker_once(self):
  with self.controller() as (c,p,thread,errors,factory):
   done=threading.Event();disconnect=threading.Thread(target=lambda:(c.disconnect(),done.set()));disconnect.start()
   try:
    self.assertFalse(done.wait(.02));self.assertEqual(c.snapshot()['state']['status'],'connecting');p.release.set();thread.join(3);disconnect.join(3)
    self.assertTrue(done.is_set());self.assertEqual(errors,[]);self.assertEqual(c.snapshot()['state']['status'],'disconnected');self.assertIsNone(c.worker);self.assertFalse(p.alive);self.assertEqual(p.starts,1);factory.assert_called_once()
   finally:p.release.set();disconnect.join(3)
 def test_real_error_event_during_start_is_not_hidden_by_start_gate(self):
  with self.controller('exited') as (c,p,thread,errors,factory):
   c.events.put(('error','Synthetic worker error before start returns'))
   self.assertEqual(c.snapshot()['state']['message'],'Synthetic worker error before start returns');p.release.set();thread.join(3);self.assertEqual(errors,[])
   self.assertEqual(c.snapshot()['state']['message'],'Synthetic worker error before start returns');factory.assert_called_once()
if __name__=='__main__':unittest.main()
