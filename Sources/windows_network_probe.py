"""Local configuration self-test for the actual windowed host; no device probes."""
import json,sys,time,traceback
from pathlib import Path
from windows_network import read_records,targets_from_records

def run(output,renderer_ready=False):
 start=time.monotonic()
 report={'frozen':bool(getattr(sys,'frozen',False)),'executable':sys.executable,'hardware_probes':0,'renderer_ready':renderer_ready}
 try:
  records=read_records()
  if not isinstance(records,(list,dict)):raise ValueError('Invalid local interface data.')
  report.update(status='passed',records=records)
  try:
   targets=targets_from_records(records);report.update(discovery_supported=True,target_count=len(targets))
  except ValueError as error:report.update(discovery_supported=False,reason=str(error),target_count=0)
 except Exception as error:
  report.update(status='failed',exception=type(error).__name__,message=str(error),winerror=getattr(error,'winerror',None),stderr=str(getattr(error,'stderr','')),traceback=traceback.format_exc())
 report['seconds']=round(time.monotonic()-start,3)
 path=Path(output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 return 0 if report['status']=='passed' else 1
