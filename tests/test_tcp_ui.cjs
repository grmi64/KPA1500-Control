const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const nodes=new Map(),$=id=>{if(!nodes.has(id))nodes.set(id,{value:'',checked:false,disabled:false,hidden:false,textContent:''});return nodes.get(id)};
let calls=[],resolve;const c={$: $,busy:false,snapshot:null,lastAction:null,paint(){},message(){},api:async(name,value)=>{calls.push({name,value});return {state:{status:'connecting'}}}};vm.createContext(c);
const source=fs.readFileSync('Sources/app.js','utf8');vm.runInContext(source.slice(source.indexOf('function connectionFields'),source.indexOf('async function control')),c);
(async()=>{
 $('port').value='/dev/cu.test';$('baud').value='230400';$('host').value=' 192.168.0.18 ';$('tcpPort').value='1500';
 $('connectionType').value='tcp';$('connectionType').onchange();assert.equal($('hostField').hidden,false);assert.equal($('host').disabled,false);assert.equal($('port').disabled,true);assert.equal($('refreshPorts').disabled,true);
 await $('connect').onclick();assert.equal(calls[0].value.mode,'tcp');assert.equal(calls[0].value.host,'192.168.0.18');assert.equal(calls[0].value.tcp_port,1500);
 $('autoConnect').checked=true;await $('autoConnect').onchange();assert.equal(calls[1].name,'settings');assert.equal(calls[1].value.mode,'tcp');assert.equal(calls[1].value.auto_connect,true);
 $('connectionType').value='usb';$('connectionType').onchange();assert.equal($('hostField').hidden,true);assert.equal($('port').disabled,false);await $('connect').onclick();assert.equal(calls[2].value.mode,'usb');assert.equal(calls[2].value.port,'/dev/cu.test');
 $('connectionType').value='simulator';$('connectionType').onchange();assert.equal($('autoConnect').disabled,true);assert.equal($('hostField').hidden,true);
 console.log('PASS: USB/TCP field switching, trimmed endpoint, Connect payload, saved startup choice and simulator startup guard.');
})().catch(e=>{console.error(e);process.exitCode=1});
