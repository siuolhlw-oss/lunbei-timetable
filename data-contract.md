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

## Class-to-teacher navigation

- A class lesson opens its teacher only when there is exactly one teacher and a matching teacher lesson with the same day, period, subject and class ID. Ambiguous or unmatched lessons stay in the class view and show the review message.
- Save the origin class ID, selected weekday and mobile view mode before opening the teacher. Highlight the matching lesson, show its candidates and keep the origin return button available in the schedule header and fixed navigation.
- Returning restores the origin class, weekday and view mode. A new manual class/teacher selection clears the origin; changing weekday, view mode or a lesson within the teacher view does not overwrite it.
- Partial teachers may be opened from known matching class lessons, but still produce no swap candidates. Navigation never changes schedule data or swap eligibility.

## Mobile current-day defaults

- Determine the calendar date and weekday in `Asia/Taipei`; Saturday and Sunday map to Monday with no additional notice.
- On mobile (viewport width at most 650px), ordinary teacher/class selections reset the weekday to today. Preserve the selected day/week mode. Specific class lesson navigation and return restore their explicit weekday and mode instead.
- On visibility restoration, page restoration or window focus, update only if the Taiwan calendar date changed and the page is visible on mobile. Clear the active lesson and candidate contents, keeping the current teacher/class, origin-class return context and view mode. Same-day returns preserve manual browsing.
- Do not use a midnight timer: uninterrupted foreground browsing stays put until the next ordinary query or return to the page. Desktop behavior remains unchanged.

## Candidate timetable preview

- A candidate expands immediately below its own row. Clicking it again collapses it; opening another closes the previous panel while preserving the clicked row's viewport position.
- Resolve each teacher's lesson by day, period, subject and candidate class. Require exactly one match on each side and complete teacher schedules; ambiguous or incomplete data shows a review message instead of a comparison.
- Portrait mode initially displays the candidate's weekday, with independent day/week and weekday controls. Width at least 900px, or landscape width at least 568px, displays the original teacher's full week on the left and candidate teacher's on the right. Highlight each teacher's own exchanged lesson; all eight periods remain visible.
- Preview cells are read-only. Keep the original target, selected lesson, main weekday/mode and class-return context unchanged. The preview does not change swap eligibility or schedule data.
- Close and destroy the preview on candidate rebuild, teacher/class replacement, closing the candidate panel and cross-day reset. Use distinct selectors from the main schedule controls.
