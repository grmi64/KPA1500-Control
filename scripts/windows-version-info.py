"""Generate a PyInstaller Windows version resource without running an EXE."""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Sources'))
from windows_identity import version_resource

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--name',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 text=version_resource(args.name);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text,encoding='utf-8')
 print(args.output)
if __name__=='__main__':main()
