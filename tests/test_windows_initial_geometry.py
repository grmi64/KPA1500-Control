"""Initial monitor placement preserves logical size; no native APIs/hardware."""
import pathlib,sys,types,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from windows_app import restore_window_geometry,normal_window_size

def rect(x,y,w,h):return types.SimpleNamespace(X=x,Y=y,Width=w,Height=h)
def size(w,h):return types.SimpleNamespace(Width=w,Height=h)
def point(x,y):return types.SimpleNamespace(X=x,Y=y)
class Form:
 WindowState=0
 def __init__(self,primary_only=False):
  self.primary_only=primary_only;self.dpi=120;self.Bounds=rect(104,96,450,550);self.Handle=types.SimpleNamespace(ToInt64=lambda:123)
 @property
 def Location(self):return point(self.Bounds.X,self.Bounds.Y)
 @Location.setter
 def Location(self,value):
  self.Bounds=rect(value.X,value.Y,self.Bounds.Width,self.Bounds.Height)
  self.dpi=120 if self.primary_only or value.X<1920 else 96
class InitialGeometryTests(unittest.TestCase):
 def context(self,form):
  def screen(r):
   area=rect(1920,0,2560,1440) if not form.primary_only and r.X>=1920 else rect(0,0,1920,1152)
   return types.SimpleNamespace(WorkingArea=area)
  modules={'System.Drawing':types.SimpleNamespace(Point=point,Rectangle=rect,Size=size),'System.Windows.Forms':types.SimpleNamespace(Screen=types.SimpleNamespace(FromRectangle=screen,FromControl=lambda f:screen(f.Bounds)),FormWindowState=types.SimpleNamespace(Normal=0,Minimized=1,Maximized=2))}
  return patch.dict('sys.modules',modules),patch('windows_app.window_dpi',side_effect=lambda h:form.dpi)
 def test_move_125_to_100_applies_saved_logical_size_at_destination(self):
  f=Form();w=types.SimpleNamespace(native=f);modules,dpi=self.context(f)
  with modules,dpi:
   restore_window_geometry(w,(1020,850),(2451,168))
   self.assertEqual((f.Bounds.X,f.Bounds.Y,f.Bounds.Width,f.Bounds.Height),(2451,168,1020,850))
   self.assertEqual(normal_window_size(w),(1020,850));self.assertEqual((f.MinimumSize.Width,f.MinimumSize.Height),(360,440))
 def test_move_100_to_125_scales_using_actual_destination_dpi(self):
  f=Form();f.Location=point(2451,168);w=types.SimpleNamespace(native=f);modules,dpi=self.context(f)
  with modules,dpi:
   restore_window_geometry(w,(1020,850),(104,40))
   self.assertEqual((f.Bounds.Width,f.Bounds.Height),(1275,1062));self.assertEqual(normal_window_size(w),(1020,850));self.assertEqual((f.MinimumSize.Width,f.MinimumSize.Height),(450,550))
 def test_five_reopens_on_secondary_do_not_grow_saved_full_dimensions(self):
  saved=(1020,850)
  for _ in range(5):
   f=Form();w=types.SimpleNamespace(native=f);modules,dpi=self.context(f)
   with modules,dpi:
    restore_window_geometry(w,saved,(2451,168));saved=normal_window_size(w)
   self.assertEqual(saved,(1020,850))
 def test_missing_secondary_clamps_position_and_keeps_size_on_primary(self):
  f=Form(primary_only=True);w=types.SimpleNamespace(native=f);modules,dpi=self.context(f)
  with modules,dpi:
   self.assertEqual(restore_window_geometry(w,(1020,850),(2451,168)),(645,90,1275,1062))
   self.assertEqual(normal_window_size(w),(1020,850))
 def test_no_saved_position_preserves_initial_monitor_and_visible_size(self):
  f=Form();w=types.SimpleNamespace(native=f);modules,dpi=self.context(f)
  with modules,dpi:
   restore_window_geometry(w,(800,600))
   self.assertEqual((f.Bounds.X,f.Bounds.Y,f.Bounds.Width,f.Bounds.Height),(104,96,1000,750));self.assertEqual(normal_window_size(w),(800,600))
 def test_oversized_saved_dimensions_fit_inside_destination_work_area(self):
  f=Form();w=types.SimpleNamespace(native=f);modules,dpi=self.context(f)
  with modules,dpi:
   self.assertEqual(restore_window_geometry(w,(4000,4000),(2451,168)),(1920,0,2560,1440))
   self.assertEqual(normal_window_size(w),(2560,1440))
if __name__=='__main__':unittest.main()
