"""Cancel native close once, flush JS preferences off the UI thread, then retry."""
import json,logging,threading

class CloseCoordinator:
 def __init__(self,window,remember,timeout=8):
  self._window=window;self._remember=remember;self._timeout=timeout
  self._lock=threading.Lock();self._pending=False;self._allowed=False
 def on_closing(self):
  with self._lock:
   if self._allowed or not self._window.events.loaded.is_set():
    try:self._remember()
    except Exception as exc:
     self._allowed=False
     threading.Thread(target=self._resume,args=(str(exc),),daemon=True).start()
     return False
    return None
   if self._pending:return False
   self._pending=True
  # Never wait here: pywebview runs this callback on the WinForms UI thread,
  # which the pending display/save calls and JS evaluation still need.
  threading.Thread(target=self._flush,daemon=True).start()
  return False
 def _flush(self):
  completed=threading.Event();result=[]
  def done(value):result.append(value);completed.set()
  try:
   self._window.evaluate_js('beginNativeClose()',done)
   if not completed.wait(self._timeout):raise RuntimeError('Saving preferences timed out. The app remains open; try closing again.')
   if not result or not isinstance(result[0],dict) or result[0].get('ready') is not True:
    raise RuntimeError((result[0].get('error') if result and isinstance(result[0],dict) else None) or 'Preferences could not be saved. The app remains open.')
   with self._lock:self._allowed=True
   if not self._window.events.closed.is_set():self._window.destroy()
  except Exception as exc:
   if not self._window.events.closed.is_set():self._resume(str(exc))
 def _resume(self,message):
  with self._lock:self._pending=False;self._allowed=False
  try:
   self._window.evaluate_js('if (typeof cancelNativeClose === "function") cancelNativeClose('+json.dumps(message)+')')
  except Exception:logging.exception('Could not show preference-close failure')
