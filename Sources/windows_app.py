"""Windows host with explicit Simulation, Read-only and Hardware control launch modes."""
import argparse,json,logging,multiprocessing,os,secrets,sys,threading,time
from pathlib import Path
from http.server import ThreadingHTTPServer
from engine import Controller
from server import handler_for
from platform_paths import data_directory,settings_path
from windows_instance import Instance
from windows_close import CloseCoordinator
from windows_preferences import Preferences
from version import VERSION,BUILD
from windows_dpi import configure_process_dpi,window_dpi,DpiWindowHook,set_window_bounds
from windows_runtime import ensure_webview2_runtime
from windows_launch import MODES,LaunchWorkflow,mode_settings,launch_replacement
from transport import tcp_endpoint,BAUDS
from platform_paths import serial_port

def fit_bounds(bounds,area):
 x,y,w,h=bounds;l,t,aw,ah=area;w=min(max(1,w),aw);h=min(max(1,h),ah)
 return max(l,min(x,l+aw-w)),max(t,min(y,t+ah-h)),w,h

class WindowDpiSizing:
 """Correct the unscaled rectangle Windows can suggest while restoring an icon."""
 def __init__(self,window):
  self.window=window;self.dpi=window_dpi(window.native.Handle.ToInt64());self.restore_size=None;self.correction=None;self.generation=0;self.last_error=None
 def minimized(self):
  bounds=self.window.native.RestoreBounds;pending=getattr(self.window,'_pending_dpi_bounds',None)
  width,height=pending[2:] if pending else (bounds.Width,bounds.Height)
  self.restore_size=(width,height,self.dpi)
 def activated(self):
  self.restore_size=None
 def prepare(self,suggested,dpi):
  from System.Windows.Forms import FormWindowState
  previous=self.dpi
  self.generation+=1
  if dpi<=0:return suggested
  self.dpi=dpi
  form=self.window.native
  pending=getattr(self.window,'_pending_dpi_bounds',None)
  if previous!=dpi and (self.restore_size or pending or form.WindowState==FormWindowState.Minimized):
   bounds=form.RestoreBounds
   width,height=pending[2:] if pending else (bounds.Width,bounds.Height)
   if self.restore_size:width,height,previous=self.restore_size
   self.restore_size=None
   self.correction=(suggested[0],suggested[1],round(width*dpi/previous),round(height*dpi/previous))
   return suggested if form.WindowState==FormWindowState.Maximized else self.correction
  return suggested
 def _apply_restore(self,target):
  from System.Windows.Forms import FormWindowState
  form=self.window.native
  if form.WindowState!=FormWindowState.Normal:
   # Preserve normal geometry independently of the maximized display rectangle.
   self.window._pending_dpi_bounds=target;keep_visible(self.window);return
  fitted=keep_visible(self.window,target)
  if fitted:set_window_bounds(form.Handle.ToInt64(),fitted)
 def _finish_later(self,target):
  # SetWindowPlacement may finish with old bounds after the native message.
  from System import Action
  generation=self.generation;dpi=self.dpi
  def finish_restore():
   try:
    form=self.window.native
    if not form.IsDisposed and generation==self.generation and window_dpi(form.Handle.ToInt64())==dpi:self._apply_restore(target)
   except Exception as exc:
    self.last_error=str(exc);logging.exception('Deferred DPI restore failed')
  self.window.native.BeginInvoke(Action(finish_restore))
 def changed(self,suggested):
  target=self.correction;self.correction=None
  if target:
   from System.Windows.Forms import FormWindowState
   if self.window.native.WindowState==FormWindowState.Maximized:
    self.window._pending_dpi_bounds=target;keep_visible(self.window)
   else:keep_visible(self.window,target)
   self._finish_later(target)
  else:keep_visible(self.window,suggested)
 def restored(self):
  from System.Windows.Forms import FormWindowState
  target=getattr(self.window,'_pending_dpi_bounds',None)
  if target and self.window.native.WindowState==FormWindowState.Normal:
   keep_visible(self.window,target);self._finish_later(target)
 def discard_restore(self):
  self.activated();self.correction=None;self.generation+=1;self.window._pending_dpi_bounds=None

def keep_visible(window,suggested=None):
 from System.Drawing import Rectangle,Size
 from System.Windows.Forms import Screen,FormWindowState
 form=window.native
 if form.WindowState==FormWindowState.Minimized and suggested:
  window._pending_dpi_bounds=suggested
 if form.WindowState==FormWindowState.Normal:
  suggested=suggested or getattr(window,'_pending_dpi_bounds',None)
  window._pending_dpi_bounds=None
 area=(Screen.FromRectangle(Rectangle(*suggested)) if suggested else Screen.FromControl(form)).WorkingArea
 scale=window_dpi(form.Handle.ToInt64())/96
 form.MinimumSize=Size(min(round(360*scale),area.Width),min(round(440*scale),area.Height))
 if form.WindowState!=FormWindowState.Normal:return
 b=form.Bounds;bounds=(b.X,b.Y,b.Width,b.Height);fitted=fit_bounds(suggested or bounds,(area.X,area.Y,area.Width,area.Height))
 if fitted!=bounds:form.Bounds=Rectangle(*fitted)
 return fitted

def restore_window_geometry(window,full_size,position=None):
 """Restore logical Full dimensions using the destination monitor's actual DPI."""
 from System.Drawing import Point
 form=window.native
 if position:form.Location=Point(*position)
 scale=window_dpi(form.Handle.ToInt64())/96
 bounds=form.Bounds
 return keep_visible(window,(bounds.X,bounds.Y,round(full_size[0]*scale),round(full_size[1]*scale)))

def normal_window_size(window):
 """Return the normal outer size in logical pixels, even while maximized."""
 from System.Windows.Forms import FormWindowState
 form=window.native
 # pywebview floors its logical size getters; round native physical bounds
 # instead so repeated Full/Compact transitions do not cumulatively shrink.
 pending=getattr(window,'_pending_dpi_bounds',None)
 bounds=form.Bounds if form.WindowState==FormWindowState.Normal else form.RestoreBounds;scale=window_dpi(form.Handle.ToInt64())/96
 if pending:return round(pending[2]/scale),round(pending[3]/scale)
 return round(bounds.Width/scale),round(bounds.Height/scale)

class DisplayBridge:
 def __init__(self,preferences=None):
  self._window=None;self._preferences=preferences;self._compact=False;self._full_size=(1020,850)
 def load_preferences(self):
  return {k:v for k,v in self._preferences.snapshot().items() if k not in ('position','full_size')} if self._preferences else {}
 def save_preferences(self,value):
  if self._preferences:self._preferences.save(value)
 def launch_info(self):return self._launch.info() if hasattr(self,'_launch') else dict(mode='simulation',label='Simulation',allowed=False)
 def request_launch_mode(self,value):return self._launch.request(value)
 def finish_launch_mode(self):
  if self._launch.pending is None:raise ValueError('No confirmed launch mode change is pending.')
  from System import Action
  self._window.native.BeginInvoke(Action(self._window.destroy))
  return {'closing':True}
 def about_info(self):return dict(name='KPA1500 Control',version=VERSION,build=BUILD,developer='Greg Miller \u00b7 NY6C',mode=self.launch_info()['label'])
 def show_about(self):
  from System import Action
  from System.Windows.Forms import MessageBox
  self._window.native.BeginInvoke(Action(lambda:MessageBox.Show(self._window.native,f'KPA1500 Control {VERSION} (build {BUILD})\nGreg Miller · NY6C\n{self.launch_info()["label"]}','About KPA1500 Control')))
 def display_window(self,options):
  if not isinstance(options,dict) or any(type(options.get(k)) is not bool for k in ('compact','alwaysOnTop')):raise ValueError('Invalid window preferences')
  from System import Action
  value=dict(options)
  self._window.native.BeginInvoke(Action(lambda:self._apply_display(value)))
 def _apply_display(self,options):
  # Runs on the UI thread. Capture normal restore bounds before leaving a
  # maximized/minimized state, so monitor-sized dimensions cannot replace them.
  from System.Windows.Forms import FormWindowState
  small=options['compact'];w=self._window
  if small!=self._compact:
   if small:self._full_size=normal_window_size(w)
   w.native.WindowState=FormWindowState.Normal
   w._pending_dpi_bounds=None
   if hasattr(w,'_dpi_sizing'):w._dpi_sizing.discard_restore()
   w.resize(*((410,540) if small else self._full_size));self._compact=small
  w.on_top=options['alwaysOnTop'];keep_visible(w)

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__)
 modes=parser.add_mutually_exclusive_group();modes.add_argument('--demo',action='store_true');modes.add_argument('--read-only',action='store_true');modes.add_argument('--hardware',action='store_true')
 parser.add_argument('--mode-handoff',action='store_true',help=argparse.SUPPRESS)
 parser.add_argument('--settings',type=Path,default=data_directory()/'Windows/simulation.json');parser.add_argument('--http-port',type=int,default=0)
 parser.add_argument('--connection-type',choices=('usb','tcp'));parser.add_argument('--usb-port');parser.add_argument('--baud',type=int,default=230400);parser.add_argument('--host');parser.add_argument('--tcp-port',type=int,default=1500)
 parser.add_argument('--smoke-test',action='store_true');parser.add_argument('--smoke-reopen',action='store_true');parser.add_argument('--smoke-close-test',action='store_true');args=parser.parse_args(argv)
 mode='read-only' if args.read_only else 'hardware' if args.hardware else 'simulation'
 if (args.smoke_test or args.smoke_reopen or args.smoke_close_test) and mode!='simulation':parser.error('Smoke tests must remain offline in Simulation.')
 if args.smoke_reopen and not args.smoke_test:parser.error('Reopen smoke requires --smoke-test')
 if (args.connection_type or args.usb_port or args.host) and mode=='simulation':parser.error('Hardware endpoints require an explicit Read-only or Hardware control mode.')
 endpoint=None
 if args.connection_type:
  if args.baud not in BAUDS:parser.error('Unsupported baud rate')
  if args.connection_type=='tcp':
   if args.usb_port:parser.error('USB port cannot be combined with TCP/IP')
   host,port=tcp_endpoint(args.host,args.tcp_port);endpoint=dict(mode='tcp',host=host,tcp_port=port,baud=args.baud)
  else:
   if args.host:parser.error('TCP/IP host cannot be combined with USB')
   endpoint=dict(mode='usb',port=serial_port(args.usb_port) if args.usb_port else '',baud=args.baud)
 elif args.usb_port or args.host:parser.error('Select the endpoint connection type')
 base_settings=settings_path(args.settings);args.settings=mode_settings(base_settings,mode)
 if sys.platform!='win32':parser.error('Windows is required')
 if args.smoke_close_test and not args.smoke_test:parser.error('Close regression requires --smoke-test')
 if args.smoke_test and args.http_port!=0:parser.error('Smoke tests require --http-port 0 and a new --settings file')
 if args.smoke_test and args.settings.exists():parser.error('Smoke tests require a new settings file')
 if args.smoke_test:
  import faulthandler
  args.settings.parent.mkdir(parents=True,exist_ok=True);trace=args.settings.with_suffix('.trace.log').open('w');faulthandler.dump_traceback_later(30,file=trace)
 configure_process_dpi()
 instance=Instance(args.settings)
 if not instance.acquire(activate_existing=not (args.mode_handoff or endpoint is not None)):return 0
 preferences=Preferences(args.settings.with_suffix('.window.json'))
 activation=threading.Event();bridge=None
 def activate():
  activation.set()
  if bridge and bridge._window:
   from System import Action
   from System.Windows.Forms import FormWindowState
   def focus():
    form=bridge._window.native
    if form.WindowState==FormWindowState.Minimized:form.WindowState=FormWindowState.Normal
    keep_visible(bridge._window);form.Show();form.Activate();form.BringToFront()
   bridge._window.native.BeginInvoke(Action(focus))
 controller=None;server=None;thread=None;failures=[];display_callback=None
 try:
  import webview
  ensure_webview2_runtime(Path(webview.__file__).parent)
  controller=Controller(args.settings,offline_only=mode=='simulation',read_only=mode=='read-only',manual_connect=True)
  if endpoint:controller.save_settings(dict(endpoint,auto_connect=False,share_readings=False))
  token=secrets.token_urlsafe(24)
  server=ThreadingHTTPServer(('127.0.0.1',args.http_port),handler_for(controller,token,activate=activate,simulate_discovery=mode=='simulation'));server.daemon_threads=True
  thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.1},daemon=True);thread.start()
  if mode=='simulation':controller.connect({'mode':'simulator'})
  bridge=DisplayBridge(preferences);bridge._launch=LaunchWorkflow(controller,server.RequestHandlerClass.discovery,base_settings,mode,restricted=args.smoke_test);url=f'http://127.0.0.1:{server.server_port}/{token}/'
  webview.settings.update(ALLOW_FILE_URLS=False,ALLOW_DOWNLOADS=False,OPEN_EXTERNAL_LINKS_IN_BROWSER=False,OPEN_DEVTOOLS_IN_DEBUG=False)
  # Construct a small native shell before moving it between DPI domains.
  # Apply the saved logical Full size only after the destination DPI is known.
  window=webview.create_window('KPA1500 Control · '+MODES[mode],url,js_api=bridge,width=360,height=440,min_size=(360,440),background_color='#111619',text_select=True);bridge._window=window
  def setup():
   nonlocal display_callback
   from System import Action
   from Microsoft.Win32 import SystemEvents
   form=window.native
   position=preferences.snapshot().get('position')
   def changed(sender,event):
    if not form.IsDisposed:form.BeginInvoke(Action(lambda:keep_visible(window)))
   display_callback=changed;SystemEvents.DisplaySettingsChanged+=display_callback
   def activated(sender,event):
    keep_visible(window);window._dpi_sizing.activated()
   form.Activated+=activated
   form.ResizeEnd+=lambda sender,event:window._dpi_sizing.discard_restore()
   bridge._full_size=tuple(preferences.snapshot().get('full_size',[1020,850]))
   def navigating(sender,event):
    if str(event.Uri)!=url:event.Cancel=True
   window.native.webview.NavigationStarting+=navigating
   window._dpi_sizing=WindowDpiSizing(window)
   window._dpi_hook=DpiWindowHook(window.native.Handle.ToInt64(),window._dpi_sizing.changed,prepare=window._dpi_sizing.prepare,minimized=window._dpi_sizing.minimized,restored=window._dpi_sizing.restored)
   restore_window_geometry(window,bridge._full_size,position)
  window.events.before_show+=setup
  def remember():
   from System.Windows.Forms import FormWindowState
   form=window.native
   bounds=form.Bounds if form.WindowState==FormWindowState.Normal else form.RestoreBounds
   value={'position':[bounds.X,bounds.Y],'full_size':list(bridge._full_size if bridge._compact else normal_window_size(window))}
   preferences.save(value)
  close_coordinator=CloseCoordinator(window,remember)
  window.events.closing+=close_coordinator.on_closing
  instance.publish(url,token)
  close_save_release=None
  def smoke():
   nonlocal close_save_release
   if not args.smoke_test:return
   try:
    if not window.events.loaded.wait(25):raise RuntimeError('Review UI did not load')
    def wait_js(expression):
     deadline=time.monotonic()+12
     while not window.evaluate_js(expression):
      if time.monotonic()>deadline:raise RuntimeError('UI check timed out: '+expression)
      time.sleep(.1)
    wait_js("snapshot?.state?.status === 'live'")
    wait_js("snapshot?.state?.demo === true")
    wait_js("!document.getElementById('top').disabled")
    wait_js("!document.getElementById('launchPanel').hidden && document.getElementById('accessNotice').textContent.includes('Simulation') && document.getElementById('applyLaunchMode').disabled")
    wait_js("getComputedStyle(document.getElementById('accessNotice')).display !== 'none'")
    if args.smoke_reopen:
     wait_js("prefs.theme === 'light' && prefs.measurement === 'frequency' && prefs.callsign === 'REVIEW' && prefs.sections.faults === false")
    window.evaluate_js("prefs.compact=false;prefs.theme='dark';applyView();document.getElementById('view').click();document.getElementById('theme').click()")
    wait_js("document.body.classList.contains('compact') && document.documentElement.dataset.theme === 'light'")
    window.evaluate_js("document.getElementById('top').checked=true;document.getElementById('top').onchange()")
    wait_js("prefs.top === true")
    window.evaluate_js("document.getElementById('top').checked=false;document.getElementById('top').onchange();document.getElementById('view').click()")
    wait_js("getComputedStyle(document.getElementById('accessNotice')).display !== 'none'")
    from System import Action
    from System.Windows.Forms import FormWindowState
    def ui(call):
     done=threading.Event();result=[];errors=[]
     def run():
      try:result.append(call())
      except Exception as exc:errors.append(exc)
      finally:done.set()
     window.native.BeginInvoke(Action(run))
     if not done.wait(5):raise RuntimeError('UI dispatch did not complete')
     if errors:raise errors[0]
     return result[0] if result else None
    # Drain the queued view changes before measuring the normal Full window.
    def drain_native_updates():
     drained=threading.Event()
     window.evaluate_js("nativeUpdates.then(()=>true)",lambda result:drained.set())
     if not drained.wait(5):raise RuntimeError("Native preference queue did not drain")
     ui(lambda:None)
    drain_native_updates()
    original_size=ui(lambda:normal_window_size(window))
    ui(lambda:setattr(window.native,'WindowState',FormWindowState.Maximized))
    ui(lambda:bridge._apply_display({'compact':True,'alwaysOnTop':False}))
    if ui(lambda:window.native.WindowState)!=FormWindowState.Normal:raise RuntimeError('Compact retained a maximized state')
    if any(abs(a-b)>1 for a,b in zip(bridge._full_size,original_size)):raise RuntimeError(f'Normal Full size changed: {original_size} -> {bridge._full_size}')
    ui(lambda:bridge._apply_display({'compact':False,'alwaysOnTop':False}))
    if any(abs(a-b)>1 for a,b in zip(ui(lambda:normal_window_size(window)),original_size)):raise RuntimeError('Full size did not restore')
    import serial
    if serial.VERSION!='3.5':raise RuntimeError('Pinned serial runtime missing')
    # Test activation IPC without launching another window or reader.
    import subprocess
    original_worker=controller.worker.pid
    launch=[sys.executable]+([] if getattr(sys,'frozen',False) else [str(Path(__file__).resolve())])+['--demo','--http-port','0','--settings',str(args.settings)]
    second=subprocess.run(launch,timeout=12,check=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if controller.worker.pid!=original_worker:raise RuntimeError('Second launch changed the reader')
    if not activation.is_set():raise RuntimeError('Second launch did not request activation')
    if bridge.about_info()['version']!=VERSION:raise RuntimeError('About version mismatch')
    window.evaluate_js("document.getElementById('disconnect').click()")
    wait_js("snapshot.state.status === 'disconnected' && !document.getElementById('demoBanner').hidden && document.getElementById('connectionStatus').textContent === 'SIMULATOR'")
    window.evaluate_js("document.getElementById('discover').click()")
    wait_js("!document.getElementById('discoveryProgress').hidden")
    window.evaluate_js("document.getElementById('cancelDiscovery').click()")
    wait_js("document.getElementById('discoveryStatus').textContent.includes('cancelled')")
    window.evaluate_js("document.getElementById('discover').click()")
    wait_js("document.getElementById('discoveryResults').options.length === 2")
    window.evaluate_js("document.getElementById('discoveryResults').value='0';document.getElementById('discoveryResults').onchange()")
    wait_js("document.getElementById('connectionType').value === 'simulator' && snapshot.state.status === 'disconnected'")
    window.evaluate_js("document.getElementById('connect').click()")
    wait_js("snapshot.state.status === 'live'")
    def action(name):
     result=controller.action({'action':name,'generation':controller.generation,'confirm_power_off':name=='power_off'})
     deadline=time.monotonic()+6
     while time.monotonic()<deadline:
      found=next((a for a in controller.snapshot()['actions'] if a['id']==result['id']),None)
      if found and found['status']!='queued':
       if found['status']!='confirmed':raise RuntimeError(str(found))
       return
      time.sleep(.05)
     raise RuntimeError('Simulated action did not finish: '+name)
    # Kill only the offline simulator reader: the state API and Disconnect must
    # remain usable even when Windows reports a broken completion pipe.
    failed_worker=controller.worker;failed_worker.terminate();failed_worker.join(3)
    if failed_worker.is_alive():raise RuntimeError('Simulator reader did not exit')
    wait_js("snapshot.state.status === 'error' && snapshot.reader_present === true && !document.getElementById('disconnect').disabled && document.getElementById('forward').textContent === '\u2014'")
    window.evaluate_js("document.getElementById('disconnect').click()")
    wait_js("snapshot.state.status === 'disconnected' && snapshot.reader_present === false && !busy && !document.getElementById('connect').disabled")
    if controller.worker is not None:raise RuntimeError('Failed simulator ownership was not released')
    window.evaluate_js("document.getElementById('connect').click()")
    wait_js("snapshot.state.status === 'live'")
    # Exercise stale/error presentation without any hardware transport.
    controller.disconnect();controller.clear('stale','Simulated telemetry loss.')
    wait_js("snapshot.state.status === 'stale' && !document.getElementById('demoBanner').hidden && document.getElementById('operate').disabled && document.getElementById('forward').textContent === '—'")
    controller.clear('error','Simulated disconnection.')
    wait_js("snapshot.state.status === 'error' && !document.getElementById('demoBanner').hidden && document.getElementById('actionMessage').textContent.includes('Simulated disconnection')")
    controller.connect({'mode':'simulator'})
    wait_js("snapshot.state.status === 'live'")
    for name in ('operate','fan_5','fan_0','tune','cancel_tune','demo_tx_on','demo_tx_off','standby','power_off','power_on'):action(name)
    window.evaluate_js("prefs.theme='light';prefs.measurement='frequency';prefs.callsign='REVIEW';prefs.sections.faults=false;applyView()")
    drain_native_updates()
    deadline=time.monotonic()+3
    while preferences.snapshot().get('measurement')!='frequency':
     if time.monotonic()>deadline:raise RuntimeError('Native preferences were not saved')
     time.sleep(.05)
    if args.smoke_close_test:
     # The ordinary close path must flush this queue itself, unlike the other
     # smoke checks which deliberately drain before making assertions.
     window.evaluate_js("prefs.theme='dark';applyView()")
     drain_native_updates()
     started=threading.Event();close_save_release=threading.Event();original_save=bridge.save_preferences;delayed_once=[False]
     def delayed_save(value):
      if not delayed_once[0]:
       delayed_once[0]=True;started.set()
       if not close_save_release.wait(5):raise RuntimeError('Close test did not release the first save')
      return original_save(value)
     bridge.save_preferences=delayed_save
     window.evaluate_js("prefs.theme='dark';applyView();prefs.theme='light';applyView()")
     if not started.wait(3):raise RuntimeError('Close test save was not in flight')
    report={'status':'passed' ,'offline_only':controller.offline_only,'sharing':controller.config['share_readings'],'auto_connect':controller.config['auto_connect'],'final_state':controller.snapshot()['state']['status'],'checks':['real WebView2 rendering','Full/Compact','Light/Dark','stay-on-top bridge','simulated mode/fan/tune/cancel/RF/power controls','return to Standby','instance activation IPC','About/version','fake discovery progress/cancel/select','native preferences persistence','pinned serial runtime import','stale/error rendering and disabled controls','maximized Compact/Full restore','persistent simulation labels','serialized preference saves','explicit Simulation launch notice and restricted mode selector','abrupt simulator reader exit, responsive state API, explicit Disconnect and manual recovery']}
    args.settings.parent.mkdir(parents=True,exist_ok=True);args.settings.with_suffix('.smoke.json').write_text(json.dumps(report,indent=2))
   except Exception as exc:
    import traceback
    detail={'error':str(exc),'traceback':traceback.format_exc()}
    try:detail['ui']=window.evaluate_js("({snapshot,busy,connectionType:document.getElementById('connectionType').value,message:document.getElementById('actionMessage').textContent})")
    except Exception:pass
    args.settings.with_suffix('.failure.json').write_text(json.dumps(detail,indent=2),encoding='utf-8');failures.append(str(exc))
   finally:
    window.destroy()
    if close_save_release is not None:close_save_release.set()
  webview.start(smoke,gui='edgechromium',private_mode=args.smoke_test,storage_path=str(args.settings.parent/'WebView2'))
  if failures:raise RuntimeError('; '.join(failures))
  if args.smoke_close_test:
   persisted=json.loads(args.settings.with_suffix('.window.json').read_text(encoding='utf-8'))
   if persisted.get('theme')!='light':raise RuntimeError('Closing lost the latest queued preference')
   path=args.settings.with_suffix('.smoke.json');report=json.loads(path.read_text(encoding='utf-8'));report['checks'].append('close during an in-flight preference save retains latest choice');path.write_text(json.dumps(report,indent=2),encoding='utf-8')
 finally:
  if server:
   discovery=server.RequestHandlerClass.discovery;discovery.stop()
   if discovery.thread:discovery.thread.join(5)
  if display_callback is not None:
   from Microsoft.Win32 import SystemEvents
   SystemEvents.DisplaySettingsChanged-=display_callback
  if controller:controller.disconnect()
  if server:server.shutdown();server.server_close()
  if thread:thread.join(3)
  instance.close()
 if args.smoke_test:
  faulthandler.cancel_dump_traceback_later();trace.close()
 return bridge._launch.pending if bridge is not None and bridge._launch.pending is not None else 0

if __name__=='__main__':
 multiprocessing.freeze_support()
 try:
  result=main()
  if isinstance(result,list):launch_replacement(result);result=0
  sys.exit(result)
 except Exception as exc:
  import ctypes
  if sys.stderr:print(str(exc),file=sys.stderr)
  if not '--smoke-test' in sys.argv:ctypes.windll.user32.MessageBoxW(None,str(exc),'KPA1500 Control',0x10)
  sys.exit(1)
