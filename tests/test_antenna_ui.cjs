const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync('Sources/app.js','utf8'),html=fs.readFileSync('Sources/index.html','utf8');
const buttons=['antenna_1','antenna_2'].map(action=>({dataset:{action},attrs:{},setAttribute(k,v){this.attrs[k]=v;}}));
const nodes=new Map(),$=id=>{if(!nodes.has(id))nodes.set(id,{});return nodes.get(id)};
const c={$ ,busy:false,snapshot:null,document:{querySelectorAll:()=>buttons}};vm.createContext(c);
vm.runInContext(source.slice(source.indexOf('function paintControls()'),source.indexOf('function number(')),c);
function paint(overrides={},actions=[]){c.snapshot={state:{status:'live',transmitting:false,forward_watts:0,tuning:false,antenna:1,...overrides},actions};c.paintControls();}
paint();assert.equal(buttons[0].attrs['aria-pressed'],'true');assert.equal(buttons[0].disabled,true);assert.equal(buttons[1].disabled,false);
paint({antenna:2});assert.equal(buttons[1].attrs['aria-pressed'],'true');assert.equal(buttons[0].attrs['aria-pressed'],'false');assert.equal(buttons[0].disabled,false);
paint({antenna:null});assert(buttons.every(b=>b.attrs['aria-pressed']==='false'));
for(const state of [{transmitting:true},{forward_watts:10},{transmitting:null},{tuning:true},{status:'stale'},{status:'error'},{status:'disconnected'}]){paint(state);assert(buttons.every(b=>b.disabled),JSON.stringify(state));}
paint({status:'stale'});assert(buttons.every(b=>b.attrs['aria-pressed']==='false'));
paint({},[{status:'queued'}]);assert(buttons.every(b=>b.disabled));c.busy=true;paint();assert(buttons.every(b=>b.disabled));c.busy=false;
const controls=html.match(/<section class="controls"[\s\S]*?<\/section>/)[0];
assert(controls.includes('data-action="antenna_1"'));assert(controls.includes('data-action="antenna_2"'));assert(!controls.includes('full-only'));assert(!html.includes('antenna_next'));
let sent=[];c.control=action=>sent.push(action);vm.runInContext(source.slice(source.indexOf("document.querySelectorAll('[data-action]').forEach(button=>button.onclick"),source.indexOf("$('tuneCancel')")),c);
buttons[0].onclick();buttons[1].onclick();assert.deepEqual(sent,['antenna_1','antenna_2']);
console.log('PASS: explicit antenna actions, reported selection, full/compact visibility, RF/tuning/stale/pending guards.');
