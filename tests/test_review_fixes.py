import pathlib,queue,sys,tempfile,types,unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from engine import Controller
from windows_app import DisplayBridge,normal_window_size

class WindowRestoreTests(unittest.TestCase):
 def window(self,state):
  form=types.SimpleNamespace(WindowState=state,RestoreBounds=types.SimpleNamespace(Width=1250,Height=1000),Handle=Mock())
  class Window:
   native=form;width=1920;height=1080
   def resize(self,w,h):
    self_test.assertEqual(form.WindowState,0,'Window must be Normal before resize')
    self.width=w;self.height=h
  self_test=self
  return Window()
 def modules(self):return {'System.Windows.Forms':types.SimpleNamespace(FormWindowState=types.SimpleNamespace(Normal=0,Minimized=1,Maximized=2))}
 def test_maximized_and_minimized_compact_preserve_normal_full_size(self):
  for state in (1,2):
   with self.subTest(state=state),patch.dict(sys.modules,self.modules()),patch('windows_app.window_dpi',return_value=120),patch('windows_app.keep_visible'):
    window=self.window(state);bridge=DisplayBridge();bridge._window=window
    bridge._apply_display({'compact':True,'alwaysOnTop':True})
    self.assertEqual(bridge._full_size,(1000,800));self.assertEqual((window.width,window.height),(410,540));self.assertEqual(window.native.WindowState,0)
    bridge._apply_display({'compact':False,'alwaysOnTop':False})
    self.assertEqual((window.width,window.height),(1000,800));self.assertEqual(window.native.WindowState,0)
 def test_normal_full_size_uses_native_rounding_instead_of_floored_getters(self):
  with patch.dict(sys.modules,self.modules()),patch('windows_app.window_dpi',return_value=120),patch('windows_app.keep_visible'):
   window=self.window(0);window.native.Bounds=types.SimpleNamespace(Width=1125,Height=938);window.width=899;window.height=749;bridge=DisplayBridge();bridge._window=window
   bridge._apply_display({'compact':True,'alwaysOnTop':False});bridge._apply_display({'compact':False,'alwaysOnTop':False})
   self.assertEqual((window.width,window.height),(900,750))
 def test_normal_size_for_close_uses_restore_bounds_when_maximized(self):
  with patch.dict(sys.modules,self.modules()),patch('windows_app.window_dpi',return_value=120):self.assertEqual(normal_window_size(self.window(2)),(1000,800))

class OfflineLabelTests(unittest.TestCase):
 def test_clear_preserves_permanent_offline_marker_for_every_nonlive_state(self):
  with tempfile.TemporaryDirectory() as directory:
   c=Controller(pathlib.Path(directory)/'review.json',offline_only=True)
   for status in ('disconnected','connecting','stale','error'):
    c.clear(status,'Synthetic state');snap=c.snapshot()
    self.assertTrue(snap['offline_only']);self.assertTrue(snap['state']['demo']);self.assertEqual(snap['state']['status'],status)
    self.assertIsNone(snap['state']['forward_watts'])
   with self.assertRaises(ValueError):c.connect({'mode':'tcp','host':'192.0.2.10'})
   self.assertIsNone(c.worker)
 def test_worker_error_cannot_clear_offline_label(self):
  with tempfile.TemporaryDirectory() as directory:
   c=Controller(pathlib.Path(directory)/'review.json',offline_only=True);c.events=queue.Queue();c.events.put(('error','Synthetic worker error'))
   snap=c.snapshot();self.assertEqual(snap['state']['status'],'error');self.assertTrue(snap['state']['demo']);c.events=None
 def test_normal_hardware_session_is_not_mislabeled(self):
  with tempfile.TemporaryDirectory() as directory:
   c=Controller(pathlib.Path(directory)/'normal.json');self.assertFalse(c.snapshot()['offline_only']);self.assertFalse(c.snapshot()['state']['demo'])
