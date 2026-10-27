"""Generator tests only: no Mac APIs, settings, devices, or network accessed."""
import importlib.util,json,pathlib,tempfile,unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mac_review_harness',ROOT/'scripts/prepare_mac_review.py')
harness=importlib.util.module_from_spec(spec);spec.loader.exec_module(harness)

class MacReviewHarnessTests(unittest.TestCase):
 def source(self):return (ROOT/'Sources/App.swift').read_text(encoding='utf-8')
 def test_forces_simulation_stable_review_port_and_explicit_settings(self):
  result=harness.render(self.source(),'/tmp/review settings.json',51981)
  self.assertIn('"--demo", "--http-port", "51981", "--settings", "/tmp/review settings.json"',result)
  self.assertNotIn('CommandLine.arguments.contains("--demo")',result)
 def test_rejects_ephemeral_production_and_invalid_ports(self):
  for port in (0,51980,1023,65536,True):
   with self.assertRaises(ValueError):harness.render(self.source(),'/tmp/review.json',port)
 def test_explicit_review_identity_store_and_geometry_domain(self):
  result=harness.render(self.source(),'/tmp/review.json',51981)
  self.assertIn('guard Bundle.main.bundleIdentifier == identifier',result)
  self.assertIn('WKWebsiteDataStore(forIdentifier:',result)
  self.assertIn('reviewDefaults.set(NSStringFromRect(window.frame), forKey: "ReviewMainFrame")',result)
  self.assertNotIn('UserDefaults.standard',result);self.assertNotIn('setFrameAutosaveName(',result)
  self.assertNotIn('"com.grmi64.KPA1500Control"',result)
 def test_changed_source_fails_closed(self):
  with self.assertRaises(ValueError):harness.render('changed wrapper','/tmp/review.json',51981)
 def test_control_characters_in_paths_rejected(self):
  with self.assertRaises(ValueError):harness.render(self.source(),'/tmp/review\nfile',51981)
 def test_generation_is_private_and_does_not_overwrite_settings(self):
  with tempfile.TemporaryDirectory() as directory:
   project=pathlib.Path(directory);(project/'Sources').mkdir();(project/'Sources/App.swift').write_text(self.source(),encoding='utf-8');(project/'Sources/version.py').write_text("VERSION='0.1.25'\nBUILD='26'\n")
   settings=project/'.tmp/settings/review.json';out=project/'.tmp/harness'
   harness.prepare(project,out,settings,51981)
   self.assertFalse(settings.exists());self.assertTrue((out/'App.swift').exists())
   self.assertTrue(json.loads((out/'review-plan.json').read_text())['geometry_domain'].startswith(harness.IDENTIFIER+'.'))
   with self.assertRaises(ValueError):harness.prepare(project,out,settings,51981)
   settings.write_text('production-like data')
   with self.assertRaises(ValueError):harness.prepare(project,project/'.tmp/second',settings,51981)
   self.assertEqual(settings.read_text(),'production-like data')
 def test_external_output_or_settings_are_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   root=pathlib.Path(directory)
   with self.assertRaises(ValueError):harness.prepare(root,root/'Sources/generated',root/'.tmp/settings.json',51981)
   with self.assertRaises(ValueError):harness.prepare(root,root/'.tmp/generated',root/'production.json',51981)
