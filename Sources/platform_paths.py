"""Platform paths and passive port naming. Never opens a serial device."""
import glob,os,re,sys
from pathlib import Path
WINDOWS=sys.platform=='win32'
def data_directory():
 if WINDOWS:return Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData/Local'))/'KPA1500 Control'
 return Path.home()/'Library/Application Support/com.grmi64.KPA1500Control'
def lock_directory():
 if WINDOWS:return Path(os.environ.get('LOCALAPPDATA',Path.home()/'AppData/Local'))/'Station Instruments/port-locks'
 return Path.home()/'Library/Application Support/com.grmi64.StationInstruments/port-locks'
def serial_port(value):
 if not isinstance(value,str):raise ValueError('Select the amplifier Host PC USB port.')
 if WINDOWS:
  if not re.fullmatch(r'COM[1-9][0-9]{0,4}',value,re.IGNORECASE):raise ValueError('Choose a COM port from the passive USB port list.')
  return value.upper()
 if not value.startswith('/dev/cu.') or '/' in value[8:]:raise ValueError('Choose a /dev/cu. USB port.')
 return value
def ports():
 if WINDOWS:
  try:from serial.tools import list_ports
  except ImportError:raise OSError('USB support requires the bundled pyserial runtime.') from None
  result=[]
  for item in list_ports.comports():
   try:result.append(serial_port(item.device))
   except ValueError:pass
  return sorted(set(result),key=lambda s:int(s[3:]))
 return sorted(set(glob.glob('/dev/cu.usbserial*')+glob.glob('/dev/cu.usbmodem*')))
