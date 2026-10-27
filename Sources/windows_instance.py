"""Single review instance per settings identity; token-protected loopback activation."""
import http.client,json,time
from pathlib import Path
from urllib.parse import urlsplit
from endpoint_lock import EndpointLock
class Instance:
 def __init__(self,settings):
  self.path=Path(settings).resolve().with_suffix('.instance.json');self.lease=EndpointLock('KPA1500-Windows-review:'+str(Path(settings).resolve()).casefold());self.owner=False
 def acquire(self):
  try:self.lease.acquire();self.owner=True;return True
  except OSError:
   # The first process may still be preparing its WebView2 runtime.
   last_error=None
   for _ in range(20):
    try:
     value=json.loads(self.path.read_text(encoding='utf-8'));url=value['url'];parts=urlsplit(url);token=value['token']
     if parts.scheme!='http' or parts.hostname!='127.0.0.1' or parts.path!='/'+token+'/' or not parts.port:raise ValueError('Invalid activation endpoint')
     connection=http.client.HTTPConnection('127.0.0.1',parts.port,timeout=.3)
     try:
      connection.request('POST',parts.path+'activate',body=b'{}',headers={'X-Amp-Token':token,'Content-Type':'application/json'})
      reply=connection.getresponse()
      if reply.status==200 and json.loads(reply.read(4096)).get('activated') is True:return False
     finally:connection.close()
    except (OSError,ValueError,KeyError,http.client.HTTPException) as exc:last_error=exc;time.sleep(.1)
   raise RuntimeError('Another KPA1500 review instance is starting or unavailable. Use or close that window before retrying. '+str(last_error)) from last_error
 def publish(self,url,token):
  self.path.parent.mkdir(parents=True,exist_ok=True);tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(dict(url=url,token=token)),encoding='utf-8');tmp.replace(self.path)
 def close(self):
  if self.owner:
   self.path.unlink(missing_ok=True);self.lease.release();self.owner=False
