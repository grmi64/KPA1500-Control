/* Display-only ranges, independent of amplifier protection and USB/CAT timing. */
(function(root){
 'use strict';
 const bands={temperature:{min:0,max:110,stops:[[0,0],[65,0],[66,1],[85,1],[86,2],[110,2]]},swr:{min:1,max:5,stops:[[1,0],[1.45,0],[1.55,1],[2.1,1],[2.2,2],[5,2]]},power:{min:0,max:1900,stops:[[0,0],[1380,0],[1420,1],[1500,1],[1520,2],[1900,2]]}};
 const palettes={dark:[[91,216,161],[244,200,79],[245,105,96]],light:[[20,119,77],[145,101,0],[184,45,39]]};
 function valid(value){return typeof value==='number'&&Number.isFinite(value);}
 function color(kind,value,theme='dark'){
  if(!valid(value))return '';const stops=bands[kind].stops,palette=palettes[theme]||palettes.dark;
  for(let i=1;i<stops.length;i++)if(value<=stops[i][0]){
   const [a,ai]=stops[i-1],[b,bi]=stops[i],t=Math.max(0,Math.min(1,(value-a)/(b-a)));
   return 'rgb('+palette[ai].map((v,j)=>Math.round(v+(palette[bi][j]-v)*t)).join(',')+')';
  }
  return 'rgb('+palette[2].join(',')+')';
 }
 function apply(number,bar,kind,value,theme='dark'){
  const range=bands[kind],usable=valid(value),tone=color(kind,value,theme);
  if(number&&number.style.color!==tone)number.style.color=tone;
  if(!bar)return;
  const fraction=usable?Math.max(0,Math.min(1,(value-range.min)/(range.max-range.min))):0;
  const width=fraction*100+'%';if(bar.style.width!==width)bar.style.width=width;
  const palette=palettes.dark;
  const gradient='linear-gradient(90deg,'+range.stops.map(([v,i])=>'rgb('+palette[i].join(',')+') '+((v-range.min)/(range.max-range.min)*100)+'%').join(',')+')';
  if(bar.style.backgroundImage!==gradient)bar.style.backgroundImage=gradient;
  // Anchor the gradient to the whole scale, not to the changing fill width.
  bar.style.backgroundSize=(fraction?100/fraction:100)+'% 100%';
 }
 const api={bands,color,apply};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.KPAMeterColors=api;
})(typeof window!=='undefined'?window:this);
