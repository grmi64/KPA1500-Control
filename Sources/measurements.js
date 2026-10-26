/* Display ranges only. Reads cached telemetry; never requests equipment data. */
(function(root){'use strict';
const choices={
 reflected:{label:'REFLECTED POWER',key:'reflected_watts',unit:'W',unitLabel:'WATTS',min:0,max:100,digits:1},
 input:{label:'INPUT POWER',key:'input_watts',unit:'W',unitLabel:'WATTS',min:0,max:100,digits:1},
 current:{label:'PA CURRENT',key:'current_a',unit:'A',unitLabel:'AMPS',min:0,max:100,digits:1},
 voltage:{label:'PA VOLTAGE',key:'voltage_v',unit:'V',unitLabel:'VOLTS',min:0,max:60,digits:1},
 frequency:{label:'FREQUENCY',key:'frequency_khz',unit:'MHz',unitLabel:'MEGAHERTZ',min:0,max:54.2,digits:3},
 bypass_swr:{label:'BYPASS SWR',key:'bypass_swr',unit:':1',unitLabel:'RATIO',min:1,max:5,digits:2}
};
function selection(value){return Object.prototype.hasOwnProperty.call(choices,value)?value:'reflected';}
function reading(value,state){const id=selection(value),spec=choices[id];let n=state.status==='live'?state[spec.key]:null;if(id==='frequency')n=typeof n==='number'&&n>0?n/1000:null;if(id==='bypass_swr'&&!(n>=1))n=null;if(typeof n!=='number'||!Number.isFinite(n)||n<0)n=null;return {id,...spec,value:n,width:n===null?0:Math.min(100,Math.max(0,(n-spec.min)/(spec.max-spec.min)*100))};}
const api={choices,selection,reading};if(typeof module!=='undefined')module.exports=api;root.KPAMeasurements=api;
})(globalThis);
