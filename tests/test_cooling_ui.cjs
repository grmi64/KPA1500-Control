const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),source=fs.readFileSync('Sources/app.js','utf8'),nodes={};
const context={$:id=>nodes[id]||(nodes[id]={}),busy:false};vm.createContext(context);vm.runInContext(source.slice(source.indexOf('function paintCooling('),source.indexOf('function number(')),context);
const live={status:'live',fan_minimum:0,fan_speed:3,transmitting:false,forward_watts:0,tuning:false};
function paint(state,pending=false){context.paintCooling(state,pending);}
paint(live);assert.equal(nodes.fanMinimum.value,'0');assert.equal(nodes.fanMinimum.disabled,false);assert.equal(nodes.fanSpeed.textContent,'3');
for(const state of [{...live,status:'stale'},{...live,status:'disconnected'},{...live,fan_minimum:null},{...live,errors:{FC:'unsupported'}},{...live,transmitting:true},{...live,tuning:true},{...live,forward_watts:10}]){paint(state);assert.equal(nodes.fanMinimum.disabled,true);}
paint({...live,status:'stale'});assert.equal(nodes.fanMinimum.value,'');assert.equal(nodes.fanSpeed.textContent,'—');paint(live,true);assert.equal(nodes.fanMinimum.disabled,true);
assert(!source.includes("localStorage.setItem('fan"));assert.match(source,/cooling:'Cooling'/);console.log('PASS: cooling readback, unavailable/stale/RF/tuning/pending guards and no restored fan setting.');
