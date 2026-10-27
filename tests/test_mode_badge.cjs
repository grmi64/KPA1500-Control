const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const source=fs.readFileSync('Sources/app.js','utf8'),node={dataset:{}};
const c={$:()=>node};vm.createContext(c);vm.runInContext(source.slice(source.indexOf('function paintMode('),source.indexOf('function paint(){')),c);
for(const [state,label,mode] of [[{status:'live',operate:true},'OPERATE','operate'],[{status:'live',operate:false},'STANDBY','standby'],[{status:'live',operate:null},'MODE UNKNOWN','unknown'],...['stale','error','disconnected','connecting'].map(status=>[{status,operate:true},'MODE UNKNOWN','unknown'])]){c.paintMode(state);assert.equal(node.textContent,label);assert.equal(node.dataset.mode,mode);}
const html=fs.readFileSync('Sources/index.html','utf8');assert.equal((html.match(/id="mode"/g)||[]).length,1);assert(html.match(/<header>[\s\S]*id="mode"[\s\S]*id="connectionStatus"[\s\S]*<\/header>/));
console.log('PASS: reported mode, stale/unknown clearing, and shared header badge.');
