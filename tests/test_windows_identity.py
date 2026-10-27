"""Offline Windows identity/version and application-license packaging regressions."""
import importlib.util,pathlib,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from windows_identity import PRODUCT_NAME,REVIEW_NAME,numeric_version,version_resource
from version import VERSION,BUILD
ROOT=pathlib.Path(__file__).resolve().parents[1]

class IdentityTests(unittest.TestCase):
 def test_version_is_derived_without_changing_shared_mac_version(self):
  self.assertEqual(numeric_version(),tuple(map(int,VERSION.split('.')+[BUILD])))
  for version,build in [('1.2','3'),('1.2.3-beta','1'),('1.2.65536','1'),('1.2.3','-1'),('1.2.3','65536'),('1.2.3',True)]:
   with self.assertRaises(ValueError):numeric_version(version,build)
 @unittest.skipUnless(sys.platform=='win32','PE resource parser uses Windows build dependencies.')
 def test_resources_parse_and_distinguish_review_from_production_filename(self):
  from PyInstaller.utils.win32.versioninfo import load_version_info_from_text_file
  for name in (PRODUCT_NAME,REVIEW_NAME):
   with tempfile.TemporaryDirectory() as directory:
    path=pathlib.Path(directory)/'version.txt';path.write_text(version_resource(name),encoding='utf-8');resource=load_version_info_from_text_file(path)
    self.assertEqual(resource.ffi.fileVersionMS,(numeric_version()[0]<<16)|numeric_version()[1]);self.assertTrue(resource.toRaw())
    self.assertIn(repr(name+'.exe'),path.read_text(encoding='utf-8'));self.assertIn('flags=0x2',path.read_text(encoding='utf-8'))
  with self.assertRaises(ValueError):version_resource('Other product')
 def test_packaged_application_license_is_required_in_both_locations(self):
  spec=importlib.util.spec_from_file_location('notice_check',ROOT/'scripts/check-windows-notices.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory() as directory:
   root=pathlib.Path(directory);(root/'LICENSE').write_text('MIT License\nTest rights notice.\n',encoding='utf-8');package=root/'package';(package/'_internal').mkdir(parents=True)
   with patch.object(module,'PROJECT',root):
    with self.assertRaises(RuntimeError):module.check_application_license(package)
    for path in (package/'LICENSE',package/'_internal/LICENSE'):path.write_bytes((root/'LICENSE').read_bytes())
    module.check_application_license(package)
    (package/'LICENSE').write_text('different grant',encoding='utf-8')
    with self.assertRaises(RuntimeError):module.check_application_license(package)
