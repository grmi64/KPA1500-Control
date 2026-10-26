const assert=require('assert/strict'),{color,apply,bands}=require('../Sources/kpa_meter_colors.js');
for(const theme of ['dark','light']){
 const green=color('temperature',20,theme),yellow=color('temperature',75,theme),red=color('temperature',100,theme);
 assert.equal(color('temperature',65,theme),green);assert.equal(color('temperature',66,theme),yellow);assert.equal(color('temperature',85,theme),yellow);assert.equal(color('temperature',86,theme),red);
 assert.equal(color('swr',1,theme),green);assert.equal(color('swr',2.1,theme),yellow);assert.equal(color('swr',3,theme),red);assert.notEqual(color('swr',1.5,theme),green);
 assert.equal(color('power',1000,theme),green);assert.equal(color('power',1500,theme),yellow);assert.equal(color('power',1600,theme),red);assert.equal(color('power',null,theme),'');
 const n={style:{}},bar={style:{}};apply(n,bar,'power',1000,theme);assert.equal(bar.style.width,'50%');assert.equal(bar.style.backgroundSize,'200% 100%');apply(n,bar,'power',null,theme);assert.equal(n.style.color,'');assert.equal(bar.style.width,'0%');
}
assert.equal(bands.power.max,2000);console.log('PASS: meter color thresholds, blends, anchored scales, light/dark contrast and missing-data clearing.');
