import pathlib,sys,time,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from protocol import Session
from simulator import SimulatorTransport

class DelayedCancel(SimulatorTransport):
 def __init__(self,reads=2,failure=None):
  super().__init__();self.tune_until=time.monotonic()+60;self.remaining=reads;self.cancelling=False;self.failure=failure
 def write(self,data):
  if data==b'^FE;':
   self.writes.append('^FE;');self.cancelling=True;return
  if self.cancelling and data==b'^TP;':
   if self.failure:raise self.failure
   if self.remaining<=0:self.tune_until=0
   self.remaining-=1
  super().write(data)

class CancelConfirmationTests(unittest.TestCase):
 def test_delayed_cancel_confirms_without_replaying(self):
  t=DelayedCancel();a=Session(t)
  self.assertEqual(a.action('cancel_tune')['status'],'confirmed')
  self.assertEqual(t.writes.count('^FE;'),1)
  self.assertEqual(t.writes.count('^TP;'),4) # preflight plus three readbacks
  self.assertFalse(a.values['tuning'])
 def test_never_stops_is_bounded_and_unconfirmed(self):
  t=DelayedCancel(reads=1000);a=Session(t);start=time.monotonic()
  self.assertEqual(a.action('cancel_tune')['status'],'unconfirmed')
  self.assertLess(time.monotonic()-start,2)
  self.assertEqual(t.writes.count('^FE;'),1)
  self.assertTrue(a.values['tuning'])
 def test_missing_readback_is_not_confirmed_from_cached_state(self):
  t=DelayedCancel(failure=TimeoutError('No response'));a=Session(t)
  self.assertEqual(a.action('cancel_tune')['status'],'unconfirmed')
  self.assertEqual(t.writes.count('^FE;'),1)
 def test_connection_failure_propagates_without_replay(self):
  t=DelayedCancel(failure=OSError('Disconnected'));a=Session(t)
  with self.assertRaises(OSError):a.action('cancel_tune')
  self.assertEqual(t.writes.count('^FE;'),1)
 def test_disconnect_stops_confirmation_queries(self):
  t=DelayedCancel();a=Session(t,cancelled=lambda:t.cancelling and t.remaining<2)
  with self.assertRaisesRegex(ValueError,'closing'):a.action('cancel_tune')
  self.assertEqual(t.writes.count('^FE;'),1)
  self.assertEqual(t.writes.count('^TP;'),2)
 def test_other_controls_do_not_wait_or_repeat(self):
  t=SimulatorTransport();a=Session(t)
  with patch('protocol.time.sleep') as sleep:
   self.assertEqual(a.action('operate')['status'],'confirmed');sleep.assert_not_called()
  self.assertEqual(t.writes.count('^OS1;'),1)

class AntennaSelectionTests(unittest.TestCase):
 def test_explicit_ports_and_worker_rf_guards(self):
  t=SimulatorTransport();a=Session(t)
  for action,port in [('antenna_2',2),('antenna_1',1)]:
   self.assertEqual(a.action(action)['status'],'confirmed');self.assertEqual(a.values['antenna'],port)
  t.tx=True
  for action in ['antenna_1','antenna_2']:
   before=list(t.writes)
   with self.assertRaisesRegex(ValueError,'transmitting'):a.action(action)
   self.assertEqual([w for w in t.writes[len(before):] if w in ['^AN1;','^AN2;']],[])
  t.tx=False;t.tune_until=time.monotonic()+60
  for action in ['antenna_1','antenna_2']:
   with self.assertRaisesRegex(ValueError,'tune is active'):a.action(action)

class AntennaWarningTests(unittest.TestCase):
 def test_disabled_antenna_suggests_configuration_without_retry(self):
  class DisabledAntenna(SimulatorTransport):
   def write(self,data):
    if data==b'^AN2;':self.writes.append('^AN2;');return
    super().write(data)
  t=DisabledAntenna();a=Session(t);result=a.action('antenna_2')
  self.assertEqual(result['status'],'unconfirmed')
  self.assertIn('Check the amplifier antenna configuration for the current band',result['message'])
  self.assertIn('may be disabled',result['message'])
  self.assertEqual(t.writes.count('^AN2;'),1)
  self.assertEqual(a.values['antenna'],1)
