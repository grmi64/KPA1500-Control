"""Per-user cooperative lock plus macOS kernel serial-port exclusivity."""
import hashlib,os,subprocess
from platform_paths import WINDOWS
from endpoint_lock import EndpointLock
if not WINDOWS:import fcntl,termios
from pathlib import Path

class PortLock:
    def __init__(self,port):self.port=port;self.fd=None;self.windows_lease=None
    def acquire(self):
        if WINDOWS:
            self.windows_lease=EndpointLock("serial:"+self.port.upper());self.windows_lease.acquire();return
        key=os.path.realpath(self.port).replace('/dev/tty.','/dev/cu.')
        folder=Path.home()/'Library/Application Support/com.grmi64.StationInstruments/port-locks'
        folder.mkdir(parents=True,exist_ok=True,mode=0o700)
        path=folder/(hashlib.sha256(key.encode()).hexdigest()+'.lock')
        fd=os.open(str(path),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise OSError('Amplifier USB port is already in use by another amplifier controller. Quit the other reader first.') from None
            self.check_owners()
            os.ftruncate(fd,0);os.write(fd,str(os.getpid()).encode());self.fd=fd
        except BaseException:os.close(fd);raise
    def check_owners(self):
        if WINDOWS:return # CreateFile with share mode 0 enforces actual serial ownership.
        check=subprocess.run(['/usr/sbin/lsof','-t',self.port],capture_output=True,text=True,timeout=3)
        if check.returncode not in (0,1):raise OSError('Could not check amplifier USB ownership. No connection opened.')
        owners={p for p in check.stdout.split() if p!=str(os.getpid())}
        if owners:raise OSError('Amplifier USB port is already open in another process (PID '+', '.join(sorted(owners))+'). Quit the other amplifier controller first.')
    def release(self):
        if self.windows_lease:self.windows_lease.release();self.windows_lease=None
        if self.fd is not None:os.close(self.fd);self.fd=None

def exclusive(fd):
    # Prevent subsequent opens even by older programs that ignore our file lock.
    fcntl.ioctl(fd,termios.TIOCEXCL)
