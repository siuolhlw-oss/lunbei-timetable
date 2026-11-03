# 課表資料格式與規則

- `timetable.json` stores the verified schedule extraction. Do not replace source lessons with guesses about unprovided special education lessons.
- `menu.json` contains user-confirmed categories, menu availability and any explicit `scheduleStatus: "partial"` override.
- `build-data.py` validates completeness consistency and regenerates browser data after source or menu changes.
- `teachers[].scheduleStatus` is `complete` for the currently supplied schedule unless a known gap is flagged, or `partial` for an explicitly incomplete schedule. It does not represent live availability or external commitments.
- A partial teacher retains known lessons. Every other cell is `未提供`; the UI displays `部分課表`. Known lessons cannot open swap suggestions.
- The swap engine returns `{status: "incomplete-data", candidates: []}` when the requesting teacher is partial. A partial teacher is also excluded from every other teacher's candidates, including when the visible lesson is corroborated by the class timetable.
- A missing timetable is a separate state: keep the menu entry disabled with `待補課表`, and exclude it from swap candidates.
- Public assets include only professional names, roles and schedule data. Local source paths and internal pending decisions stay out of generated assets.
- The existing same-class, reciprocal conflict checks and 1–7 versus 8 period restriction remain mandatory.
