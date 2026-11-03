"""Regenerate browser data from the versioned JSON sources."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
menu = json.loads((ROOT / 'menu.json').read_text())
data = json.loads((ROOT / 'timetable.json').read_text())
people = [p for group in ('admin', 'homerooms', 'subject', 'native')
          for row in menu[group] for p in row['items']] + menu['special']
assert len(people) == len({p['name'] for p in people}), 'Duplicate teacher menu entry'
by_name = {p['name']: p for p in people}
for teacher in data['teachers']:
    record = by_name[teacher['name']]
    assert record['hasSchedule'], 'Missing timetable entry contains course data'
    status = record.get('scheduleStatus', 'complete')
    assert status in ('complete', 'partial')
    assert teacher.get('scheduleStatus', 'complete') == status, 'Menu and timetable completeness disagree'
for source, variable, destination in (
    (menu, 'selectionData', 'selection-data.js'),
    (data, 'timetableData', 'timetable-data.js'),
):
    text = json.dumps(source, ensure_ascii=False).replace('<', '\\u003c')
    (ROOT / destination).write_text(f'const {variable} = {text};\n')
print('Browser data rebuilt successfully.')
