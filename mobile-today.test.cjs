// State-transition tests using the real app and timetable data; no browser dependency.
// Rendering, layout and actual mobile resume events are verified in the preview.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {createEngine} = require('./timetable-engine.js');
const timetableData = JSON.parse(fs.readFileSync(__dirname+'/timetable.json','utf8'));
const appSource = fs.readFileSync(__dirname+'/app.js','utf8');
function session(iso, mobile=true, search=''){
 let now=Date.parse(iso);
 let mountedPreviews=0;
 const nodes=new Map(), documentEvents={}, windowEvents={};
 const node=key=>{
  if(!nodes.has(key))nodes.set(key,{
   hidden:true,innerHTML:'',textContent:'',dataset:{},
   setAttribute(){},append(){},focus(){document.activeElement=this;},scrollIntoView(){},
   contains(element){return element===this;},querySelector:node,
   classList:{toggle(){},add(){},contains(){return false;}}
  });
  return nodes.get(key);
 };
 const document={visibilityState:'visible',activeElement:null,body:node('body'),
  createElement:tag=>node('created-'+tag),querySelector:node,querySelectorAll:()=>[],
  addEventListener:(name,handler)=>{documentEvents[name]=handler;}};
 const context=vm.createContext({document,console,URLSearchParams,location:{search},
  window:{addEventListener:(name,handler)=>{windowEvents[name]=handler;}},
  Date:class extends Date{constructor(...args){super(...(args.length?args:[now]));}},
  matchMedia:()=>({matches:mobile}),IntersectionObserver:class{observe(){}},
  TimetableEngine:{createEngine},timetableData,siteConfig:{manualPdf:'user-manual.pdf'},
  CandidatePreview:{renderCards:()=>'',mount:()=>{mountedPreviews++;return {destroy(){mountedPreviews--;}};}},
  escapeHTML:String,clearSelection(){}});
 vm.runInContext(appSource,context);
 const run=code=>vm.runInContext(code,context);
 return {run,node,document,previews:()=>mountedPreviews,setTime:iso=>{now=Date.parse(iso);},
  event:(name)=>{(documentEvents[name]||windowEvents[name])();},
  state:()=>JSON.parse(run('JSON.stringify({day:chosenDay,date:observedDate,mode:viewMode,active:!!activeLesson,origin:classReturn,kind:selectedTarget?.kind,id:selectedTarget?.record.id,name:selectedTarget?.record.name})'))};
}
let checks=0;
function check(name,fn){fn();checks++;console.log('PASS '+name);}
check('Taiwan weekdays and weekend defaults for teacher and class queries',()=>{
 const days=['02','03','04','05','06','07','08'];
 days.forEach((day,index)=>{
  const s=session(`2026-11-${day}T01:00:00Z`);
  const expected=index<5?index+1:1;
  assert.equal(s.state().day,expected);
  for(const query of ["choose('teacher','黃隆偉',false)","choose('class','804',false)"]){
   s.run('chosenDay=5;viewMode="week"');s.run(query);
   assert.equal(s.state().day,expected);assert.equal(s.state().mode,'week');
  }
 });
});
check('Taiwan midnight is independent of the computer timezone',()=>{
 const s=session('2026-11-02T15:59:59Z');s.run("choose('class','804',false)");
 assert.equal(s.state().day,1);
 s.setTime('2026-11-02T16:00:00Z');s.run("choose('teacher','黃隆偉',false)");
 assert.equal(s.state().day,2);assert.equal(s.state().date,'2026-11-03');
});
check('A teacher deep link starts on today',()=>{
 const s=session('2026-11-04T01:00:00Z',true,'?teacher='+encodeURIComponent('黃隆偉'));
 assert.equal(s.state().name,'黃隆偉');assert.equal(s.state().day,3);
});
check('Same-day resume preserves manual day, mode and candidates',()=>{
 const s=session('2026-11-02T01:00:00Z');
 s.run("choose('teacher','黃隆偉',false);chosenDay=5;viewMode='week';openLesson(selectedTarget.record.lessons[0])");
 const before=s.state();s.event('visibilitychange');s.event('focus');s.event('pageshow');
 assert.deepEqual(s.state(),before);assert.equal(s.node('.candidate-panel').hidden,false);
});
for(const event of ['visibilitychange','focus','pageshow'])check('Cross-day '+event+' clears stale selection and candidates',()=>{
 const s=session('2026-11-02T15:59:59Z');
 s.run("choose('teacher','黃隆偉',false);viewMode='week';openLesson(selectedTarget.record.lessons[0])");
 s.document.activeElement=s.node('.candidate-panel');
 s.setTime('2026-11-02T16:00:00Z');
 assert.equal(s.state().day,1,'No midnight timer changes an active session');
 s.document.visibilityState='hidden';s.event(event);assert.equal(s.state().day,1);
 s.document.visibilityState='visible';s.event(event);
 assert.equal(s.state().day,2);assert.equal(s.state().mode,'week');assert.equal(s.state().name,'黃隆偉');
 assert.equal(s.state().active,false);assert.equal(s.node('.candidate-panel').hidden,true);
 assert.equal(s.previews(),0,'Cross-day reset destroys the old candidate controller');
 assert.equal(s.node('.candidate-panel').innerHTML,'');
 assert.equal(s.node('.lesson-summary').hidden,true);
 assert.equal(s.document.activeElement,s.node('created-section'));
 s.run('chosenDay=4');s.event(event);assert.equal(s.state().day,4,'Repeated resume events must not reset manual browsing');
});
check('Full calendar date detects a week away and year boundaries',()=>{
 for(const [before,after,expected] of [
  ['2026-11-02T01:00:00Z','2026-11-09T01:00:00Z',1],
  ['2026-12-31T15:59:59Z','2026-12-31T16:00:00Z',5],
  ['2026-11-06T15:59:59Z','2026-11-06T16:00:00Z',1]
 ]){
  const s=session(before);s.run("choose('class','804',false);chosenDay=4");
  s.setTime(after);s.event('pageshow');assert.equal(s.state().day,expected);
 }
});
check('Class drill-down and return retain explicit day and mode',()=>{
 const s=session('2026-11-02T01:00:00Z');
 s.run("choose('class','804',false);chosenDay=3;viewMode='week';openLesson(selectedTarget.record.lessons.find(l=>l.day===3&&l.period===4))");
 assert.equal(s.state().name,'林來進');assert.equal(s.state().day,3);assert.equal(s.state().active,true);
 assert.deepEqual(s.state().origin,{id:'804',day:3,mode:'week'});
 s.setTime('2026-11-03T01:00:00Z');s.event('visibilitychange');
 assert.equal(s.state().day,2);assert.equal(s.state().active,false);
 assert.deepEqual(s.state().origin,{id:'804',day:3,mode:'week'});
 s.run("chosenDay=5;viewMode='day';returnToClass()");
 assert.equal(s.state().id,'804');assert.equal(s.state().day,3);assert.equal(s.state().mode,'week');
 s.run("choose('class','701',false)");assert.equal(s.state().day,2);assert.equal(s.state().origin,null);
});
check('No selection and invalid targets are safe across date changes',()=>{
 const s=session('2026-11-02T01:00:00Z');s.setTime('2026-11-03T01:00:00Z');
 s.event('visibilitychange');assert.equal(s.state().day,2);
 s.run("chosenDay=5;choose('teacher','不存在',false)");assert.equal(s.state().day,5);
});
check('Blank timetable slots retain all periods; unknown schedules remain explicit',()=>{
 const s=session('2026-11-04T01:00:00Z');
 for(const query of ["choose('teacher','黃隆偉',false)","choose('class','804',false)"]){
  s.run(query);
  const daily=s.node('.schedule-day').innerHTML, weekly=s.node('.schedule-grid').innerHTML;
  assert.equal((daily.match(/class="day-slot"/g)||[]).length,8);
  assert.equal((weekly.match(/class="period-time"/g)||[]).length,8);
  assert.ok(!daily.includes('未排課')&&!weekly.includes('—'));
 }
 const partial=timetableData.teachers.find(t=>t.scheduleStatus==='partial');
 assert.ok(partial);
 s.run(`choose('teacher',${JSON.stringify(partial.name)},false)`);
 assert.ok(s.node('.schedule-day').innerHTML.includes('未提供'));
 assert.ok(s.node('.schedule-grid').innerHTML.includes('未提供'));
});
check('Candidate controllers are released on rebuild, close and target replacement',()=>{
 const s=session('2026-11-04T01:00:00Z');
 s.run("choose('teacher','黃隆偉',false);openLesson(selectedTarget.record.lessons.find(l=>l.day===3&&l.period===6))");
 assert.equal(s.previews(),1);
 s.run('showCandidates(activeLesson,false)');assert.equal(s.previews(),1);
 s.run('returnToSchedule()');assert.equal(s.previews(),0);
 s.run('showCandidates(activeLesson,false)');assert.equal(s.previews(),1);
 s.run("choose('class','804',false)");assert.equal(s.previews(),0);
});
check('Desktop retains existing behavior',()=>{
 const s=session('2026-11-02T01:00:00Z',false);
 s.run("choose('class','804',false);chosenDay=5;choose('teacher','黃隆偉',false);openLesson(selectedTarget.record.lessons[0])");
 s.setTime('2026-11-03T01:00:00Z');s.event('visibilitychange');
 assert.equal(s.state().day,5);assert.equal(s.state().active,true);
});
console.log(JSON.stringify({scenarioGroups:checks,result:'passed'}));
