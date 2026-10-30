"""Native GIL regression: no amplifier, serial ports or network access."""
import sys,threading,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Sources'))

@unittest.skipUnless(sys.platform=='win32','Native WinForms requires Windows')
class ManagedSizingTests(unittest.TestCase):
 def test_native_sizing_can_complete_a_callback_on_another_python_thread(self):
  import clr
  clr.AddReference('System.Windows.Forms');clr.AddReference('System.Drawing');clr.AddReference('Microsoft.CSharp')
  from Microsoft.CSharp import CSharpCodeProvider
  from System.CodeDom.Compiler import CompilerParameters
  from System import Action
  from System.Drawing import Size
  from System.Windows.Forms import Form
  from windows_forms import managed_sizing_form
  source='''using System; using System.Threading; using System.Windows.Forms;
namespace KPAFormsRegression { public class GatedForm : Form {
 public Action Callback;
 protected override void SetBoundsCore(int x,int y,int width,int height,BoundsSpecified specified) {
  if(Callback!=null){Thread t=new Thread(()=>Callback());t.IsBackground=true;t.Start();
   if(!t.Join(1500))throw new TimeoutException("Native setter retained Python GIL");}
  base.SetBoundsCore(x,y,width,height,specified);
 }
}}'''
  provider=CSharpCodeProvider();options=CompilerParameters();options.GenerateInMemory=True
  for reference in ('System.dll','System.Windows.Forms.dll','System.Drawing.dll'):options.ReferencedAssemblies.Add(reference)
  compiled=provider.CompileAssemblyFromSource(options,source)
  self.assertFalse(compiled.Errors.HasErrors,str(compiled.Errors))
  from KPAFormsRegression import GatedForm
  wrapped=managed_sizing_form(GatedForm,Form)
  for mode,type_ in (('negative_control',GatedForm),('managed',wrapped)):
   with self.subTest(mode=mode):
    form=type_();completed=threading.Event();form.Callback=Action(completed.set)
    try:
     if mode=='negative_control':
      with self.assertRaisesRegex(Exception,'Native setter retained Python GIL'):form.Size=Size(361,441)
     else:
      form.Size=Size(361,441);self.assertTrue(completed.is_set());self.assertEqual(form.Size.Width,361)
    finally:form.Callback=None;form.Dispose()

if __name__=='__main__':unittest.main()
