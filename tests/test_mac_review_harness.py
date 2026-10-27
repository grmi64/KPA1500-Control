"""Generator tests only: no Mac APIs, settings, devices, or network accessed."""
import importlib.util,json,pathlib,plistlib,re,tempfile,unittest

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
  self.assertIn('reviewDefaults?.set(NSStringFromRect(window.frame), forKey: "ReviewMainFrame")',result)
  self.assertNotIn('UserDefaults.standard',result);self.assertNotIn('setFrameAutosaveName(',result)
  self.assertNotIn('"com.grmi64.KPA1500Control"',result)
 def test_geometry_suite_is_distinct_and_initialized_without_force_unwrap(self):
  identifier='com.grmi64.KPA1500Control.WindowsReview.test'
  result=harness.render(self.source(),'/tmp/review.json',51982,identifier=identifier)
  self.assertIn('guard let geometryDefaults = UserDefaults(suiteName: "'+identifier+'.geometry") else {',result)
  self.assertNotIn('UserDefaults(suiteName: "'+identifier+'")',result)
  self.assertNotRegex(result,r'UserDefaults\(suiteName:[^\n]+\)!')
  self.assertIn('var reviewDefaults: UserDefaults?',result)
  self.assertNotIn('reviewDefaults.',result)
 def test_suite_failure_returns_before_window_or_backend_start(self):
  result=harness.render(self.source(),'/tmp/review.json',51982)
  guard=result.index('guard let geometryDefaults = UserDefaults(')
  assignment=result.index('reviewDefaults = geometryDefaults')
  failure=result[guard:assignment]
  self.assertIn('No backend was started.',failure)
  self.assertIn('NSApp.terminate(nil); return',failure)
  self.assertLess(result.index('guard Bundle.main.bundleIdentifier == identifier'),guard)
  self.assertLess(assignment,result.index('let lockDirectory'))
  self.assertLess(assignment,result.index('window = NSWindow('))
  self.assertLess(assignment,result.index('launchReader()'))
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
   plan=json.loads((out/'review-plan.json').read_text())
   bundle=plistlib.loads((out/'Info.plist').read_bytes())['CFBundleIdentifier']
   generated=(out/'App.swift').read_text(encoding='utf-8')
   suite=re.search(r'guard let geometryDefaults = UserDefaults\(suiteName: "([^"]+)"\)',generated).group(1)
   self.assertNotEqual(suite,bundle)
   self.assertEqual(suite,bundle+'.geometry')
   self.assertEqual(plan['geometry_suite'],suite)
   self.assertEqual(plan['geometry_domain'],suite)
   self.assertEqual(plan['bundle_identifier'],bundle)
   with self.assertRaises(ValueError):harness.prepare(project,out,settings,51981)
   settings.write_text('production-like data')
   with self.assertRaises(ValueError):harness.prepare(project,project/'.tmp/second',settings,51981)
   self.assertEqual(settings.read_text(),'production-like data')
 def test_external_output_or_settings_are_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   root=pathlib.Path(directory)
   with self.assertRaises(ValueError):harness.prepare(root,root/'Sources/generated',root/'.tmp/settings.json',51981)
   with self.assertRaises(ValueError):harness.prepare(root,root/'.tmp/generated',root/'production.json',51981)
