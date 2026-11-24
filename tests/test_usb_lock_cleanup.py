import errno
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Sources'))
import transport


@unittest.skipUnless(sys.platform == 'darwin', 'macOS termios cleanup')
class USBLockCleanupTests(unittest.TestCase):
    def test_serial_setup_and_restore_errors_release_discovery_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            port = '/dev/cu.test-amplifier'
            real_open = os.open
            fd = real_open(Path(directory) / 'serial-fixture', os.O_CREAT | os.O_RDWR)
            settings = [0, 0, 0, 0, 0, 0, [0] * 32]
            setup_error = transport.termios.error(errno.EINVAL, 'Invalid argument')
            restore_error = transport.termios.error(errno.EIO, 'restore failed')

            def open_fixture(path, *args):
                return fd if path == port else real_open(path, *args)

            with patch.object(Path, 'home', return_value=Path(directory)), \
                 patch.object(transport.PortLock, 'check_owners'), \
                 patch.object(transport.os, 'open', side_effect=open_fixture), \
                 patch.object(transport, 'exclusive'), \
                 patch.object(transport.termios, 'tcgetattr', return_value=settings), \
                 patch.object(transport.termios, 'tcsetattr', side_effect=[setup_error, restore_error]) as configure:
                with self.assertRaises(transport.termios.error) as result:
                    transport.PosixSerialTransport(port, 230400)
                self.assertIs(result.exception, setup_error)
                self.assertEqual(configure.call_count, 2)
                with self.assertRaises(OSError) as closed:
                    os.fstat(fd)
                self.assertEqual(closed.exception.errno, errno.EBADF)
                retry = transport.PortLock(port)
                retry.acquire()
                retry.release()


if __name__ == '__main__':
    unittest.main()
