"""Logical Windows profile identity; no GUI, transport, discovery or hardware."""
import os,pathlib,sys,tempfile,unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
import platform_paths,windows_app,windows_instance,windows_launch

class LogicalSettingsTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name).absolute();self.base=self.root/'Local'/'KPA1500'/'settings.json'
  self.private=self.root/'Local'/'Packages'/'review'/'LocalCache'/'Local'/'KPA1500'/'settings.json'
  self.patches=[patch.object(platform_paths,'WINDOWS',True),patch.object(windows_instance,'WINDOWS',True),patch('windows_lease.activation_directory',return_value=self.root/'LocalLow'/'instances')]
  for p in self.patches:p.start()
 def tearDown(self):
  for p in reversed(self.patches):p.stop()
  self.temp.cleanup()
 def forbidden_resolution(self):return patch.object(pathlib.Path,'resolve',side_effect=AssertionError('Physical file resolution would split the MSIX identity'))
 def test_existing_settings_never_resolve_to_package_storage(self):
  self.private.parent.mkdir(parents=True);self.private.write_text('{}')
  with self.forbidden_resolution():
   self.assertEqual(platform_paths.settings_path(self.base),self.base)
   before=windows_instance.Instance(self.base)
   self.base.parent.mkdir(parents=True);self.base.write_text('{}')
   after=windows_instance.Instance(self.base)
   self.assertEqual(before.lease.key,after.lease.key);self.assertEqual(before.path,after.path)
   self.assertEqual(before.legacy_path,self.base.with_suffix('.instance.json'))
   self.assertNotIn('LocalCache',before.lease.key)
 def test_relative_and_dot_segment_spellings_have_same_identity(self):
  variant=self.base.parent/'nested'/'..'/'settings.json'
  relative='offline-identity-review.json';absolute_relative=pathlib.Path(os.path.abspath(relative))
  with self.forbidden_resolution():
   normal=windows_instance.Instance(self.base)
   self.assertEqual(normal.lease.key,windows_instance.Instance(variant).lease.key)
   self.assertEqual(windows_instance.Instance(absolute_relative).lease.key,windows_instance.Instance(relative).lease.key)
 def test_case_spelling_is_normalized_for_identity(self):
  with self.forbidden_resolution():
   self.assertEqual(windows_instance.Instance(str(self.base).upper()).lease.key,windows_instance.Instance(str(self.base).lower()).lease.key)
 def test_distinct_logical_profiles_remain_distinct(self):
  with self.forbidden_resolution():
   a=windows_instance.Instance(self.base);b=windows_instance.Instance(self.base.with_name('other.json'))
   self.assertNotEqual(a.path,b.path);self.assertNotEqual(a.lease.key,b.lease.key)
 def test_all_mode_profiles_and_handoff_arguments_remain_logical(self):
  self.private.parent.mkdir(parents=True);self.private.write_text('{}');self.base.parent.mkdir(parents=True);self.base.write_text('{}')
  state={'state':{'status':'disconnected'},'actions':[]}
  with self.forbidden_resolution():
   for mode in windows_launch.MODES:
    with self.subTest(mode=mode):
     expected=self.base if mode=='simulation' else self.base.with_name('settings.'+mode+'.json')
     self.assertEqual(windows_launch.mode_settings(self.base,mode),expected)
     value=dict(mode=mode,confirmed=True,connection=dict(mode='tcp',host='192.0.2.18',tcp_port=1500,baud=230400))
     argv=windows_launch.prepare_reopen(value,state,self.base)
     self.assertIn('--settings='+str(self.base),argv);self.assertIn('--mode-handoff',argv)
 def test_main_startup_passes_logical_profile_before_any_backend_or_gui(self):
  class StopBeforeBackend(Exception):pass
  self.private.parent.mkdir(parents=True);self.private.write_text('{}')
  with self.forbidden_resolution(),patch.object(windows_app.sys,'platform','win32'),patch('windows_app.configure_process_dpi'),patch('windows_app.Instance',side_effect=StopBeforeBackend) as instance,patch('windows_app.Controller',side_effect=AssertionError('Backend forbidden')):
   for flag,mode in [('--demo','simulation'),('--read-only','read-only'),('--hardware','hardware')]:
    with self.subTest(mode=mode),self.assertRaises(StopBeforeBackend):windows_app.main([flag,'--settings',str(self.base)])
    expected=self.base if mode=='simulation' else self.base.with_name('settings.'+mode+'.json')
    self.assertEqual(instance.call_args.args[0],expected)
 def test_confirmed_simulation_workflow_retains_base_identity(self):
  from engine import Controller
  controller=Controller(self.base,offline_only=True);discovery=Mock();discovery.snapshot.return_value={'running':False}
  with self.forbidden_resolution():
   workflow=windows_launch.LaunchWorkflow(controller,discovery,self.base,'simulation')
   self.assertTrue(workflow.request(dict(mode='simulation',confirmed=True))['reopening'])
   self.assertIn('--settings='+str(self.base),workflow.pending);self.assertIsNone(controller.worker)
 def test_non_windows_resolution_behavior_is_preserved(self):
  physical=self.root/'physical.json'
  with patch.object(platform_paths,'WINDOWS',False),patch.object(pathlib.Path,'resolve',return_value=physical) as resolve:
   self.assertEqual(platform_paths.settings_path(self.base),physical);resolve.assert_called_once_with()

if __name__=='__main__':unittest.main()
