"""Activation readiness races: fake native host and loopback only; no devices."""
import contextlib,json,pathlib,sys,tempfile,threading,types,unittest,urllib.request
from unittest.mock import Mock,MagicMock,patch
from http.server import ThreadingHTTPServer
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
import engine,windows_app
from server import handler_for

class Event:
 def __init__(self):self.callbacks=[]
 def __iadd__(self,callback):self.callbacks.append(callback);return self
 def __isub__(self,callback):self.callbacks.remove(callback);return self
 def fire(self):
  for callback in list(self.callbacks):callback()

class ActivationTests(unittest.TestCase):
 def test_early_requests_are_coalesced_until_native_ready(self):
  gate=windows_app.ActivationGate();dispatch=Mock()
  for _ in range(20):gate.request()
  dispatch.assert_not_called();gate.ready(dispatch);dispatch.assert_called_once_with()
 def test_ready_without_request_does_not_steal_focus(self):
  gate=windows_app.ActivationGate();dispatch=Mock();gate.ready(dispatch);dispatch.assert_not_called()
  gate.request();dispatch.assert_called_once_with();gate.request();self.assertEqual(dispatch.call_count,2)
 def test_request_during_ready_handoff_is_not_lost(self):
  gate=windows_app.ActivationGate();gate.request();entered=threading.Event();release=threading.Event();calls=[];errors=[]
  def dispatch():
   calls.append('queued')
   if len(calls)==1:
    entered.set()
    if not release.wait(3):raise RuntimeError('Test did not release dispatcher')
  def ready():
   try:gate.ready(dispatch)
   except BaseException as exc:errors.append(exc)
  first=threading.Thread(target=ready);second=threading.Thread(target=gate.request);first.start()
  try:
   self.assertTrue(entered.wait(2));second.start();release.set();first.join(2);second.join(2)
   self.assertFalse(first.is_alive());self.assertFalse(second.is_alive());self.assertEqual(errors,[]);self.assertEqual(calls,['queued','queued'])
  finally:
   release.set();first.join(2)
   if second.ident is not None:second.join(2)
 def test_close_before_ready_discards_pending_and_late_requests(self):
  gate=windows_app.ActivationGate();dispatch=Mock();gate.request();gate.close();gate.ready(dispatch);gate.request();dispatch.assert_not_called()
 def test_close_after_ready_discards_late_requests(self):
  gate=windows_app.ActivationGate();dispatch=Mock();gate.ready(dispatch);gate.request();gate.close();gate.request();dispatch.assert_called_once_with()
 def test_http_accepts_early_requests_without_hardware_or_state_changes(self):
  with tempfile.TemporaryDirectory() as folder:
   c=engine.Controller(pathlib.Path(folder)/'settings.json',offline_only=True,manual_connect=True);gate=windows_app.ActivationGate();dispatch=Mock()
   server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(c,'activation-test',activate=gate.request,simulate_discovery=True));thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.01});thread.start();url=f'http://127.0.0.1:{server.server_port}/activation-test/'
   def activate():
    req=urllib.request.Request(url+'activate',data=b'{}',headers={'Content-Type':'application/json','X-Amp-Token':'activation-test'},method='POST')
    return json.load(urllib.request.urlopen(req,timeout=2))
   try:
    with patch('engine.SerialTransport',side_effect=AssertionError('USB forbidden')),patch('engine.TCPTransport',side_effect=AssertionError('hardware TCP forbidden')):
     for _ in range(5):self.assertEqual(activate(),{'activated':True})
     state=json.load(urllib.request.urlopen(url+'state',timeout=2));self.assertEqual(state['state']['status'],'disconnected');self.assertFalse(state['reader_present']);self.assertEqual(state['actions'],[])
     dispatch.assert_not_called();gate.ready(dispatch);dispatch.assert_called_once_with();self.assertEqual(activate(),{'activated':True});self.assertEqual(dispatch.call_count,2)
   finally:gate.close();server.shutdown();server.server_close();thread.join(2);c.disconnect()
 def test_actual_host_defers_activation_before_native_form_then_restores_once(self):
  with tempfile.TemporaryDirectory() as folder,contextlib.ExitStack() as stack:
   events=types.SimpleNamespace(before_show=Event(),closing=Event(),closed=Event());window=types.SimpleNamespace(native=None,events=events)
   form=MagicMock();form.IsDisposed=False;form.Disposing=False;form.WindowState=0;queued=[];form.BeginInvoke.side_effect=queued.append
   hooks={};server=MagicMock();server.server_port=12345;discovery=Mock();discovery.thread=None
   def handler(controller,token,**kw):hooks.update(kw);return types.SimpleNamespace(discovery=discovery)
   def serve(address,cls):server.RequestHandlerClass=cls;return server
   def start(callback,**kw):
    # Reproduce the real failure: bridge window exists, native form is still None.
    for _ in range(3):hooks['activate']()
    self.assertEqual(queued,[]);window.native=form;events.before_show.fire();self.assertEqual(len(queued),1)
    queued[0]();form.Show.assert_called_once();form.Activate.assert_called_once();form.BringToFront.assert_called_once()
    form.WindowState=1;hooks['activate']();self.assertEqual(len(queued),2);queued[1]();self.assertEqual(form.WindowState,0)
    # Queued UI work and late HTTP requests must not touch a disposed form.
    hooks['activate']();self.assertEqual(len(queued),3);form.IsDisposed=True;events.closed.fire();queued[2]();hooks['activate']();self.assertEqual(len(queued),3);self.assertEqual(form.Show.call_count,2)
   view=types.SimpleNamespace(__file__=str(pathlib.Path(folder)/'webview/__init__.py'),settings={},create_window=Mock(return_value=window),start=start)
   modules={'webview':view,'System':types.SimpleNamespace(Action=lambda fn:fn),'System.Windows.Forms':types.SimpleNamespace(FormWindowState=types.SimpleNamespace(Normal=0,Minimized=1)),'Microsoft.Win32':types.SimpleNamespace(SystemEvents=types.SimpleNamespace(DisplaySettingsChanged=Event()))}
   stack.enter_context(patch.dict('sys.modules',modules));stack.enter_context(patch.object(windows_app.sys,'platform','win32'))
   for name in ['configure_process_dpi','ensure_webview2_runtime','restore_window_geometry','keep_visible','WindowDpiSizing','DpiWindowHook','CloseCoordinator'] :stack.enter_context(patch('windows_app.'+name))
   controller=stack.enter_context(patch('windows_app.Controller')).return_value;controller.connect.side_effect=AssertionError('No hardware startup allowed')
   instance=stack.enter_context(patch('windows_app.Instance')).return_value;instance.acquire.return_value=True
   stack.enter_context(patch('windows_app.handler_for',side_effect=handler));stack.enter_context(patch('windows_app.ThreadingHTTPServer',side_effect=serve));stack.enter_context(patch('windows_app.threading.Thread'))
   self.assertEqual(windows_app.main(['--read-only','--settings',str(pathlib.Path(folder)/'settings.json')]),0)
   controller.connect.assert_not_called();controller.action.assert_not_called();controller.disconnect.assert_called_once();instance.close.assert_called_once();server.shutdown.assert_called_once()

if __name__=='__main__':unittest.main()
