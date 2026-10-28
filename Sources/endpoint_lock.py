"""Cross-process endpoint lease, released by OS process/handle teardown."""
import hashlib,os
from platform_paths import WINDOWS,lock_directory
class EndpointLock:
 def __init__(self,key):self.key=key;self.fd=None;self.windows_lease=None
 def acquire(self):
  if self.fd is not None or self.windows_lease is not None:raise OSError('This amplifier endpoint is already in use.')
  if WINDOWS:
   from windows_lease import WindowsLease
   lease=WindowsLease(self.key);lease.acquire();self.windows_lease=lease
  fd=None
  try:
   # Retain the old byte lock for cooperation with older portable versions.
   # On Windows it is supplemental: MSIX can virtualize this file, whereas
   # the per-user named lease above is shared across both package contexts.
   folder=lock_directory();folder.mkdir(parents=True,exist_ok=True,mode=0o700)
   path=folder/(hashlib.sha256(self.key.encode()).hexdigest()+'.lock')
   fd=os.open(str(path),os.O_CREAT|os.O_RDWR|getattr(os,'O_NOFOLLOW',0),0o600)
   if WINDOWS:
    import msvcrt
    if os.fstat(fd).st_size==0:os.write(fd,b'0')
    os.lseek(fd,0,os.SEEK_SET);msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
   else:
    import fcntl
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BaseException:
   if fd is not None:os.close(fd)
   if self.windows_lease is not None:self.windows_lease.release();self.windows_lease=None
   raise OSError('This amplifier endpoint is already in use or its lease cannot be acquired.') from None
  self.fd=fd
 def release(self):
  try:
   if self.fd is not None:os.close(self.fd);self.fd=None
  finally:
   if self.windows_lease is not None:self.windows_lease.release();self.windows_lease=None
