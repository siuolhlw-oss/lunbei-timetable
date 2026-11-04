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

## Default view and mobile current-day selection

- Start teacher/class views in week mode on a fresh page load; retain the user-selected day/week mode during the current session. Mobile day view still uses the current-day rules below.

- Determine the calendar date and weekday in `Asia/Taipei`; Saturday and Sunday map to Monday with no additional notice.
- On mobile (viewport width at most 650px), ordinary teacher/class selections reset the weekday to today. Preserve the selected day/week mode. Specific class lesson navigation and return restore their explicit weekday and mode instead.
- On visibility restoration, page restoration or window focus, update only if the Taiwan calendar date changed and the page is visible on mobile. Clear the active lesson and candidate contents, keeping the current teacher/class, origin-class return context and view mode. Same-day returns preserve manual browsing.
- Do not use a midnight timer: uninterrupted foreground browsing stays put until the next ordinary query or return to the page. Desktop behavior remains unchanged.

## Candidate timetable preview

- A candidate expands immediately below its own row. Clicking it again collapses it; opening another closes the previous panel while preserving the clicked row's viewport position.
- Resolve each teacher's lesson by day, period, subject and candidate class. Require exactly one match on each side and complete teacher schedules; ambiguous or incomplete data shows a review message instead of a comparison.
- Portrait mode initially displays the full week, with independent day/week and weekday controls. Switching to day mode initially displays the candidate's weekday. Width at least 900px, or landscape width at least 568px, displays the original teacher's full week on the left and candidate teacher's on the right. Highlight each teacher's own exchanged lesson; all eight periods remain visible.
- Preview cells are read-only. Keep the original target, selected lesson, main weekday/mode and class-return context unchanged. The preview does not change swap eligibility or schedule data.
- Close and destroy the preview on candidate rebuild, teacher/class replacement, closing the candidate panel and cross-day reset. Use distinct selectors from the main schedule controls.

## Original lesson marker and blank slots

- Each comparison timetable marks the other teacher's requested day/period with an amber dashed reference card containing that teacher, subject and class: the left/original timetable marks the candidate's slot, while the right/candidate timetable marks the original slot. Each teacher's own lesson remains green, with a role-specific legend above each table. These references never write schedule data or replace occupied lessons.
- `renderWeek` / `renderDay` options retain `origin` as the reference lesson pair and accept an optional `referenceRole` (default `原老師`); use `候選老師` for the left table's marker label and accessible name. Portrait source-summary and jump behavior remain unchanged.
- Portrait previews retain the original lesson summary above both daily and weekly views. The jump button selects the original weekday within the preview, preserves day/week mode, focuses and scrolls to the visible marker. The main schedule selection, day/mode and class-return context stay unchanged. Opening or reopening a candidate resets its preview to week mode and its day-view weekday to the candidate day.
- Teacher, class and candidate timetables retain every period and grid cell, including all eight periods. Remove the unassigned placeholder text and dash; blank cells remain visible. Known incomplete data must still display `未提供`, and candidates remain disabled for partial teachers.

## Teacher subject search

- Build each teacher menu button's `data-search` from the existing name and role tag plus distinct subject strings from that teacher's provided timetable lessons. Match across every menu category using the existing substring search.
- These search subjects are metadata only: keep visible name/role text, accessible button name, category order and timetable-availability state unchanged. No hidden text nodes or additional visible subject labels are added. Metadata remains inspectable in public page source.
- Use only supplied lessons, including known lessons for partial schedules; do not infer missing subjects, teaching qualifications or a primary specialty. Missing schedules retain existing name/tag matching and disabled buttons. Preserve original curriculum names without guessed categorization.
- Load timetable data before menu rendering. No source JSON schema or swap eligibility changes are required.
