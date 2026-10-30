"""One bounded recovery for an invalid handle in the initial offline simulator."""
import datetime,json,logging,time

def start_simulation(controller,timeout=10):
 if not controller.offline_only:raise ValueError('Initial simulator recovery requires offline-only mode.')
 deadline=time.monotonic()+timeout
 for attempt in (1,2):
  error=None
  try:controller.connect({'mode':'simulator'})
  except OSError as exc:
   if getattr(exc,'winerror',None)!=6:raise
   error=str(exc)
  while error is None:
   snapshot=controller.snapshot();state=snapshot['state']
   if state['status']=='live':return snapshot
   if state['status']=='error':error=state.get('message','');break
   if time.monotonic()>=deadline:return snapshot
   time.sleep(.05)
  if attempt==2 or not error.startswith('[WinError 6]') or time.monotonic()>=deadline:return controller.snapshot()
  # connect() disposes and joins the failed worker before creating fresh IPC.
  # This helper is invoked only by the initial offline Simulation launch. No
  # operating request is queued or replayed; later reader failures stay manual.
  event={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'initial_offline_simulator','attempt':attempt,'error':error,'recovery':'recreate simulator worker once'}
  try:
   path=controller.settings.with_suffix('.startup-events.jsonl');path.parent.mkdir(parents=True,exist_ok=True)
   with path.open('a',encoding='utf-8') as log:log.write(json.dumps(event)+'\n')
  except OSError:logging.exception('Could not record initial simulator recovery')
