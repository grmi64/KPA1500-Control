"""Cross-process endpoint lease, released by OS process/handle teardown."""
import hashlib,os
from platform_paths import WINDOWS,lock_directory
class EndpointLock:
 def __init__(self,key):self.key=key;self.fd=None
 def acquire(self):
  folder=lock_directory();folder.mkdir(parents=True,exist_ok=True,mode=0o700)
  path=folder/(hashlib.sha256(self.key.encode()).hexdigest()+'.lock')
  fd=os.open(str(path),os.O_CREAT|os.O_RDWR|getattr(os,'O_NOFOLLOW',0),0o600)
  try:
   if WINDOWS:
    import msvcrt
    if os.fstat(fd).st_size==0:os.write(fd,b'0')
    os.lseek(fd,0,os.SEEK_SET);msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
   else:
    import fcntl
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BaseException:
   os.close(fd);raise OSError('This amplifier endpoint is already in use or its lease cannot be acquired.') from None
  self.fd=fd
 def release(self):
  if self.fd is not None:os.close(self.fd);self.fd=None
