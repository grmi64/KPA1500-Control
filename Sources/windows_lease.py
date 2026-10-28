"""Per-user Windows lease shared by packaged and unpackaged desktop processes.

The named mutex is used as an *existence* lease, not a thread-owned mutex:
only the creator keeps its handle. Contenders close their handles immediately.
This rejects same-thread reentry, permits release on another thread, and lets
Windows remove the lease when its last owning process/handle exits. No wait or
ReleaseMutex is used. Global scopes sessions; the user SID scopes users.
"""
import ctypes,hashlib,threading
from functools import lru_cache

ERROR_ALREADY_EXISTS=183

def lease_name(key,sid):
 return 'Global\\StationInstruments.EndpointLease.v1.'+hashlib.sha256(sid.encode('utf-8')).hexdigest()+'.'+hashlib.sha256(key.encode('utf-8')).hexdigest()

@lru_cache(maxsize=1)
def user_sid():
 from ctypes import wintypes as w
 kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 advapi=ctypes.WinDLL('advapi32',use_last_error=True)
 kernel.GetCurrentProcess.argtypes=[];kernel.GetCurrentProcess.restype=w.HANDLE
 kernel.CloseHandle.argtypes=[w.HANDLE];kernel.CloseHandle.restype=w.BOOL
 kernel.LocalFree.argtypes=[ctypes.c_void_p];kernel.LocalFree.restype=ctypes.c_void_p
 advapi.OpenProcessToken.argtypes=[w.HANDLE,w.DWORD,ctypes.POINTER(w.HANDLE)];advapi.OpenProcessToken.restype=w.BOOL
 advapi.GetTokenInformation.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD,ctypes.POINTER(w.DWORD)];advapi.GetTokenInformation.restype=w.BOOL
 advapi.ConvertSidToStringSidW.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)];advapi.ConvertSidToStringSidW.restype=w.BOOL
 token=w.HANDLE();text=ctypes.c_void_p()
 if not advapi.OpenProcessToken(kernel.GetCurrentProcess(),0x0008,ctypes.byref(token)):raise ctypes.WinError(ctypes.get_last_error())
 try:
  size=w.DWORD()
  advapi.GetTokenInformation(token,1,None,0,ctypes.byref(size)) # TokenUser
  if not size.value:raise ctypes.WinError(ctypes.get_last_error())
  buffer=ctypes.create_string_buffer(size.value)
  if not advapi.GetTokenInformation(token,1,buffer,size,ctypes.byref(size)):raise ctypes.WinError(ctypes.get_last_error())
  sid=ctypes.cast(buffer,ctypes.POINTER(ctypes.c_void_p))[0]
  if not advapi.ConvertSidToStringSidW(sid,ctypes.byref(text)):raise ctypes.WinError(ctypes.get_last_error())
  return ctypes.wstring_at(text)
 finally:
  if text.value:kernel.LocalFree(text)
  kernel.CloseHandle(token)

def create_handle(name):
 from ctypes import wintypes as w
 kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 kernel.CreateMutexW.argtypes=[ctypes.c_void_p,w.BOOL,w.LPCWSTR];kernel.CreateMutexW.restype=w.HANDLE
 ctypes.set_last_error(0)
 handle=kernel.CreateMutexW(None,False,name) # default non-inheritable handle
 return handle,ctypes.get_last_error()

def close_handle(handle):
 from ctypes import wintypes as w
 kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 kernel.CloseHandle.argtypes=[w.HANDLE];kernel.CloseHandle.restype=w.BOOL
 if not kernel.CloseHandle(handle):raise ctypes.WinError(ctypes.get_last_error())

class WindowsLease:
 def __init__(self,key):self.key=key;self.handle=None;self.guard=threading.Lock()
 def acquire(self):
  with self.guard:self._acquire()
 def _acquire(self):
  if self.handle is not None:raise OSError('This amplifier endpoint is already in use.')
  handle,error=create_handle(lease_name(self.key,user_sid()))
  if not handle:raise OSError('This amplifier endpoint is already in use or its Windows lease cannot be acquired (error '+str(error)+').')
  if error==ERROR_ALREADY_EXISTS:
   close_handle(handle)
   raise OSError('This amplifier endpoint is already in use.')
  if error:
   close_handle(handle)
   raise OSError('The Windows endpoint lease could not be verified (error '+str(error)+').')
  self.handle=handle
 def release(self):
  with self.guard:
   if self.handle is not None:
    close_handle(self.handle);self.handle=None

def activation_directory():
 """Per-user LocalLow rendezvous, outside MSIX Local/Roaming redirection.

Use the OS known-folder path rather than deriving another user's/profile's
path or changing package virtualization settings. Real MSIX/portable tests
must verify that both contexts read this same directory.
 """
 import uuid
 from pathlib import Path
 shell=ctypes.WinDLL('shell32',use_last_error=True)
 ole=ctypes.WinDLL('ole32',use_last_error=True)
 shell.SHGetKnownFolderPath.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)]
 shell.SHGetKnownFolderPath.restype=ctypes.c_long
 ole.CoTaskMemFree.argtypes=[ctypes.c_void_p];ole.CoTaskMemFree.restype=None
 folder_id=(ctypes.c_ubyte*16).from_buffer_copy(uuid.UUID('A520A1A4-1780-4FF6-BD18-167343C5AF16').bytes_le)
 value=ctypes.c_void_p()
 result=shell.SHGetKnownFolderPath(ctypes.byref(folder_id),0,None,ctypes.byref(value))
 try:
  if result or not value.value:raise OSError('Cannot find the Windows activation directory (error '+str(result)+').')
  return Path(ctypes.wstring_at(value))/'Station Instruments'/'instances'
 finally:
  if value.value:ole.CoTaskMemFree(value)
