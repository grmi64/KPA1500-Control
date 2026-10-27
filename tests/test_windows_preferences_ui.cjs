const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync('Sources/app.js','utf8');
const queueSource=source.slice(source.indexOf('let nativeUpdates='),source.indexOf('window.addEventListener?.'));
const tick=()=>new Promise(setImmediate);
function setup(api){const errors=[],c={document:{body:{inert:false}},prefs:{theme:'dark',sections:{faults:true}},window:{pywebview:{api}},message:text=>errors.push(text)};vm.createContext(c);vm.runInContext(queueSource,c);return {c,errors};}
(async()=>{
 const displays=[],saves=[];let stored;
 const {c}=setup({display_window:options=>new Promise(resolve=>displays.push({options,resolve})),save_preferences:value=>new Promise(resolve=>saves.push({value,resolve:()=>{stored=value;resolve();}}))});
 const first=c.postWindowsPreferences({compact:false,alwaysOnTop:false});c.prefs.theme='light';c.prefs.sections.faults=false;const second=c.postWindowsPreferences({compact:true,alwaysOnTop:false});const closing=c.beginNativeClose();assert.equal(c.document.body.inert,true);c.prefs.theme='ignored_after_close';c.postWindowsPreferences({compact:false,alwaysOnTop:true});
 await tick();assert.equal(displays.length,1);assert.equal(saves.length,0);
 displays[0].resolve();await tick();assert.equal(saves.length,1);assert.equal(saves[0].value.theme,'dark');assert.equal(saves[0].value.sections.faults,true,'Snapshot nested settings at enqueue time');assert.equal(displays.length,1,'Second update waits for first persistence');
 saves[0].resolve();await first;await tick();assert.equal(displays.length,2);assert.equal(displays[1].options.compact,true);displays[1].resolve();await tick();saves[1].resolve();await second;assert.equal(stored.theme,'light');assert.equal(stored.sections.faults,false);assert.equal((await closing).ready,true);assert.equal(displays.length,2,'Close freezes further display/save requests');
 const attempts=[];const failed=setup({display_window:async()=>{},save_preferences:async value=>{attempts.push(value.theme);if(attempts.length===1)throw Error('Disk busy');}});
 const a=failed.c.postWindowsPreferences({compact:false,alwaysOnTop:false});failed.c.prefs.theme='light';const b=failed.c.postWindowsPreferences({compact:false,alwaysOnTop:false});await Promise.all([a,b]);assert.deepEqual(attempts,['dark','light']);assert.equal(failed.errors.length,1,'Save failures are visible and do not strand later updates');
 const retry=setup({display_window:async()=>{},save_preferences:async()=>{throw Error('Disk full');}});
 await retry.c.postWindowsPreferences({compact:false,alwaysOnTop:false});assert.equal((await retry.c.beginNativeClose()).ready,false);retry.c.cancelNativeClose('Disk full');assert.equal(retry.c.document.body.inert,false);retry.c.window.pywebview.api.save_preferences=async()=>{};assert.equal((await retry.c.beginNativeClose()).ready,true,'A later Close retries the failed preference write without requiring another UI change');
 // Execute the actual badge/banner logic for disconnected, failed-service,
 // stale and normal states; never contact the service or a device.
 const nodes={connectionStatus:{dataset:{}},demoBanner:{hidden:true}};
 const labelSource=source.slice(source.indexOf('const simulated='),source.indexOf(" number('forward'",source.indexOf('const simulated=')));
 const labels={$:id=>nodes[id]};vm.createContext(labels);
 for(const status of ['disconnected','stale','error']){Object.assign(labels,{snapshot:{offline_only:true},state:{status},live:false});vm.runInContext('{'+labelSource+'}',labels);assert.equal(nodes.connectionStatus.textContent,'SIMULATOR');assert.equal(nodes.demoBanner.hidden,false);assert.equal(nodes.connectionStatus.dataset.state,status);}
 Object.assign(labels,{snapshot:{offline_only:false},state:{status:'live',demo:false},live:true});vm.runInContext('{'+labelSource+'}',labels);assert.equal(nodes.connectionStatus.textContent,'CONNECTED');assert.equal(nodes.demoBanner.hidden,true);
 console.log('PASS: serialized native preference saves, snapshots, failure recovery and persistent simulation labeling.');
})().catch(error=>{console.error(error);process.exitCode=1;});
