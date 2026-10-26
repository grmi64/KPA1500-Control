const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const nodes=new Map(),$=id=>{if(!nodes.has(id))nodes.set(id,{dataset:{},textContent:'',disabled:false});return nodes.get(id)};
const power=$('powerButton');const c={$ ,busy:false,snapshot:null,document:{querySelectorAll:()=>[power]}};vm.createContext(c);
const s=fs.readFileSync('Sources/app.js','utf8');vm.runInContext(s.slice(s.indexOf('function paintControls()'),s.indexOf('function number(')),c);
function paint(state,connection={mode:'usb',port:'/dev/cu.test'},actions=[]){c.snapshot={state:{status:'live',transmitting:false,forward_watts:0,tuning:false,...state},connection,actions};c.paintControls();}
paint({});assert.equal(power.textContent,'Power Off');assert.equal(power.disabled,false);
for(const state of [{transmitting:true},{transmitting:null},{forward_watts:1},{tuning:true},{status:'stale'}]){paint(state);assert.equal(power.disabled,true);}
paint({status:'powered_off'});assert.equal(power.textContent,'Power On');assert.equal(power.disabled,false);
paint({status:'disconnected'},{mode:'tcp',wake_mac:''});assert.equal(power.disabled,true);
paint({status:'disconnected'},{mode:'tcp',wake_mac:'54:10:EC:14:75:22'});assert.equal(power.disabled,false);
paint({status:'connecting'});assert.equal(power.disabled,true);
paint({},undefined,[{status:'queued'}]);assert.equal(power.disabled,true);
const html=fs.readFileSync('Sources/index.html','utf8');assert(html.includes('class="control-row power-row"'));assert(html.includes('id="powerDialog"'));assert(s.includes("else if(button.dataset.action==='power_off')$('powerDialog').showModal()"));assert(s.includes("control('power_off',true)"));
console.log('PASS: power labels, RF/tuning/stale/pending guards, disconnected wake prerequisites and confirmation dialog.');
