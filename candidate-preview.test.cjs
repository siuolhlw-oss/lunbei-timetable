const assert = require('node:assert/strict');
const data = require('./timetable.json');
const {createEngine} = require('./timetable-engine.js');
const preview = require('./candidate-preview.js');
const engine = createEngine(data);
let count = 0, sample;
for (const teacher of data.teachers) for (const source of teacher.lessons) {
  for (const candidate of engine.findCandidates(teacher.name, source).candidates) {
    const pair = preview.resolvePair(engine, teacher.name, source, candidate);
    assert.ok(pair, 'Every eligible candidate must resolve to two teacher lessons');
    assert.equal(pair.original.lesson, source);
    assert.equal(pair.other.teacher.name, candidate.teacher);
    for (const field of ['day', 'period', 'subject']) assert.equal(pair.other.lesson[field], candidate[field]);
    assert.ok(pair.other.lesson.classIds.includes(candidate.classId));
    for (const entry of [pair.original, pair.other]) {
      const week = preview.renderWeek(entry.teacher, entry.lesson, data.periods, engine.classes);
      assert.equal((week.match(/class="compare-picked-label"/g) || []).length, 1);
      assert.equal((week.match(/scope="row"/g) || []).length, 8);
      assert.ok(!week.includes('data-lesson'), 'Comparison cells must not trigger another swap');
    }
    sample ||= {teacher, source, candidate};
    count++;
  }
}
assert.ok(count > 0);
const {teacher, source, candidate} = sample;
assert.equal(preview.resolvePair(engine, 'missing', source, candidate), null);
assert.equal(preview.resolvePair(engine, teacher.name, source, {...candidate, teacher:'missing'}), null);
for (const side of [teacher.name, candidate.teacher]) {
  const changed = createEngine(structuredClone(data));
  changed.teachers.get(side).scheduleStatus = 'partial';
  assert.equal(preview.resolvePair(changed, teacher.name, source, candidate), null);
}
const duplicate = createEngine(structuredClone(data));
const lesson = duplicate.teachers.get(candidate.teacher).lessons.find(l => l.day === candidate.day && l.period === candidate.period);
duplicate.teachers.get(candidate.teacher).lessons.push({...lesson});
assert.equal(preview.resolvePair(duplicate, teacher.name, source, candidate), null);
const pair = preview.resolvePair(engine, teacher.name, source, candidate);
const day = preview.renderDay(pair.other.teacher, pair.other.lesson, candidate.day, data.periods, engine.classes);
assert.equal((day.match(/class="compare-day-row"/g) || []).length, 8);
assert.equal((day.match(/class="compare-picked-label"/g) || []).length, 1);
const safe = preview.renderCards([{...candidate, teacher:'<img src=x>', subject:'"<script>', classId:'A&B'}]);
assert.ok(!safe.includes('<img') && !safe.includes('<script>'));
assert.ok(safe.includes('&lt;img') && safe.includes('A&amp;B'));
console.log(JSON.stringify({result:'passed',candidatePairs:count,checks:['exact lesson identity','both selected cells','all eight periods','read-only cells','partial/missing/ambiguous rejection','escaping']}));
