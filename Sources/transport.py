"""Byte transport boundary: USB and TCP share the same paced command/reply contract."""
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


def tcp_endpoint(host,port):
 import ipaddress
 if not isinstance(host,str):raise ValueError('Enter the amplifier IP address.')
 try:host=str(ipaddress.ip_address(host.strip()))
 except ValueError:raise ValueError('Enter a valid amplifier IPv4 or IPv6 address.') from None
 if type(port) is not int or not 1<=port<=65535:raise ValueError('Enter a TCP port from 1 to 65535.')
 return host,port

class TCPTransport:
 """One bounded TCP stream; same command framing and guards as USB."""
 def __init__(self,host,port):
  import socket,fcntl,hashlib
  from pathlib import Path
  host,port=tcp_endpoint(host,port);self.sock=None;self.lease=None
  folder=Path.home()/'Library/Application Support/com.grmi64.StationInstruments/port-locks'
  folder.mkdir(parents=True,exist_ok=True,mode=0o700)
  key=hashlib.sha256(('tcp:'+host+':'+str(port)).encode()).hexdigest()
  try:
   self.lease=os.open(str(folder/(key+'.lock')),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
   try:fcntl.flock(self.lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
   except BlockingIOError:raise OSError('This amplifier TCP endpoint is already in use by another controller.') from None
   self.sock=socket.create_connection((host,port),timeout=2)
   self.sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1);self.sock.setblocking(False)
  except BaseException:self.close();raise
 def write(self,data):
  if self.sock is None:raise OSError('TCP connection is closed.')
  deadline=time.monotonic()+.5
  while data:
   remaining=deadline-time.monotonic()
   if remaining<=0:raise TimeoutError('TCP write timed out.')
   if select.select([], [self.sock], [], min(.05,remaining))[1]:
    try:
     sent=self.sock.send(data)
     if not sent:raise OSError('TCP connection closed.')
     data=data[sent:]
    except BlockingIOError:pass
 def read(self,timeout):
  if self.sock is None:raise OSError('TCP connection is closed.')
  if select.select([self.sock],[],[],timeout)[0]:
   try:data=self.sock.recv(4096)
   except BlockingIOError:return b''
   if not data:raise OSError('TCP connection closed. Reconnect when ready.')
   return data
  return b''
 def close(self):
  if self.sock is not None:self.sock.close();self.sock=None
  if self.lease is not None:os.close(self.lease);self.lease=None
