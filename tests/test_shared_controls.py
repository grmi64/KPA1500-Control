import http.client,json,pathlib,sys,tempfile,threading,time,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from engine import Controller
from server import handler_for
from http.server import ThreadingHTTPServer
class SharedControlsTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.c=Controller(pathlib.Path(self.tmp.name)/'settings.json')
 def tearDown(self):self.tmp.cleanup()
 def ready(self):
  self.c.config.update(share_readings=True,share_controls=True)
  self.c.state=dict(status='live',age_seconds=0,transmitting=False,tuning=False,operate=False,forward_watts=0,demo=True);self.c.received=time.time()
 def test_opt_in_persistence_revocation_and_offline(self):
  self.assertFalse(self.c.config['share_controls'])
  with self.assertRaises(PermissionError):self.c.shared_controls()
  self.c.save_settings(dict(share_readings=True,share_controls=True));self.assertTrue(Controller(self.c.settings).config['share_controls'])
  self.c.save_settings(dict(share_readings=False));self.assertFalse(self.c.config['share_controls'])
  self.assertFalse(Controller(self.c.settings,offline_only=True).config['share_controls'])
  self.c.read_only=True
  with self.assertRaises(ValueError):self.c.save_settings(dict(share_readings=True,share_controls=True))
 def test_guards(self):
  self.ready();self.assertTrue(self.c.shared_controls()['can_operate']);self.assertFalse(self.c.shared_controls()['can_standby'])
  for change in ({'transmitting':True},{'transmitting':None},{'tuning':True},{'operate':None},{'forward_watts':1},{'forward_watts':None},{'age_seconds':5},{'status':'error'}):
   self.ready();self.c.state.update(change);self.assertFalse(self.c.shared_controls()['can_operate'])
  for attr in ('read_only','offline_only','launch_pending'):
   self.ready();setattr(self.c,attr,True);self.assertFalse(self.c.shared_controls()['can_operate']);setattr(self.c,attr,False)
  self.ready();self.c.action_log=[{'status':'queued'}];self.assertFalse(self.c.shared_controls()['can_operate'])
  self.ready();self.c.action_log=[];self.c.state['operate']=True;self.assertTrue(self.c.shared_controls()['can_standby'])
 def test_binding_and_exact_actions(self):
  self.ready();value=dict(action='operate',generation=self.c.generation,expected_operate=False)
  with patch.object(self.c,'action',return_value={'status':'queued'}) as action:
   self.c.shared_control_action(value);action.assert_called_once_with(dict(action='operate',generation=self.c.generation))
   for change in ({'generation':'old'},{'expected_operate':True},{'expected_operate':0},{'action':'power_off'}):
    with self.assertRaises(ValueError):self.c.shared_control_action(dict(value,**change))
   self.assertEqual(action.call_count,1)
 def test_http_auth_deduplication_and_revocation(self):
  self.ready();server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(self.c,'ui-token',simulate_discovery=True));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  def request(method='GET',body=None,headers=None):
   client=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=2);client.request(method,'/api/v1/controls',body=json.dumps(body) if body is not None else None,headers=headers or {});response=client.getresponse();result=(response.status,json.loads(response.read()));client.close();return result
  try:
   code,data=request();self.assertEqual(code,200);token=data['control_token'];self.assertNotEqual(token,'ui-token')
   self.assertEqual(request(headers={'Origin':'http://evil.example'})[0],403);self.assertEqual(request(headers={'Host':'evil.example'})[0],403)
   value=dict(action='operate',generation=self.c.generation,expected_operate=False,id='offline-test-request-001');headers={'X-KPA-Feed-Token':token}
   self.assertEqual(request('POST',value)[0],403);self.assertEqual(request('POST',value,dict(headers,Origin='http://127.0.0.1'))[0],403)
   self.assertEqual(request('POST',{'id':'x'*2048},headers)[0],400)
   with patch.object(self.c,'action',return_value={'status':'queued','id':'fake'}) as action:
    for _ in range(2):self.assertTrue(request('POST',value,headers)[1]['queued'])
    action.assert_called_once();self.assertEqual(request('POST',dict(value,action='standby'),headers)[0],400)
    self.c.config['share_controls']=False;self.assertEqual(request('POST',value,headers)[0],403)
  finally:server.shutdown();server.server_close();thread.join(2)

 def test_real_simulator_worker_operate_then_standby(self):
  self.c.config.update(share_readings=True,share_controls=True)
  try:
   self.c.connect({'mode':'simulator'})
   deadline=time.time()+8
   while time.time()<deadline and not self.c.shared_controls()['can_operate']:time.sleep(.05)
   for name,expected in [('operate',True),('standby',False)]:
    caps=self.c.shared_controls();self.assertTrue(caps['can_'+name])
    receipt=self.c.shared_control_action(dict(action=name,generation=caps['generation'],expected_operate=caps['operate']))
    self.assertEqual(receipt['status'],'queued');deadline=time.time()+8
    while time.time()<deadline:
     snap=self.c.snapshot();action=next((a for a in snap['actions'] if a['id']==receipt['id']),{})
     if action.get('status')!='queued':break
     time.sleep(.05)
    self.assertEqual(action['status'],'confirmed');self.assertIs(self.c.snapshot()['state']['operate'],expected)
  finally:self.c.disconnect()

 def receipt_pressure(self,kind,power=False):
  self.ready();self.c.config['share_power']=power;server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(self.c,'private-ui-token',simulate_discovery=True));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  def request(method='GET',value=None,token=None):
   self.c.received=time.time()
   client=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=3)
   try:
    client.request(method,'/api/v1/power' if power else '/api/v1/controls',body=json.dumps(value) if value is not None else None,headers={'X-KPA-Feed-Token':token} if token else {})
    response=client.getresponse();return response.status,json.loads(response.read())
   finally:client.close()
  try:
   token=request()[1]['control_token'];original=dict(id='original-request-001122',generation=self.c.generation,expected_operate=False,action='operate')
   if power:original=dict(id='original-request-001122',generation=self.c.generation,expected_status='live',action='power_off',confirmed=True)
   with patch.object(self.c,'action',return_value={'status':'queued','id':'fake-action'}) as action:
    if kind=='uncertain':action.side_effect=RuntimeError('Synthetic dispatch failure')
    first=request('POST',original,token)
    self.assertEqual(first[0],400 if kind=='uncertain' else 200)
    immediate=request('POST',original,token);self.assertEqual(immediate[0],200);self.assertEqual(action.call_count,1)
    # Exceed the old eviction threshold. Rejected IDs must not erase accepted
    # or uncertain receipts; accepted traffic must also fail closed at capacity.
    for i in range(140):
     value=dict(original,id=f'pressure-request-{i:016d}')
     if kind!='accepted':value['generation']='wrong-generation'
     status,result=request('POST',value,token)
     if kind=='accepted' and i<127:self.assertEqual(status,200)
     else:self.assertEqual(status,400)
    expected=128 if kind=='accepted' else 1
    self.assertEqual(action.call_count,expected)
    code,receipt=request('POST',original,token);self.assertEqual(code,200)
    self.assertEqual(action.call_count,expected,'A spent ID was dispatched again')
    self.assertEqual(receipt,immediate[1],'Original receipt must remain intact')
    self.assertEqual(request('POST',dict(original,action='standby'),token)[0],400)
    code,result=request('POST',dict(original,id='new-request-after-capacity'),token)
    self.assertEqual(code,400);self.assertIn('capacity',result['error'].lower())
    self.assertEqual(action.call_count,expected)
  finally:server.shutdown();server.server_close();thread.join(3)
 def test_accepted_receipt_survives_rejected_request_pressure(self):self.receipt_pressure('rejected')
 def test_accepted_receipt_survives_accepted_request_pressure(self):self.receipt_pressure('accepted')
 def test_uncertain_receipt_is_not_replayed_after_capacity_pressure(self):self.receipt_pressure('uncertain')

 def test_power_receipt_survives_rejected_request_pressure(self):self.receipt_pressure('rejected',power=True)
 def test_power_receipt_survives_accepted_request_pressure(self):self.receipt_pressure('accepted',power=True)
 def test_power_uncertain_receipt_survives_capacity_pressure(self):self.receipt_pressure('uncertain',power=True)
