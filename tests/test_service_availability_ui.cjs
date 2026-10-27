const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync('Sources/app.js','utf8'),nodes=new Map();
const $=id=>{if(!nodes.has(id))nodes.set(id,{dataset:{},disabled:false,setAttribute(){}});return nodes.get(id);};
const buttons=['powerButton','operate','standby','tune','cancel_tune'].map(id=>$(id));
buttons.forEach((node,i)=>node.dataset.action=['power_on','operate','standby','tune','cancel_tune'][i]);
let response,unavailable=false,calls=0,scheduled=0;
const c={$,busy:false,polling:false,snapshot:null,message(){},setTimeout(fn,ms){assert.equal(ms,300);scheduled++;},document:{querySelectorAll:()=>buttons},api:async()=>{calls++;if(unavailable)throw Error('offline');return structuredClone(response);},paint(){c.paintControls();}};
vm.createContext(c);
vm.runInContext(source.slice(source.indexOf('function paintControls()'),source.indexOf('function number(')),c);
vm.runInContext(source.slice(source.indexOf('async function control('),source.indexOf("document.querySelectorAll('[data-action]').forEach")),c);
vm.runInContext(source.slice(source.indexOf('async function poll()'),source.indexOf('applyView();poll();')),c);
const healthy=status=>({offline_only:true,connection:{mode:'simulator'},actions:[],state:{status,demo:true,transmitting:false,forward_watts:0,tuning:false,operate:false,fault_code:'00',atu_enabled:true}});
(async()=>{
 // Initial service failure must also leave backend controls disabled.
 unavailable=true;await c.poll();assert.equal($('powerButton').disabled,true);assert.equal($('demoTx').disabled,true);assert.equal($('connect').disabled,true);
 response=healthy('live');unavailable=false;await c.poll();assert.equal($('powerButton').disabled,false);assert.equal($('demoTx').disabled,false);
 // Run the real polling failure handler and shared Full/Compact control renderer.
 for(let cycle=0;cycle<2;cycle++){unavailable=true;await c.poll();
  assert.equal(c.snapshot.state.message,'Local amplifier service unavailable.');assert.equal(c.snapshot.offline_only,true);
  assert.equal(c.snapshot.connection.mode,'simulator');assert.equal(c.snapshot.state.forward_watts,undefined);
  for(const node of [...buttons,$('demoTx'),$('disconnect'),$('connect'),$('fanMinimum')])assert.equal(node.disabled,true);
  const before=calls;await c.control('power_on');await c.control('demo_tx_on');assert.equal(calls,before); // queued/programmatic handlers cannot send either
  // A successful state response clears the frontend outage marker, even if the simulator is off.
  unavailable=false;response=healthy('powered_off');await c.poll();
  assert.equal($('powerButton').textContent,'Power On');assert.equal($('powerButton').disabled,false);assert.equal($('connect').disabled,false);assert.equal($('demoTx').disabled,true);
  response=healthy('disconnected');await c.poll();assert.equal($('powerButton').disabled,false);assert.equal($('connect').disabled,false);
  response=healthy('error');await c.poll();assert.equal($('powerButton').disabled,false); // healthy service reports simulator error
  response=healthy('live');await c.poll();assert.equal($('powerButton').textContent,'Power Off');assert.equal($('powerButton').disabled,false);assert.equal($('demoTx').disabled,false);
 }
 assert.equal(c.polling,false);assert.equal(scheduled,calls);
 console.log('PASS: actual polling outages disable backend controls, retain permanent simulation identity, and recover healthy simulator disconnect/power/live controls.');
})().catch(e=>{console.error(e);process.exitCode=1;});
