import pathlib,sys,time,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from protocol import Session,parse,FAST,SLOW
from simulator import SimulatorTransport
class CoolingTests(unittest.TestCase):
 def session(self,transport=None):
  t=transport or SimulatorTransport();s=Session(t);s.identify();s.poll(True);return s,t
 def test_parse_and_invalid_levels(self):
  for n in range(6):
   self.assertEqual(parse('^FC%d;'%n),{'fan_minimum':n});self.assertEqual(parse('^FS%d;'%n),{'fan_speed':n})
  for raw in ['^FC6;','^FS9;','^FC-1;','^FC1.5;','^FCnan;']:
   with self.assertRaises(ValueError):parse(raw)
 def test_poll_reads_only_at_slow_cadence(self):
  s,t=self.session();self.assertEqual(s.snapshot()['fan_minimum'],0);self.assertEqual(s.snapshot()['fan_speed'],2)
  self.assertIn('FC',SLOW);self.assertNotIn('FC',FAST)
  start=len(t.writes);s.poll(False);self.assertNotIn('^FC;',t.writes[start:]);self.assertNotIn('^FS;',t.writes[start:]);self.assertFalse(any(x.startswith('^FC') and x!='^FC;' for x in t.writes))
 def test_every_level_once_and_readback(self):
  s,t=self.session()
  for n in [5,3,1,0]:
   start=len(t.writes);self.assertEqual(s.action('fan_'+str(n))['status'],'confirmed');self.assertEqual(t.writes[start:].count('^FC%d;'%n),1);self.assertEqual(s.values['fan_minimum'],n)
  self.assertGreaterEqual(t.fan_minimum,0)
 def test_rf_tune_unknown_and_cancel_guards(self):
  s,t=self.session();t.tx=True
  with self.assertRaisesRegex(ValueError,'transmitting'):s.action('fan_5')
  t.tx=False;t.tune_until=time.monotonic()+10
  with self.assertRaisesRegex(ValueError,'tune'):s.action('fan_5')
  t.tune_until=0;s.cancelled=lambda:True
  with self.assertRaisesRegex(ValueError,'closing'):s.action('fan_5')
  self.assertNotIn('^FC5;',t.writes)
  for name in ['fan_6','fan_-1','fan_1;^OS1']:
   with self.assertRaises(ValueError):s.action(name)
 def test_unsupported_blocks_setter(self):
  class Unsupported(SimulatorTransport):
   def write(self,data):
    if data==b'^FC;':self.writes.append(data.decode());self.buffer+=b'^?;'
    else:super().write(data)
  s,t=self.session(Unsupported())
  with self.assertRaisesRegex(ValueError,'verify'):s.action('fan_4')
  self.assertNotIn('^FC4;',t.writes)
 def test_echo_is_not_confirmation(self):
  class Ignored(SimulatorTransport):
   def write(self,data):
    if data==b'^FC4;':self.writes.append(data.decode());self.buffer+=data
    else:super().write(data)
  s,t=self.session(Ignored());self.assertEqual(s.action('fan_4')['status'],'unconfirmed');self.assertEqual(t.writes.count('^FC4;'),1)
 def test_stale_clears_both_fan_readings(self):
  s,t=self.session();s.last_live=time.time()-4
  self.assertIsNone(s.snapshot()['fan_minimum']);self.assertIsNone(s.snapshot()['fan_speed'])
if __name__=='__main__':unittest.main()
