import pathlib,sys,time,tempfile,unittest
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from protocol import Session,parse
from simulator import SimulatorTransport
from engine import Controller
from power import wake,mac_address,wake_address,wake_connect

class PowerTests(unittest.TestCase):
 def test_power_frames_strict(self):
  self.assertEqual(parse('^ON0;'),{'powered_on':False});self.assertEqual(parse('^ON1;'),{'powered_on':True})
  self.assertEqual(parse('^MA54:10:EC:14:75:22;')['mac_address'],'54:10:EC:14:75:22')
  for bad in ['^ON2;','^ON;','^WL2;','^MAgarbage;']:
   with self.assertRaises(ValueError):parse(bad)
 def test_off_on_single_explicit_commands_and_cleared_readings(self):
  t=SimulatorTransport();a=Session(t);a.poll(True)
  self.assertEqual(a.action('power_off')['status'],'confirmed');self.assertEqual(t.writes.count('^ON0;'),1)
  self.assertEqual(a.snapshot()['status'],'powered_off');self.assertIsNone(a.snapshot()['operate']);self.assertIsNone(a.snapshot()['forward_watts'])
  before=len(t.writes);a.poll(True);self.assertEqual(t.writes[before:],['^ON;'])
  self.assertEqual(a.power_on(usb=True)['status'],'confirmed');self.assertEqual(t.writes.count('^ON1;'),1);self.assertIn(';;;',t.writes)
  a.poll();self.assertEqual(a.snapshot()['status'],'live')
 def test_no_redundant_on(self):
  t=SimulatorTransport();self.assertEqual(Session(t).power_on()['status'],'confirmed');self.assertNotIn('^ON1;',t.writes)
 def test_off_guards_rf_tune_unknown_and_cancel(self):
  for condition in ['tx','tune','unknown','cancel']:
   t=SimulatorTransport();a=Session(t,cancelled=lambda:condition=='cancel')
   if condition=='tx':t.tx=True
   if condition=='tune':t.tune_until=time.monotonic()+60
   original=a.read
   def read(tag):
    v=original(tag)
    if condition=='unknown' and tag=='VG':a.values['transmitting']=None
    return v
   with patch.object(a,'read',side_effect=read):
    with self.assertRaises(ValueError):a.action('power_off')
   self.assertNotIn('^ON0;',t.writes)
 def test_lost_off_reply_does_not_claim_shutdown(self):
  class Lost(SimulatorTransport):
   def write(self,data):
    if data==b'^ON0;':self.writes.append('^ON0;');self.lost=True;return
    if getattr(self,'lost',False):raise OSError('Connection lost')
    super().write(data)
  t=Lost();r=Session(t).action('power_off');self.assertEqual(r['status'],'unconfirmed');self.assertIn('not confirmed',r['message']);self.assertEqual(t.writes.count('^ON0;'),1)
 def test_unknown_power_blocks_usb_on(self):
  t=SimulatorTransport();a=Session(t)
  with patch.object(a,'read',return_value={}):
   with self.assertRaises(ValueError):a.power_on(usb=True)
  self.assertNotIn('^ON1;',t.writes)
 def test_wake_packet_and_validation(self):
  sock=MagicMock()
  with patch('power.socket.socket') as socket:
   socket.return_value.__enter__.return_value=sock;wake('54:10:EC:14:75:22','192.168.0.255')
  packet,address=sock.sendto.call_args.args;self.assertEqual(packet,b'\xff'*6+bytes.fromhex('5410ec147522')*16);self.assertEqual(address,('192.168.0.255',9));sock.sendto.assert_called_once()
  for mac in ['','FF:FF:FF:FF:FF:FF','00:00:00:00:00:00','not-a-mac']:
   with self.assertRaises(ValueError):mac_address(mac)
  for address in ['localhost','::1','127.0.0.1','0.0.0.0']:
   with self.assertRaises(ValueError):wake_address(address)
 def test_wake_connect_retries_connections_not_wake(self):
  cfg=dict(wake_mac='54:10:EC:14:75:22',wake_broadcast='255.255.255.255',host='192.168.0.18',tcp_port=1500)
  with patch('power.wake') as wake_mock:
   connect=MagicMock(side_effect=[OSError('Not ready'),object()]);result=wake_connect(cfg,lambda:False,connect,lambda _:None);self.assertIsNotNone(result);wake_mock.assert_called_once();self.assertEqual(connect.call_count,2)
  with patch('power.wake') as wake_mock:
   with self.assertRaises(ValueError):wake_connect(cfg,lambda:True,MagicMock(),lambda _:None)
   wake_mock.assert_not_called()
 def test_confirmation_and_generation_and_settings(self):
  with tempfile.TemporaryDirectory() as d:
   c=Controller(pathlib.Path(d)/'settings.json')
   with self.assertRaisesRegex(ValueError,'Confirm Power Off'):c.action({'action':'power_off','generation':c.generation})
   with self.assertRaisesRegex(ValueError,'Connection changed'):c.action({'action':'power_on','generation':'old'})
   c.save_settings({'wake_mac':'54:10:ec:14:75:22','wake_broadcast':'192.168.0.255'});restored=Controller(c.settings);self.assertEqual(restored.config['wake_mac'],'54:10:EC:14:75:22')
   before=c.settings.read_text()
   with self.assertRaises(ValueError):c.save_settings({'wake_mac':'bad'})
   self.assertEqual(c.settings.read_text(),before)

class PowerControllerTests(unittest.TestCase):
 def test_simulator_shutdown_wake_and_no_startup_wake(self):
  with tempfile.TemporaryDirectory() as d:
   c=Controller(pathlib.Path(d)/'settings.json')
   def wait_status(status):
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
     snap=c.snapshot()
     if snap['state']['status']==status and not any(a['status']=='queued' for a in snap['actions']):return snap
     time.sleep(.02)
    self.fail(str(c.snapshot()))
   try:
    c.connect({'mode':'simulator'});wait_status('live')
    c.action({'action':'power_off','generation':c.generation,'confirm_power_off':True});off=wait_status('powered_off');self.assertIsNone(off['state']['forward_watts']);self.assertFalse(off['state']['powered_on'])
    c.action({'action':'power_on','generation':c.generation});on=wait_status('live');self.assertEqual(on['actions'][0]['status'],'confirmed')
   finally:c.disconnect()
 def test_wake_timeout_one_packet_and_bounded(self):
  cfg=dict(wake_mac='54:10:EC:14:75:22',wake_broadcast='255.255.255.255',host='192.168.0.18',tcp_port=1500)
  with patch('power.wake') as wake_mock,patch('power.time.monotonic',side_effect=[0,16]):
   with self.assertRaisesRegex(OSError,'not confirmed'):wake_connect(cfg,lambda:False,MagicMock(side_effect=OSError('Not ready')),lambda _:None)
   wake_mock.assert_called_once()
 def test_cancel_before_usb_on_no_setter(self):
  t=SimulatorTransport();t.power=False;a=Session(t,cancelled=lambda:True)
  with self.assertRaises(ValueError):a.power_on(usb=True)
  self.assertEqual(t.writes,[])

class GenericMACDiscoveryTests(unittest.TestCase):
 def test_controller_saves_reported_mac_for_any_amplifier(self):
  import queue
  with tempfile.TemporaryDirectory() as d:
   c=Controller(pathlib.Path(d)/'settings.json');c.events=queue.Queue()
   try:
    for address in ['54:10:EC:12:34:56','00:11:22:33:44:66']:
     c.events.put(('identity',address));c.pump();self.assertEqual(Controller(c.settings).config['wake_mac'],address)
   finally:c.events=None
 def test_changing_network_endpoint_clears_old_mac(self):
  with tempfile.TemporaryDirectory() as d:
   c=Controller(pathlib.Path(d)/'settings.json');c.save_settings({'host':'192.168.0.18','wake_mac':'00:11:22:33:44:66'});c.save_settings({'host':'192.168.0.19'});self.assertEqual(c.config['wake_mac'],'')
 def test_ethernet_wake_never_sends_usb_power_setter(self):
  t=SimulatorTransport();t.power=False;a=Session(t)
  original=a.read;reads=0
  def read(tag):
   nonlocal reads
   reads+=1
   if reads>2:t.power=True
   return original(tag)
  with patch.object(a,'read',side_effect=read):self.assertEqual(a.power_on(wake_only=True)['status'],'confirmed')
  self.assertNotIn('^ON1;',t.writes)

class USBWakeHandshakeTests(unittest.TestCase):
 def test_sleeping_usb_can_miss_first_query_without_setter_retry(self):
  class Sleepy(SimulatorTransport):
   def __init__(self):super().__init__();self.power=False;self.missed=False
   def write(self,data):
    if data==b'^ON;' and not self.missed:self.missed=True;self.writes.append('^ON;');return
    super().write(data)
  t=Sleepy();a=Session(t);self.assertEqual(a.power_on(usb=True)['status'],'confirmed');self.assertEqual(t.writes.count('^ON1;'),1)

class WakeSuccessMessageTests(unittest.TestCase):
 def test_wake_success_is_distinct_from_already_on(self):
  t=SimulatorTransport();a=Session(t)
  self.assertIn('Wake-on-LAN startup confirmed',a.power_on(wake_only=True)['message'])
  self.assertIn('already powered on',a.power_on()['message'])
  self.assertNotIn('^ON1;',t.writes)
