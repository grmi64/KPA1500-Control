const assert=require('assert/strict'),{color,apply,bands}=require('../Sources/kpa_meter_colors.js');
for(const theme of ['dark','light']){
 const green=color('temperature',20,theme),yellow=color('temperature',75,theme),red=color('temperature',100,theme);
 assert.equal(color('temperature',65,theme),green);assert.equal(color('temperature',66,theme),yellow);assert.equal(color('temperature',85,theme),yellow);assert.equal(color('temperature',86,theme),red);
 assert.equal(color('swr',1,theme),green);assert.equal(color('swr',2.1,theme),yellow);assert.equal(color('swr',3,theme),red);assert.notEqual(color('swr',1.5,theme),green);
 assert.equal(color('power',1000,theme),green);assert.equal(color('power',1500,theme),yellow);assert.equal(color('power',1600,theme),red);assert.equal(color('power',null,theme),'');
 const n={style:{}},bar={style:{}};apply(n,bar,'power',1000,theme);assert.ok(Math.abs(parseFloat(bar.style.width)-1000/1900*100)<1e-9);assert.equal(bar.style.backgroundSize,'190% 100%');apply(n,bar,'power',null,theme);assert.equal(n.style.color,'');assert.equal(bar.style.width,'0%');
}
assert.equal(bands.power.max,1900);console.log('PASS: meter color thresholds, blends, anchored scales, light/dark contrast and missing-data clearing.');

for(const [watts,width] of [[0,0],[950,50],[1900,100],[2100,100]]){const bar={style:{}};apply(null,bar,'power',watts);assert.equal(parseFloat(bar.style.width),width);}
const fs=require('fs'),html=fs.readFileSync('Sources/index.html','utf8'),app=fs.readFileSync('Sources/app.js','utf8');assert.match(html,/aria-label="Forward power"[^>]*aria-valuemax="1900"/);assert.match(html,/<span>950<\/span><span>1,900 W<\/span>/);assert.match(app,/live\?'CONNECTED'/);
