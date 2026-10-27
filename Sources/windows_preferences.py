"""Validated review-only view/window preferences, independent of HTTP origin."""
import json,threading
from pathlib import Path
def validate(value):
 if not isinstance(value,dict):return {}
 out={k:v for k,v in value.items() if k in ('compact','top') and type(v) is bool}
 if value.get('theme') in ('dark','light'):out['theme']=value['theme']
 if value.get('measurement') in ('reflected','input','current','voltage','frequency','bypass_swr'):out['measurement']=value['measurement']
 if isinstance(value.get('callsign'),str):out['callsign']=value['callsign'].strip().upper()[:24]
 if isinstance(value.get('sections'),dict):out['sections']={k:v for k,v in value['sections'].items() if k in ('status','amplifier','faults','cooling','connection') and type(v) is bool}
 for key,count in [('full_size',2),('position',2)]:
  data=value.get(key)
  if isinstance(data,list) and len(data)==count and all(type(n) is int for n in data):
   if key=='full_size' and 360<=data[0]<=4000 and 440<=data[1]<=4000:out[key]=data
   elif key=='position' and all(abs(n)<=100000 for n in data):out[key]=data
 return out
class Preferences:
 def __init__(self,path):
  self.path=Path(path);self.lock=threading.RLock()
  try:self.value=validate(json.loads(self.path.read_text(encoding='utf-8')))
  except (OSError,ValueError):self.value={}
 def snapshot(self):
  with self.lock:return json.loads(json.dumps(self.value))
 def save(self,value):
  with self.lock:
   self.value.update(validate(value));self.path.parent.mkdir(parents=True,exist_ok=True)
   tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(self.value),encoding='utf-8');tmp.replace(self.path)
