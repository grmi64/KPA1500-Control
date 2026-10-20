"""Byte transport boundary: USB today; a TCP transport can implement this contract later."""
import os,select,termios,time
from port_lock import PortLock,exclusive
BAUDS=(4800,9600,19200,38400,57600,115200,230400)
class SerialTransport:
 def __init__(self,port,baud):
  if not isinstance(port,str) or not port.startswith('/dev/cu.') or '/' in port[8:]:raise ValueError('Choose a /dev/cu. USB port.')
  if baud not in BAUDS:raise ValueError('Unsupported baud rate.')
  self.fd=None;self.old=None;self.guard=PortLock(port)
  try:
   self.guard.acquire();self.fd=os.open(port,os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK);exclusive(self.fd);self.guard.check_owners()
   self.old=termios.tcgetattr(self.fd);a=termios.tcgetattr(self.fd);a[0]=a[1]=a[3]=0;a[2]=termios.CS8|termios.CREAD|termios.CLOCAL
   a[4]=a[5]=getattr(termios,'B'+str(baud));a[6][termios.VMIN]=0;a[6][termios.VTIME]=0
   termios.tcsetattr(self.fd,termios.TCSANOW,a);termios.tcflush(self.fd,termios.TCIFLUSH)
  except BaseException:self.close();raise
 def write(self,data):
  deadline=time.monotonic()+.5
  while data:
   if time.monotonic()>=deadline:raise TimeoutError('USB write timed out.')
   if select.select([], [self.fd], [], .05)[1]:
    try:data=data[os.write(self.fd,data):]
    except BlockingIOError:pass
 def read(self,timeout):
  if select.select([self.fd],[],[],timeout)[0]:
   data=os.read(self.fd,4096)
   if not data:raise OSError('USB connection closed.')
   return data
  return b''
 def close(self):
  if self.fd is not None:
   try:
    if self.old is not None:termios.tcsetattr(self.fd,termios.TCSANOW,self.old)
   except OSError:pass
   finally:os.close(self.fd);self.fd=None
  self.guard.release()
