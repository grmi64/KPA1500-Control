"""Single review instance per settings identity; token-protected loopback activation."""
import hashlib,http.client,json,time
from urllib.parse import urlsplit
from endpoint_lock import EndpointLock
from platform_paths import WINDOWS,settings_path
class Instance:
 def __init__(self,settings):
  settings=settings_path(settings);self.legacy_path=settings.with_suffix('.instance.json')
  key='KPA1500-Windows-review:'+str(settings).casefold()
  if WINDOWS:
   from windows_lease import activation_directory
   self.path=activation_directory()/(hashlib.sha256(key.encode()).hexdigest()+'.json')
  else:self.path=self.legacy_path
  self.lease=EndpointLock(key);self.owner=False
 def acquire(self,activate_existing=True):
  try:self.lease.acquire();self.owner=True;return True
  except OSError:
   if not activate_existing:raise RuntimeError('A KPA1500 window for the selected mode is already open. Close that window and retry the mode change. Its connection was not activated or changed.') from None
   # The first process may still be preparing its WebView2 runtime. The
   # shared rendezvous bypasses MSIX settings-file virtualization. A legacy
   # sidecar can still activate an older owner when its file lease is busy.
   last_error=None
   for _ in range(20):
    for path in dict.fromkeys((self.path,self.legacy_path)):
     try:
      value=json.loads(path.read_text(encoding='utf-8'));url=value['url'];parts=urlsplit(url);token=value['token']
      if not isinstance(token,str) or not token or parts.scheme!='http' or parts.hostname!='127.0.0.1' or parts.path!='/'+token+'/' or not parts.port:raise ValueError('Invalid activation endpoint')
      connection=http.client.HTTPConnection('127.0.0.1',parts.port,timeout=.3)
      try:
       connection.request('POST',parts.path+'activate',body=b'{}',headers={'X-Amp-Token':token,'Content-Type':'application/json'})
       reply=connection.getresponse()
       if reply.status==200 and json.loads(reply.read(4096)).get('activated') is True:return False
      finally:connection.close()
     except (OSError,ValueError,KeyError,http.client.HTTPException) as exc:last_error=exc
    time.sleep(.1)
   raise RuntimeError('Another KPA1500 review instance is starting or unavailable. Use or close that window before retrying. '+str(last_error)) from last_error
 def publish(self,url,token):
  if not self.owner:raise RuntimeError('Only the instance owner may publish activation metadata.')
  value=json.dumps(dict(url=url,token=token))
  for path in dict.fromkeys((self.path,self.legacy_path)):
   path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(value,encoding='utf-8');tmp.replace(path)
 def close(self):
  if self.owner:
   try:
    for path in dict.fromkeys((self.path,self.legacy_path)):path.unlink(missing_ok=True)
   finally:
    self.lease.release();self.owner=False
