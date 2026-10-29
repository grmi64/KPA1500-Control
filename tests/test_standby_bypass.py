"""Observed firmware 03.06 inhibited Standby; all transports are synthetic."""
import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from protocol import parse,Session
from simulator import SimulatorTransport
FRAME='^VG TR inhibit x01 TR_STATE_PA_BYPASSED_3R_ON 3R:0 3T:0 Bias:0 PA STBY KeyIn:0  MODE_STBY;'
class ObservedStandby(SimulatorTransport):
 def __init__(self,frame=FRAME):super().__init__();self.frame=frame
 def write(self,data):
  if data==b'^VG;':self.writes.append(data.decode());self.buffer+=self.frame.encode();return
  super().write(data)
class StandbyBypassTests(unittest.TestCase):
 def session(self,frame=FRAME):
  t=ObservedStandby(frame);s=Session(t);s.identify();s.poll(True);return s,t
 def test_complete_observed_frame_and_existing_receive_relay_variant(self):
  for frame in (FRAME,FRAME.replace('3R:0','3R:1'),FRAME.replace('  ',' ')):
   with self.subTest(frame=frame):self.assertIs(parse(frame)['transmitting'],False)
 def test_transmit_or_key_indications_take_precedence(self):
  for old,new in [('KeyIn:0','KeyIn:1'),('3T:0','3T:1'),('TR_STATE_PA_BYPASSED_3R_ON','TR_STATE_TX')]:
   with self.subTest(new=new):self.assertIs(parse(FRAME.replace(old,new))['transmitting'],True)
 def test_incomplete_unknown_or_conflicting_diagnostics_remain_unknown(self):
  for old,new in [('TR inhibit x01','TR inhibit x00'),('3R:0','3R:2'),('3R:0',''),('3T:0',''),('Bias:0','Bias:1'),('Bias:0',''),('KeyIn:0',''),('PA STBY','PA OPER'),('MODE_STBY','MODE_OPER'),('MODE_STBY',''),('TR_STATE_PA_BYPASSED_3R_ON','TR_STATE_UNKNOWN'),('3R:0','3R:0 3R:1'),('Bias:0','Bias:0 Bias:1')]:
   with self.subTest(old=old,new=new):self.assertIsNone(parse(FRAME.replace(old,new))['transmitting'])
 def test_atu_setters_confirm_once_with_observed_standby(self):
  s,t=self.session()
  for action,setter in [('atu_in','^AMI;'),('atu_bypass','^AMB;')]:
   self.assertEqual(s.action(action)['status'],'confirmed');self.assertEqual(t.writes.count(setter),1)
 def test_unknown_or_active_frames_prevent_setter_after_previous_idle(self):
  for frame in (FRAME.replace('Bias:0','Bias:1'),FRAME.replace('KeyIn:0','KeyIn:1'),FRAME.replace('3T:0','3T:1'),FRAME.replace('PA STBY','PA OPER')):
   with self.subTest(frame=frame):
    s,t=self.session();t.frame=frame
    with self.assertRaisesRegex(ValueError,'transmitting'):s.action('atu_in')
    self.assertNotIn('^AMI;',t.writes)
 def test_independent_rf_gate_still_blocks_observed_standby(self):
  s,t=self.session();t.tx=True
  with self.assertRaisesRegex(ValueError,'RF'):s.action('atu_in')
  self.assertNotIn('^AMI;',t.writes)
if __name__=='__main__':unittest.main()
