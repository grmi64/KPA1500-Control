"""Offline regressions for the frozen host's .NET download-aware configuration."""
import importlib.util
import pathlib
import tempfile
import unittest
import xml.etree.ElementTree as ET
ROOT = pathlib.Path(__file__).resolve().parents[1]

class DotNetPackagingTests(unittest.TestCase):
    def test_configuration_is_only_for_the_application_clr(self):
        root = ET.parse(ROOT / 'Sources/windows_dotnet.config').getroot()
        self.assertEqual(root.tag, 'configuration')
        self.assertEqual(len(root), 1)
        runtime = root.find('runtime')
        self.assertEqual(len(runtime), 1)
        self.assertEqual(runtime[0].tag, 'loadFromRemoteSources')
        self.assertEqual(runtime[0].attrib, {'enabled': 'true'})

    def test_build_copies_config_beside_each_named_executable(self):
        source = (ROOT / 'scripts/build-windows.ps1').read_text()
        self.assertIn('"$project/Sources/windows_dotnet.config" -Destination ($exe + \'.config\')', source)

    def test_audit_requires_exact_config_for_both_build_names(self):
        spec = importlib.util.spec_from_file_location('identity_audit', ROOT / 'scripts/check-windows-identity.py')
        audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audit)
        with tempfile.TemporaryDirectory() as folder:
            package = pathlib.Path(folder)
            for name in ('KPA1500 Control', 'KPA1500 Control Review'):
                with self.assertRaisesRegex(RuntimeError, '.NET configuration'):
                    audit.check_dotnet_config(package, name)
                path = package / (name + '.exe.config')
                path.write_bytes((ROOT / 'Sources/windows_dotnet.config').read_bytes())
                audit.check_dotnet_config(package, name)
                path.write_text('<configuration/>')
                with self.assertRaisesRegex(RuntimeError, '.NET configuration'):
                    audit.check_dotnet_config(package, name)
                path.unlink()
