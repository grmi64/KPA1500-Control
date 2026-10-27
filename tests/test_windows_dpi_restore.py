import ctypes,sys,types,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Sources'))
from windows_app import WindowDpiSizing,keep_visible,normal_window_size
from windows_dpi import DpiWindowHook,WM_DPICHANGED,_Rect

class MinimizedDpiRestoreTests(unittest.TestCase):
 def setUp(self):
  self.rect=lambda x,y,w,h:types.SimpleNamespace(X=x,Y=y,Width=w,Height=h)
  self.form=types.SimpleNamespace(WindowState=1,RestoreBounds=self.rect(0,0,1920,1200),Bounds=self.rect(-32000,-32000,199,34),Handle=Mock())
  self.form.Handle.ToInt64.return_value=456;self.window=types.SimpleNamespace(native=self.form)
  area=self.rect(0,0,1920,1200)
  screen=types.SimpleNamespace(FromRectangle=lambda r:types.SimpleNamespace(WorkingArea=area),FromControl=lambda f:types.SimpleNamespace(WorkingArea=area))
  modules={'System.Drawing':types.SimpleNamespace(Rectangle=self.rect,Size=lambda w,h:(w,h)),'System.Windows.Forms':types.SimpleNamespace(Screen=screen,FormWindowState=types.SimpleNamespace(Normal=0,Minimized=1,Maximized=2))}
  item=patch.dict('sys.modules',modules);item.start();self.addCleanup(item.stop)
  with patch('windows_app.window_dpi',return_value=192):self.sizing=WindowDpiSizing(self.window)
 def test_clamped_full_ignores_unscaled_windows_suggestion(self):
  self.assertEqual(self.sizing.prepare((-13,-13,1946,1226),120),(-13,-13,1200,750))
 def test_nonclamped_full_and_compact_restore_sizes(self):
  for width,height in ((1400,1000),(820,1080)):
   self.sizing.dpi=192;self.form.RestoreBounds=self.rect(0,0,width,height)
   self.assertEqual(self.sizing.prepare((20,30,width,height),120),(20,30,round(width*120/192),round(height*120/192)))
 def test_normal_and_maximized_keep_suggestion(self):
  for state in (0,2):
   self.form.WindowState=state;self.sizing.dpi=192
   self.assertEqual(self.sizing.prepare((20,30,1205,760),120),(20,30,1205,760));self.assertEqual(self.sizing.dpi,120)
 def test_deferred_restore_applies_once_and_close_keeps_logical_size(self):
  corrected=self.sizing.prepare((-13,-13,1946,1226),120)
  with patch('windows_app.window_dpi',return_value=120):
   keep_visible(self.window,corrected);self.assertEqual(normal_window_size(self.window),(960,600))
   self.form.WindowState=0;self.form.Bounds=self.rect(0,0,1920,1200);keep_visible(self.window)
   self.assertEqual((self.form.Bounds.Width,self.form.Bounds.Height),(1200,750));self.assertIsNone(self.window._pending_dpi_bounds)
   self.form.Bounds=self.rect(10,10,1100,700);keep_visible(self.window);self.assertEqual(self.form.Bounds.Width,1100)
 def test_repeated_minimized_changes_scale_pending_bounds(self):
  with patch('windows_app.window_dpi',return_value=120):keep_visible(self.window,self.sizing.prepare((0,0,1946,1226),120))
  self.assertEqual(self.sizing.prepare((0,0,1920,1200),144),(0,0,1440,900))
 def test_scale_increase_is_fitted_to_work_area_after_restore(self):
  self.sizing.dpi=120;self.form.RestoreBounds=self.rect(0,0,1600,1000)
  corrected=self.sizing.prepare((0,0,1600,1000),192)
  self.assertEqual(corrected,(0,0,2560,1600));self.form.WindowState=0
  with patch('windows_app.window_dpi',return_value=192):keep_visible(self.window,corrected)
  self.assertEqual((self.form.Bounds.Width,self.form.Bounds.Height),(1920,1200))
 def test_native_prepare_precedes_default_and_corrected_application(self):
  api=Mock();api.SetWindowSubclass.return_value=1;events=[]
  api.DefSubclassProc.side_effect=lambda *args:events.append('default') or 123
  def prepare(bounds,dpi):events.append(('prepare',dpi));return (1,2,1200,750)
  with patch('windows_dpi._comctl32',return_value=api),patch('windows_dpi._callback',side_effect=lambda fn:fn):
   hook=DpiWindowHook(456,lambda bounds:events.append(('apply',bounds)),prepare=prepare)
   rect=_Rect(-13,-13,1933,1213);hook._message(456,WM_DPICHANGED,120|(120<<16),ctypes.addressof(rect),hook.identity,0)
  self.assertEqual(events,[('prepare',120),'default',('apply',(1,2,1200,750))])
 def test_restored_state_before_dpi_still_uses_captured_minimized_bounds(self):
  self.sizing.minimized();self.form.WindowState=0;self.form.RestoreBounds=self.rect(0,0,1912,1176)
  self.assertEqual(self.sizing.prepare((0,0,1912,1176),120),(0,0,1200,750))
 def test_deferred_native_restore_cannot_overwrite_corrected_size(self):
  queued=[];self.form.BeginInvoke=queued.append;self.form.IsDisposed=False
  with patch.dict('sys.modules',{'System':types.SimpleNamespace(Action=lambda fn:fn)}),patch('windows_app.window_dpi',return_value=120),patch('windows_app.set_window_bounds') as native:
   self.sizing.minimized();target=self.sizing.prepare((-13,-13,1946,1226),120);self.form.WindowState=0
   self.sizing.changed(target)
   self.form.Bounds=self.rect(0,0,1920,1200) # SetWindowPlacement unwinds after WM_DPICHANGED
   queued.pop()();self.assertEqual((self.form.Bounds.Width,self.form.Bounds.Height),(1200,750));native.assert_called_once_with(456,(0,0,1200,750))
 def test_later_view_change_invalidates_deferred_correction(self):
  queued=[];self.form.BeginInvoke=queued.append;self.form.IsDisposed=False
  with patch.dict('sys.modules',{'System':types.SimpleNamespace(Action=lambda fn:fn)}),patch('windows_app.window_dpi',return_value=120):
   target=self.sizing.prepare((0,0,1946,1226),120);self.form.WindowState=0;self.sizing.changed(target)
   self.sizing.discard_restore();self.form.Bounds=self.rect(0,0,512,675);queued.pop()()
   self.assertEqual((self.form.Bounds.Width,self.form.Bounds.Height),(512,675))

 def test_native_bounds_application_uses_physical_pixels_without_activation(self):
  from windows_dpi import set_window_bounds
  api=Mock();api.SetWindowPos.return_value=1
  with patch('windows_dpi._user32',return_value=api):set_window_bounds(456,(-900,20,1200,750))
  api.SetWindowPos.assert_called_once_with(456,None,-900,20,1200,750,0x0014)
  api.SetWindowPos.return_value=0
  with patch('windows_dpi._user32',return_value=api):
   with self.assertRaises(RuntimeError):set_window_bounds(456,(0,0,1200,750))
 def test_user_resize_discards_saved_minimized_dimensions(self):
  self.sizing.minimized();self.sizing.discard_restore();self.form.WindowState=0
  self.assertEqual(self.sizing.prepare((10,20,875,625),120),(10,20,875,625))

 def test_deferred_native_failure_is_logged_without_escaping_ui_callback(self):
  queued=[];self.form.BeginInvoke=queued.append;self.form.IsDisposed=False
  with patch.dict('sys.modules',{'System':types.SimpleNamespace(Action=lambda fn:fn)}),patch('windows_app.window_dpi',return_value=120),patch('windows_app.set_window_bounds',side_effect=RuntimeError('Native bounds rejected')):
   target=self.sizing.prepare((0,0,1946,1226),120);self.form.WindowState=0;self.sizing.changed(target)
   with self.assertLogs(level='ERROR'):queued.pop()()
  self.assertEqual(self.sizing.last_error,'Native bounds rejected')
