const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync('Sources/app.js','utf8');
const html=fs.readFileSync('Sources/index.html','utf8');
const nodes=new Map();
const $=id=>{if(!nodes.has(id))nodes.set(id,{dataset:{},disabled:false,hidden:true,value:'',setAttribute(){}});return nodes.get(id);};
const buttons=['powerButton','operate','standby','tune','cancelTune','fan1','ant1','fault'].map(id=>$(id));
buttons.forEach((node,i)=>node.dataset.action=['power_on','operate','standby','tune','cancel_tune','fan_1','antenna_1','clear_fault'][i]);
let requestCount=0,messageCount=0,confirmResult=false,resolveRequest,mode='simulation';
const c={$ ,busy:false,snapshot:null,connectionFields:()=>({mode:'tcp',host:'192.0.2.18',tcp_port:1500}),message(){messageCount++;},api:async()=>{requestCount++;},document:{body:{inert:false},querySelectorAll:()=>buttons},window:{confirm:()=>confirmResult,pywebview:{api:{launch_info:async()=>({mode,allowed:true}),finish_launch_mode:async()=>{messageCount++;},request_launch_mode:value=>{requestCount++;assert.equal(value.confirmed,true);assert.equal(value.connection.host,'192.0.2.18');return new Promise(resolve=>resolveRequest=resolve);}}}}};
vm.createContext(c);
vm.runInContext(source.slice(source.indexOf('let windowsLaunch=null;'),source.indexOf('let prefs=')),c);
vm.runInContext(source.slice(source.indexOf('function paintControls()'),source.indexOf('function number(')),c);
vm.runInContext(source.slice(source.indexOf('async function control('),source.indexOf("document.querySelectorAll('[data-action]').forEach")),c);
(async()=>{
 for(mode of ['simulation','read-only','hardware']){
  await c.setupWindowsLaunch();assert.equal($('launchPanel').hidden,false);assert.equal($('accessNotice').hidden,mode!=='read-only');assert.equal($('launchMode').value,mode);
  assert.equal($('simulatorConnection').hidden,mode!=='simulation');assert.equal($('simulatorConnection').disabled,mode!=='simulation');
  assert.equal($('autoConnectSetting').hidden,true);assert.match($('connectionPolicy').textContent,/open disconnected/);
  assert.equal($('applyLaunchMode').disabled,false);
  if(mode==='read-only')assert.match($('accessNotice').textContent,/READ-ONLY.*disabled/);
  else assert.equal($('accessNotice').textContent,'','No duplicate simulation banner or hardware instructions above meters');
 }
 const before=requestCount;await $('applyLaunchMode').onclick();assert.equal(requestCount,before,'Cancel must never call native bridge');
 confirmResult=true;const pending=$('applyLaunchMode').onclick();await Promise.resolve();const beforeMessage=messageCount;
 assert.equal(requestCount,before+1);assert.equal(messageCount,beforeMessage,'No close signal before native acknowledgement');
 resolveRequest({reopening:true});await pending;assert.equal(messageCount,beforeMessage+1);assert.equal($('applyLaunchMode').disabled,true);
 c.window.pywebview.api.launch_info=async()=>({mode:'simulation',allowed:false});await c.setupWindowsLaunch();assert.equal($('applyLaunchMode').disabled,true);
 for(const status of ['live','powered_off','disconnected','error','stale']){
  c.snapshot={read_only:true,manual_connect:true,actions:[],connection:{mode:'tcp',wake_mac:'54:10:EC:14:75:22'},state:{status,transmitting:false,forward_watts:0,tuning:false,fault_code:'00',operate:false,atu_enabled:true,fan_minimum:0,fan_speed:0}};
  c.paintControls();for(const button of [...buttons,$('demoTx'),$('fanMinimum')])assert.equal(button.disabled,true,button.dataset.action||'other read-only control');
  assert.equal($('connect').disabled,false,'Healthy read-only service permits explicit Connect');
  if(status==='live')assert.equal($('disconnect').disabled,false);
  const calls=requestCount;await c.control('power_on');await c.control('operate');assert.equal(requestCount,calls,'Programmatic controls blocked too');
 }
 // A healthy service must allow cleanup after a reader error or terminal exit.
 for(const status of ['error','disconnected']){
  c.snapshot={read_only:true,reader_present:true,actions:[],connection:{mode:'tcp'},state:{status}};
  c.paintControls();assert.equal($('disconnect').disabled,false,'Dead reader ownership must be releasable');
  for(const button of buttons)assert.equal(button.disabled,true);
 }
 c.snapshot.reader_present=false;c.snapshot.state.status='disconnected';c.paintControls();assert.equal($('disconnect').disabled,true);
 c.snapshot.reader_present=true;c.snapshot.local_service_unavailable=true;c.paintControls();assert.equal($('disconnect').disabled,true,'A lost local service still cannot receive requests');
 // The permanent access notice is outside Full-only containers and collapsible connection sections.
 assert.match(html,/<div id="accessNotice" class="demo-banner" role="status" hidden><\/div>/);
 assert.match(html,/<div id="connectionContent"><section id="launchPanel" class="launch-settings" hidden>/);
 assert.ok(html.indexOf('id="launchPanel"')>html.indexOf('class="meter-grid"'),'Mode settings belong after the instruments');
 assert.equal((html.match(/id="host"/g)||[]).length,1,'Reuse ordinary endpoint fields');
 assert.equal((html.match(/id="port"/g)||[]).length,1);
 console.log('PASS: explicit launch modes, cancel/acknowledgement ordering, permanent notices, reused endpoint fields and read-only controls/API guards.');
})().catch(error=>{console.error(error);process.exitCode=1;});
