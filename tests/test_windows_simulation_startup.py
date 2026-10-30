"""Offline initial-worker recovery; no processes, devices or sockets."""
import json,os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Sources'))
from windows_simulation_startup import start_simulation
from unittest.mock import patch
import engine
_real_worker=engine.worker_main

def fail_once_worker(config,events,commands,stop):
 marker=Path(config['_startup_test_marker'])
 if marker.exists():return _real_worker(config,events,commands,stop)
 marker.write_text(str(os.getpid()));events.cancel_join_thread()
 outcome=[('error','[WinError 6] The handle is invalid')]
 try:config['_completion'].send(outcome)
 finally:config['_completion'].close()

class InitialSimulationTests(unittest.TestCase):
 class Controller:
  offline_only=True
  def __init__(self,path,states):self.settings=path;self.states=states;self.connects=[];self.actions=[];self.attempt=0
  def connect(self,value):
   self.connects.append(value);self.attempt+=1
   state=self.states[min(self.attempt-1,len(self.states)-1)]
   if isinstance(state,Exception):raise state
  def snapshot(self):
   state=self.states[min(self.attempt-1,len(self.states)-1)]
   if isinstance(state,Exception):state={'status':'error','message':str(state)}
   return {'state':dict(state),'actions':list(self.actions)}
 def run_case(self,states):
  temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
  c=self.Controller(Path(temporary.name)/'settings.json',states);result=start_simulation(c);return c,result
 def test_invalid_handle_worker_is_recreated_once_and_failure_is_retained(self):
  c,result=self.run_case([{'status':'error','message':'[WinError 6] The handle is invalid'},{'status':'live'}])
  self.assertEqual(result['state']['status'],'live');self.assertEqual(c.connects,[{'mode':'simulator'}]*2);self.assertEqual(c.actions,[])
  event=json.loads(c.settings.with_suffix('.startup-events.jsonl').read_text());self.assertEqual(event['attempt'],1);self.assertIn('WinError 6',event['error'])
 def test_second_invalid_handle_remains_error_without_a_third_attempt(self):
  c,result=self.run_case([{'status':'error','message':'[WinError 6] The handle is invalid'}])
  self.assertEqual(result['state']['status'],'error');self.assertEqual(len(c.connects),2)
 def test_other_errors_are_preserved_without_retry(self):
  c,result=self.run_case([{'status':'error','message':'Synthetic reader exit'}]);self.assertEqual(len(c.connects),1);self.assertEqual(result['state']['message'],'Synthetic reader exit')
 def test_hardware_controller_is_rejected_before_connect(self):
  c=self.Controller(Path('unused.json'),[]);c.offline_only=False
  with self.assertRaisesRegex(ValueError,'offline-only'):start_simulation(c)
  self.assertEqual(c.connects,[])
 def test_runtime_failure_after_success_does_not_reconnect(self):
  c,result=self.run_case([{'status':'live'}]);c.states=[{'status':'error','message':'[WinError 6] The handle is invalid'}]
  self.assertEqual(c.snapshot()['state']['status'],'error');self.assertEqual(len(c.connects),1)
 def test_start_failure_with_error6_uses_same_bounded_recovery(self):
  error=OSError('[WinError 6] The handle is invalid');error.winerror=6
  c,result=self.run_case([error,{'status':'live'}]);self.assertEqual(result['state']['status'],'live');self.assertEqual(len(c.connects),2)
 def test_other_start_exception_propagates(self):
  with self.assertRaisesRegex(OSError,'different'):self.run_case([OSError('different')])
 def test_spawned_failed_worker_is_disposed_before_fresh_simulator_recovers(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);controller=engine.Controller(root/'settings.json',offline_only=True)
   controller.config['_startup_test_marker']=str(root/'first-worker.txt')
   try:
    with patch('engine.worker_main',fail_once_worker):result=start_simulation(controller)
    self.assertEqual(result['state']['status'],'live');self.assertTrue(result['state']['demo'])
    self.assertNotEqual(controller.worker.pid,int((root/'first-worker.txt').read_text()))
    self.assertEqual(result['actions'],[]);self.assertTrue(controller.settings.with_suffix('.startup-events.jsonl').exists())
   finally:controller.disconnect()

if __name__=='__main__':unittest.main()
