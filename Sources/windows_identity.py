"""Offline Windows executable identity; shared Mac version remains authoritative."""
import re
from version import VERSION,BUILD
PRODUCT_NAME='KPA1500 Control'
REVIEW_NAME=PRODUCT_NAME+' Review'
DEVELOPER='Greg Miller (NY6C)'
INTERNAL_NAME='KPA1500Control'
COPYRIGHT='Copyright (c) 2026 '+DEVELOPER

def numeric_version(version=VERSION,build=BUILD):
 if not isinstance(version,str) or not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Version must have three numeric components.')
 if not isinstance(build,str) or not re.fullmatch(r'\d+',build):raise ValueError('Build must be numeric.')
 parts=tuple(map(int,version.split('.')+[build]))
 if any(n>65535 for n in parts):raise ValueError('Windows version components must fit 16 bits.')
 return parts

def version_resource(name):
 if name not in (PRODUCT_NAME,REVIEW_NAME):raise ValueError('Unknown Windows build identity.')
 version=numeric_version();version_text='.'.join(map(str,version))
 strings={'CompanyName':DEVELOPER,'FileDescription':name,'FileVersion':version_text,'InternalName':INTERNAL_NAME+('Review' if name==REVIEW_NAME else ''),'LegalCopyright':COPYRIGHT,'OriginalFilename':name+'.exe','ProductName':PRODUCT_NAME,'ProductVersion':VERSION,'Comments':'Development candidate; not a published release.'}
 table=',\n'.join('    StringStruct('+repr(k)+', '+repr(v)+')' for k,v in strings.items())
 return ("# Generated from Sources/version.py; local candidate, not Store identity.\n"
  +f"VSVersionInfo(ffi=FixedFileInfo(filevers={version!r}, prodvers={version!r}, mask=0x3f, flags=0x2, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)), kids=[\n"
  +" StringFileInfo([StringTable('040904B0', [\n"+table+"\n ])]),\n VarFileInfo([VarStruct('Translation', [1033, 1200])])\n])\n")
