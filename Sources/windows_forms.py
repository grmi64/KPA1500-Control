"""Keep the Python GIL available during native WinForms sizing callbacks."""

def managed_sizing_form(base,form):
 import clr
 properties={name:clr.GetClrType(form).GetProperty(name) for name in ('Size','MinimumSize','ClientSize','Location','Bounds')}
 def managed_property(name):
  info=properties[name]
  # A CLR property descriptor holds the GIL while invoking its setter. Native
  # sizing can reenter accessibility/COM and need another Python thread. Calling
  # PropertyInfo's managed methods releases the GIL around the native operation.
  return property(lambda self:info.GetValue(self,None),lambda self,value:info.SetValue(self,value,None))
 class ManagedSizingForm(base):
  Size=managed_property('Size')
  MinimumSize=managed_property('MinimumSize')
  ClientSize=managed_property('ClientSize')
  Location=managed_property('Location')
  Bounds=managed_property('Bounds')
 return ManagedSizingForm

def install():
 from webview.platforms import winforms
 from System.Windows.Forms import Form
 if getattr(winforms.BrowserView,'_managed_sizing_installed',False):return
 winforms.BrowserView.BrowserForm=managed_sizing_form(winforms.BrowserView.BrowserForm,Form)
 winforms.BrowserView._managed_sizing_installed=True
