const { chromium } = require('playwright'); const fs=require('fs');
const base=fs.readFileSync('/home/user/Motion1/logo/logo.html','utf8');
const V={
 a:`<div class="ring"></div><div class="g" style="font-size:620px;letter-spacing:-40px;margin-left:-20px">?!</div>`,
 b:`<svg style="position:absolute;left:50%;top:52%;transform:translate(-50%,-50%);filter:drop-shadow(0 0 40px rgba(198,244,50,.5)) drop-shadow(0 20px 30px rgba(0,0,0,.6))" width="700" height="640" viewBox="0 0 700 640">
   <path d="M90 40 H610 a60 60 0 0 1 60 60 V430 a60 60 0 0 1 -60 60 H330 L200 600 L215 490 H90 a60 60 0 0 1 -60 -60 V100 a60 60 0 0 1 60 -60z" fill="#c6f432"/></svg>
   <div class="g" style="top:48%;font-size:400px;color:#06080d;text-shadow:none;letter-spacing:-26px;margin-left:-14px">?!</div>`,
 c:`<div class="ring" style="border-width:0;box-shadow:none;background:conic-gradient(from 200deg,#c6f432,#5aa9ff,#c6f432);-webkit-mask:radial-gradient(circle, transparent 455px, #000 457px)"></div>
   <svg style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%)" width="1080" height="1080"><circle cx="540" cy="540" r="330" fill="#c6f432"/></svg>
   <div class="g" style="font-size:470px;color:#06080d;text-shadow:none;letter-spacing:-30px;margin-left:-14px;top:51%">?!</div>`
};
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1080}});
for(const k in V){fs.writeFileSync('/home/user/Motion1/logo/_v.html',base.replace('VARIANT',V[k]));await p.goto('file:///home/user/Motion1/logo/_v.html');await p.evaluate(()=>document.fonts.load('400px Anton'));await p.waitForTimeout(300);
await p.screenshot({path:`/home/user/Motion1/logo/logo_${k}.png`,omitBackground:true});}
await b.close();})();
