const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync('Sources/app.js','utf8'),node={textContent:'',dataset:{}};
const containers={routineMessage:{appendChild(n){n.parentElement=this;}},importantMessage:{appendChild(n){n.parentElement=this;}}};
const c={$:id=>containers[id]||node,lastAction:'previous',snapshot:{actions:[{id:'previous',status:'confirmed',message:'Standby confirmed.'}]}};vm.createContext(c);
vm.runInContext(source.slice(source.indexOf('function message('),source.indexOf('async function api(')),c);
// Execute the real message-selection code without polling or hardware.
const start=source.indexOf('\n if(',source.indexOf('if(!initialized)'));
const original=source.slice(start,source.indexOf("\n $('sampleAge')",start));
function paint(state){c.state=state;c.live=state.status==='live';vm.runInContext(original,c);}
paint({status:'error',message:'Amplifier stopped responding. Connection closed; reconnect when ready.'});
assert.equal(node.textContent,'Amplifier stopped responding. Connection closed; reconnect when ready.');assert.equal(node.dataset.error,'true');
paint({status:'stale',message:'Amplifier readings are stale.'});assert.equal(node.textContent,'Amplifier readings are stale.');assert.equal(node.dataset.error,'true');assert.equal(node.parentElement,containers.importantMessage);
paint({status:'connecting',message:'Identifying amplifier…'});assert.equal(node.textContent,'Identifying amplifier…');
paint({status:'disconnected',message:'Amplifier disconnected.'});assert.equal(node.textContent,'Amplifier disconnected.');
paint({status:'live'});assert.equal(node.parentElement,containers.routineMessage);assert.equal(node.textContent,'Standby confirmed.');assert.equal(node.dataset.error,'false');
c.snapshot.actions[0]={id:'previous',status:'failed',message:'Control was not confirmed.'};paint({status:'live'});assert.equal(node.textContent,'Control was not confirmed.');assert.equal(node.dataset.error,'true');
paint({status:'error',message:'Local amplifier service unavailable.'});assert.equal(node.textContent,'Local amplifier service unavailable.');
console.log('PASS: connection loss, stale and startup notices override older actions; live confirmation/failure feedback remains intact.');

assert.equal(node.parentElement,containers.importantMessage);
