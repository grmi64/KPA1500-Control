import pathlib,sys,threading,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from windows_close import CloseCoordinator
class EventSet:
 def __init__(self):self.loaded=threading.Event();self.closed=threading.Event()
class FakeWindow:
 def __init__(self):self.events=EventSet();self.events.loaded.set();self.requested=threading.Event();self.resumed=threading.Event();self.callback=None;self.destroyed=0
 def evaluate_js(self,script,callback=None):
  if callback:self.callback=callback;self.requested.set()
  else:self.resumed.set()
 def destroy(self):
  self.destroyed+=1
  if self.guard.on_closing() is not False:self.events.closed.set()
class CloseTests(unittest.TestCase):
 def create(self,timeout=1):
  w=FakeWindow();remember=[];g=CloseCoordinator(w,lambda:remember.append('saved'),timeout);w.guard=g;return w,g,remember
 def test_close_returns_immediately_and_repeated_clicks_do_not_duplicate_flush(self):
  w,g,remember=self.create()
  self.assertIs(g.on_closing(),False);self.assertTrue(w.requested.wait(1));self.assertIs(g.on_closing(),False)
  self.assertEqual(w.destroyed,0);self.assertEqual(remember,[])
  w.callback({'ready':True});self.assertTrue(w.events.closed.wait(1));self.assertEqual(remember,['saved']);self.assertEqual(w.destroyed,1)
 def test_timeout_keeps_window_open_and_late_callback_cannot_close_it(self):
  w,g,remember=self.create(.02);g.on_closing();self.assertTrue(w.requested.wait(1));self.assertTrue(w.resumed.wait(1))
  w.callback({'ready':True});self.assertFalse(w.events.closed.is_set());self.assertEqual(w.destroyed,0);self.assertEqual(remember,[])
 def test_failed_save_reenables_window_and_retry_can_close(self):
  w,g,remember=self.create();g.on_closing();self.assertTrue(w.requested.wait(1));w.callback({'ready':False,'error':'Disk full'});self.assertTrue(w.resumed.wait(1));self.assertFalse(w.events.closed.is_set())
  w.requested.clear();self.assertIs(g.on_closing(),False);self.assertTrue(w.requested.wait(1));w.callback({'ready':True});self.assertTrue(w.events.closed.wait(1));self.assertEqual(remember,['saved'])
 def test_unloaded_window_can_close_without_a_javascript_queue(self):
  w,g,remember=self.create();w.events.loaded.clear();self.assertIsNone(g.on_closing());self.assertEqual(remember,['saved']);self.assertFalse(w.requested.is_set())
 def test_geometry_save_failure_cancels_close(self):
  w=FakeWindow();w.events.loaded.clear()
  def broken():raise OSError('Read-only preference folder')
  g=CloseCoordinator(w,broken);w.guard=g
  self.assertIs(g.on_closing(),False);self.assertTrue(w.resumed.wait(1));self.assertFalse(w.events.closed.is_set())
