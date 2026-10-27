"""Inspect Windows PE metadata/icon resources without executing the application."""
import argparse,sys,struct
from pathlib import Path
import pefile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Sources'))
from windows_identity import PRODUCT_NAME,REVIEW_NAME,DEVELOPER,COPYRIGHT,numeric_version
from version import VERSION

def check(package,name):
 if name not in (PRODUCT_NAME,REVIEW_NAME):raise ValueError('Unknown build identity')
 exe=package/(name+'.exe');pe=pefile.PE(str(exe))
 try:
  info=pe.VS_FIXEDFILEINFO[0]
  actual=(info.FileVersionMS>>16,info.FileVersionMS&65535,info.FileVersionLS>>16,info.FileVersionLS&65535)
  if actual!=numeric_version():raise RuntimeError('Incorrect numeric EXE version')
  product=(info.ProductVersionMS>>16,info.ProductVersionMS&65535,info.ProductVersionLS>>16,info.ProductVersionLS&65535)
  if product!=numeric_version():raise RuntimeError('Incorrect numeric product version')
  if not info.FileFlags&2:raise RuntimeError('Development candidate must retain prerelease flag')
  strings={}
  for group in pe.FileInfo:
   for item in group:
    if item.Key==b'StringFileInfo':
     for table in item.StringTable:strings.update({k.decode('utf-8'):v.decode('utf-8') for k,v in table.entries.items()})
  expected={'CompanyName':DEVELOPER,'FileDescription':name,'FileVersion':'.'.join(map(str,numeric_version())),'LegalCopyright':COPYRIGHT,'OriginalFilename':name+'.exe','ProductName':PRODUCT_NAME,'ProductVersion':VERSION}
  for key,value in expected.items():
   if strings.get(key)!=value:raise RuntimeError('Incorrect EXE identity field: '+key)
  resources={entry.id for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries}
  if not {3,14}.issubset(resources):raise RuntimeError('Application icon resources missing')
  icon=(Path(__file__).resolve().parents[1]/'Assets/AppIcon.ico').read_bytes()
  reserved,kind,count=struct.unpack_from('<HHH',icon)
  if reserved!=0 or kind!=1 or count==0:raise RuntimeError('Invalid source icon')
  expected_icons=set()
  for index in range(count):
   entry=struct.unpack_from('<BBBBHHII',icon,6+16*index);length,offset=entry[-2:];expected_icons.add(icon[offset:offset+length])
  actual_icons=set()
  for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
   if entry.id==3:
    for image in entry.directory.entries:
     for language in image.directory.entries:
      data=language.data.struct;actual_icons.add(pe.get_data(data.OffsetToData,data.Size))
  if not expected_icons.issubset(actual_icons):raise RuntimeError('Embedded icons do not match project artwork')
 finally:pe.close()
 print('Windows identity audit passed: '+name+'; file version '+'.'.join(map(str,numeric_version()))+'; project icon frames verified; prerelease candidate.')
 return strings
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--package',type=Path,required=True);parser.add_argument('--name',required=True);args=parser.parse_args();check(args.package,args.name)
