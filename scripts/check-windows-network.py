"""Exercise local interface enumeration inside the packaged GUI executable."""
import argparse,json,subprocess,tempfile
from pathlib import Path

def check(exe,output):
 exe=Path(exe).resolve();output=Path(output).resolve()
 if not exe.is_file():raise RuntimeError('Packaged executable is missing.')
 if output.exists():raise RuntimeError('Use a fresh network self-test output path.')
 result=subprocess.run([str(exe),'--network-self-test',str(output)],stdin=subprocess.DEVNULL,capture_output=True,timeout=45)
 report=json.loads(output.read_text(encoding='utf-8')) if output.exists() else {}
 if result.returncode or report.get('status')!='passed' or report.get('frozen') is not True or report.get('hardware_probes')!=0 or report.get('renderer_ready') is not True:
  raise RuntimeError('Frozen network self-test failed; inspect '+str(output))
 print('Frozen network configuration check passed; targets='+str(report['target_count'])+'; no addresses probed. Evidence: '+str(output))
 return report

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--exe',type=Path,required=True);parser.add_argument('--output',type=Path);args=parser.parse_args()
 if args.output:check(args.exe,args.output)
 else:
  with tempfile.TemporaryDirectory(prefix='kpa-frozen-network-') as directory:check(args.exe,Path(directory)/'result.json')
