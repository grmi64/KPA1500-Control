import http.client,json,pathlib,sys,tempfile,threading,time,unittest
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'Sources'))
from engine import Controller
from server import handler_for
from http.server import ThreadingHTTPServer

class SharedPowerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.c=Controller(pathlib.Path(self.tmp.name)/'settings.json')
 def tearDown(self):self.tmp.cleanup()
 def ready(self):
  self.c.config.update(share_readings=True,share_power=True,mode='simulator')
  self.c.state=dict(status='live',age_seconds=0,transmitting=False,tuning=False,forward_watts=0,demo=True);self.c.received=time.time()
 def test_default_persistence_and_offline_exclusion(self):
  self.assertFalse(self.c.config['share_power'])
  with self.assertRaises(PermissionError):self.c.shared_power()
  self.c.save_settings(dict(share_readings=True,share_power=True));self.assertTrue(Controller(self.c.settings).config['share_power'])
  self.c.save_settings(dict(share_readings=False));self.assertFalse(self.c.config['share_power'])
  self.assertFalse(Controller(self.c.settings,offline_only=True).config['share_power'])
 def test_guards_and_no_connection_settings_exposed(self):
  self.ready();self.assertTrue(self.c.shared_power()['can_off']);self.assertNotIn('connection',self.c.shared_power())
  for change in ({'transmitting':True},{'transmitting':None},{'tuning':True},{'forward_watts':1},{'forward_watts':None},{'age_seconds':5},{'status':'error'}):
   self.ready();self.c.state.update(change);self.assertFalse(self.c.shared_power()['can_off'])
  for attr in ('read_only','offline_only','launch_pending'):
   self.ready();setattr(self.c,attr,True);self.assertFalse(self.c.shared_power()['can_off']);setattr(self.c,attr,False)
  self.ready();self.c.state['status']='powered_off';self.assertTrue(self.c.shared_power()['can_on'])
  self.c.config.update(mode='tcp',wake_mac='');self.assertFalse(self.c.shared_power()['can_on'])
 def test_exact_action_and_connection_binding(self):
  self.ready();value=dict(action='power_off',confirmed=True,generation=self.c.generation,expected_status='live')
  with patch.object(self.c,'action',return_value={'status':'queued'}) as action:
   self.c.shared_power_action(value);action.assert_called_once_with(dict(action='power_off',generation=self.c.generation,confirm_power_off=True))
   for change in ({'confirmed':False},{'generation':'old'},{'expected_status':'powered_off'},{'action':'operate'}):
    with self.assertRaises(ValueError):self.c.shared_power_action(dict(value,**change))
   self.assertEqual(action.call_count,1)
 def test_http_backend_token_origin_size_revocation_and_deduplication(self):
  self.ready();handler=handler_for(self.c,'ui-token',simulate_discovery=True)
  server=ThreadingHTTPServer(('127.0.0.1',0),handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  def request(method='GET',body=None,headers=None):
   client=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=2)
   client.request(method,'/api/v1/power',body=json.dumps(body) if body is not None else None,headers=headers or {})
   response=client.getresponse();result=(response.status,json.loads(response.read()));client.close();return result
  try:
   code,data=request();self.assertEqual(code,200);token=data['control_token'];self.assertNotEqual(token,'ui-token')
   self.assertEqual(request(headers={'Origin':'http://evil.example'})[0],403)
   self.assertEqual(request(headers={'Host':'evil.example'})[0],403)
   value=dict(action='power_off',confirmed=True,generation=self.c.generation,expected_status='live',id='offline-test-request-001')
   headers={'X-KPA-Feed-Token':token}
   self.assertEqual(request('POST',value)[0],403)
   self.assertEqual(request('POST',value,dict(headers,Origin='http://127.0.0.1'))[0],403)
   self.assertEqual(request('POST',{'id':'x'*2048},headers)[0],400)
   with patch.object(self.c,'action',return_value={'status':'queued','id':'fake'}) as action:
    for _ in range(2):self.assertTrue(request('POST',value,headers)[1]['queued'])
    action.assert_called_once()
    self.assertEqual(request('POST',dict(value,action='power_on'),headers)[0],400)
    self.c.config['share_power']=False
    self.assertEqual(request('POST',value,headers)[0],403);self.assertEqual(request()[0],403)
  finally:server.shutdown();server.server_close();thread.join(2)
