"""Offline ownership tests: synthetic keys, no serial/network transport opens."""
import ctypes,hashlib,json,os,pathlib,subprocess,sys,tempfile,threading,time,unittest,uuid
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'Sources'))
import endpoint_lock
import windows_lease as win

class LeaseContractTests(unittest.TestCase):
 def test_names_are_stable_per_user_and_key_and_session_independent(self):
  a=win.lease_name('serial:COM10','S-1-5-21-1')
  self.assertEqual(a,win.lease_name('serial:COM10','S-1-5-21-1'))
  self.assertTrue(a.startswith('Global\\StationInstruments.EndpointLease.v1.'))
  self.assertLess(len(a),256)
  self.assertNotEqual(a,win.lease_name('serial:COM10','S-1-5-21-2'))
  self.assertNotEqual(a,win.lease_name('serial:COM11','S-1-5-21-1'))
  self.assertNotIn('COM10',a)
 def test_existing_object_is_closed_and_rejected_without_wait_or_ownership(self):
  with patch.object(win,'user_sid',return_value='test-sid'),patch.object(win,'create_handle',return_value=(2**40,183)),patch.object(win,'close_handle') as close:
   lease=win.WindowsLease('test')
   with self.assertRaisesRegex(OSError,'already in use'):lease.acquire()
   close.assert_called_once_with(2**40);self.assertIsNone(lease.handle)
 def test_access_or_creation_errors_fail_closed(self):
  for handle,error in ((None,5),(None,6),(123,5)):
   with self.subTest(handle=handle,error=error),patch.object(win,'user_sid',return_value='test-sid'),patch.object(win,'create_handle',return_value=(handle,error)),patch.object(win,'close_handle') as close:
    lease=win.WindowsLease('test')
    with self.assertRaises(OSError):lease.acquire()
    self.assertIsNone(lease.handle)
    self.assertEqual(close.call_count,1 if handle else 0)
 def test_double_acquire_rejected_and_release_idempotent(self):
  with patch.object(win,'user_sid',return_value='test-sid'),patch.object(win,'create_handle',return_value=(2**40,0)) as create,patch.object(win,'close_handle') as close:
   lease=win.WindowsLease('test');lease.acquire()
   with self.assertRaises(OSError):lease.acquire()
   create.assert_called_once();lease.release();lease.release();close.assert_called_once_with(2**40)
 def test_sid_failure_does_not_fall_back_to_unscoped_or_file_only_lock(self):
  with patch.object(win,'user_sid',side_effect=OSError('No token')),patch.object(win,'create_handle') as create,patch('endpoint_lock.WINDOWS',True),patch('endpoint_lock.lock_directory') as folder:
   with self.assertRaises(OSError):endpoint_lock.EndpointLock('test').acquire()
   create.assert_not_called();folder.assert_not_called()
 def test_native_lease_is_released_if_legacy_file_setup_fails(self):
  with patch.object(win,'user_sid',return_value='test-sid'),patch.object(win,'create_handle',return_value=(123,0)),patch.object(win,'close_handle') as close,patch('endpoint_lock.WINDOWS',True),patch('endpoint_lock.lock_directory',side_effect=OSError('Cannot create folder')):
   lease=endpoint_lock.EndpointLock('test')
   with self.assertRaises(OSError):lease.acquire()
   self.assertIsNone(lease.fd);self.assertIsNone(lease.windows_lease);close.assert_called_once_with(123)
 def test_failed_close_retains_handle_for_retry(self):
  lease=win.WindowsLease('test');lease.handle=123
  with patch.object(win,'close_handle',side_effect=[OSError('Close failed'),None]) as close:
   with self.assertRaises(OSError):lease.release()
   self.assertEqual(lease.handle,123);lease.release();self.assertIsNone(lease.handle);self.assertEqual(close.call_count,2)

@unittest.skipUnless(sys.platform=='win32','Actual Windows named-object API')
class NativeLeaseTests(unittest.TestCase):
 def setUp(self):self.key='offline-regression:'+uuid.uuid4().hex
 def child(self,code,*args):
  return subprocess.run([sys.executable,'-B','-c',"import sys;sys.path.insert(0,'Sources');"+code,*args],cwd=ROOT,capture_output=True,text=True,timeout=12,creationflags=subprocess.CREATE_NO_WINDOW)
 def test_same_thread_reentry_and_different_keys(self):
  first=win.WindowsLease(self.key);first.acquire();other=win.WindowsLease(self.key+'-other')
  try:
   with self.assertRaises(OSError):win.WindowsLease(self.key).acquire()
   other.acquire()
  finally:other.release();first.release()
  recovered=win.WindowsLease(self.key);recovered.acquire();recovered.release()
 def test_release_can_run_on_another_thread(self):
  first=win.WindowsLease(self.key);first.acquire();errors=[]
  def release():
   try:first.release()
   except Exception as exc:errors.append(exc)
  t=threading.Thread(target=release);t.start();t.join(3);self.assertFalse(t.is_alive());self.assertEqual(errors,[])
  next_lease=win.WindowsLease(self.key);next_lease.acquire();next_lease.release()
 def test_concurrent_release_closes_exactly_once(self):
  first=win.WindowsLease(self.key);first.acquire();errors=[]
  def release():
   try:first.release()
   except Exception as exc:errors.append(exc)
  threads=[threading.Thread(target=release) for _ in range(8)]
  for t in threads:t.start()
  for t in threads:t.join(3)
  self.assertTrue(all(not t.is_alive() for t in threads));self.assertEqual(errors,[])
  next_lease=win.WindowsLease(self.key);next_lease.acquire();next_lease.release()
 def test_cross_process_exclusion_ignores_different_virtualized_storage(self):
  with tempfile.TemporaryDirectory() as folder:
   first=endpoint_lock.EndpointLock(self.key)
   with patch('endpoint_lock.lock_directory',return_value=pathlib.Path(folder)/'private'):
    first.acquire()
   code="from pathlib import Path;import endpoint_lock;endpoint_lock.lock_directory=lambda:Path(sys.argv[2]);lock=endpoint_lock.EndpointLock(sys.argv[1]);\ntry:lock.acquire()\nexcept OSError:sys.exit(3)\nelse:lock.release();sys.exit(0)"
   try:self.assertEqual(self.child(code,self.key,str(pathlib.Path(folder)/'portable')).returncode,3)
   finally:first.release()
   self.assertEqual(self.child(code,self.key,str(pathlib.Path(folder)/'portable')).returncode,0)
 def test_owner_process_death_releases_without_recovery_command(self):
  with tempfile.TemporaryDirectory() as folder:
   ready=pathlib.Path(folder)/'ready'
   code="import sys,pathlib;sys.path.insert(0,'Sources');from windows_lease import WindowsLease;l=WindowsLease(sys.argv[1]);l.acquire();pathlib.Path(sys.argv[2]).write_text('ready');sys.stdin.buffer.read(1)"
   child=subprocess.Popen([sys.executable,'-B','-c',code,self.key,str(ready)],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
   try:
    deadline=time.monotonic()+8
    while not ready.exists() and child.poll() is None and time.monotonic()<deadline:time.sleep(.03)
    self.assertTrue(ready.exists(),'Synthetic owner did not initialize')
    with self.assertRaises(OSError):win.WindowsLease(self.key).acquire()
    child.kill();child.wait(5)
    # Process exit can be signalled just before Windows finishes handle teardown.
    deadline=time.monotonic()+3
    while True:
     recovered=win.WindowsLease(self.key)
     try:recovered.acquire();break
     except OSError:
      if time.monotonic()>=deadline:raise
      time.sleep(.03)
    recovered.release()
   finally:
    if child.poll() is None:child.kill();child.wait(5)
    child.communicate(timeout=3)
 def test_native_handle_is_not_inheritable(self):
  from ctypes import wintypes as w
  lease=win.WindowsLease(self.key);lease.acquire()
  try:
   kernel=ctypes.WinDLL('kernel32',use_last_error=True);kernel.GetHandleInformation.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)];kernel.GetHandleInformation.restype=w.BOOL
   flags=w.DWORD();self.assertTrue(kernel.GetHandleInformation(lease.handle,ctypes.byref(flags)));self.assertEqual(flags.value&1,0)
  finally:lease.release()
 def test_legacy_portable_file_owner_still_blocks_and_rolls_back_native_lease(self):
  import msvcrt
  with tempfile.TemporaryDirectory() as folder,patch('endpoint_lock.lock_directory',return_value=pathlib.Path(folder)):
   path=pathlib.Path(folder)/(hashlib.sha256(self.key.encode()).hexdigest()+'.lock')
   fd=os.open(path,os.O_CREAT|os.O_RDWR,0o600);os.write(fd,b'0');os.lseek(fd,0,0);msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
   try:
    with self.assertRaises(OSError):endpoint_lock.EndpointLock(self.key).acquire()
    # A rejected supplemental file lock must not strand the named lease.
    probe=win.WindowsLease(self.key);probe.acquire();probe.release()
   finally:os.close(fd)
   recovered=endpoint_lock.EndpointLock(self.key);recovered.acquire();recovered.release()



class ActivationRendezvousTests(unittest.TestCase):
 def setUp(self):
  import windows_instance
  self.module=windows_instance;self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name)
  self.patches=[patch.object(windows_instance,'WINDOWS',True),patch.object(win,'activation_directory',return_value=self.root/'shared'),patch('endpoint_lock.lock_directory',return_value=self.root/'locks')]
  for p in self.patches:p.start()
 def tearDown(self):
  for p in reversed(self.patches):p.stop()
  self.temp.cleanup()
 def test_shared_metadata_activates_across_redirected_sidecars(self):
  from engine import Controller
  from server import handler_for
  from http.server import ThreadingHTTPServer
  owner=self.module.Instance(self.root/'settings.json');duplicate=self.module.Instance(self.root/'settings.json')
  owner.legacy_path=self.root/'package-private'/'settings.instance.json';duplicate.legacy_path=self.root/'portable'/'settings.instance.json'
  self.assertEqual(owner.path,duplicate.path);self.assertTrue(owner.acquire())
  activated=threading.Event();c=Controller(self.root/'settings.json',offline_only=True)
  server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(c,'offline-rendezvous',activate=activated.set));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   owner.publish(f'http://127.0.0.1:{server.server_port}/offline-rendezvous/','offline-rendezvous')
   self.assertTrue(owner.path.exists());self.assertTrue(owner.legacy_path.exists());self.assertFalse(duplicate.legacy_path.exists())
   self.assertFalse(duplicate.acquire());self.assertTrue(activated.is_set());self.assertIsNone(c.worker)
   duplicate.close();self.assertTrue(owner.path.exists())
  finally:server.shutdown();server.server_close();thread.join();owner.close()
  self.assertFalse(owner.path.exists());self.assertFalse(owner.legacy_path.exists())
 def test_unavailable_activation_does_not_grant_ownership(self):
  owner=self.module.Instance(self.root/'settings.json');owner.acquire();owner.publish('http://127.0.0.1:1/test/','test')
  try:
   duplicate=self.module.Instance(self.root/'settings.json')
   with patch.object(self.module.time,'sleep'),patch.object(self.module.http.client,'HTTPConnection',side_effect=OSError('Service unavailable')):
    with self.assertRaises(RuntimeError):duplicate.acquire()
   self.assertFalse(duplicate.owner);self.assertIsNone(duplicate.lease.fd)
  finally:owner.close()
 def test_only_owner_can_publish(self):
  duplicate=self.module.Instance(self.root/'settings.json')
  with self.assertRaises(RuntimeError):duplicate.publish('http://127.0.0.1:1/test/','test')
  self.assertFalse(duplicate.path.exists());self.assertFalse(duplicate.legacy_path.exists())
 def test_metadata_cleanup_error_still_releases_ownership(self):
  owner=self.module.Instance(self.root/'settings.json');owner.acquire();owner.publish('http://127.0.0.1:1/test/','test')
  with patch.object(pathlib.Path,'unlink',side_effect=PermissionError('File busy')):
   with self.assertRaises(PermissionError):owner.close()
  self.assertFalse(owner.owner)
  recovered=self.module.Instance(self.root/'settings.json');self.assertTrue(recovered.acquire());recovered.close()
 def test_legacy_sidecar_can_activate_older_owner(self):
  from engine import Controller
  from server import handler_for
  from http.server import ThreadingHTTPServer
  duplicate=self.module.Instance(self.root/'settings.json');activated=threading.Event();c=Controller(self.root/'settings.json',offline_only=True)
  server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(c,'legacy-offline',activate=activated.set));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  duplicate.legacy_path.write_text(json.dumps(dict(url=f'http://127.0.0.1:{server.server_port}/legacy-offline/',token='legacy-offline')))
  try:
   with patch.object(duplicate.lease,'acquire',side_effect=OSError('Legacy owner')):self.assertFalse(duplicate.acquire())
   self.assertTrue(activated.is_set());self.assertFalse(duplicate.owner);self.assertIsNone(c.worker)
  finally:server.shutdown();server.server_close();thread.join()
 def test_non_windows_metadata_path_is_unchanged(self):
  with patch.object(self.module,'WINDOWS',False),patch.object(win,'activation_directory',side_effect=AssertionError('Windows path queried')):
   path=self.root/'mac-review.json';self.assertEqual(self.module.Instance(path).path,path.resolve().with_suffix('.instance.json'))

if __name__=='__main__':unittest.main()
