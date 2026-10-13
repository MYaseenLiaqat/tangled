# Phase 6: Instructor dashboard UI (F9, F10) and polish
Read `.github/copilot-instructions.md` and `docs/SCOPE.md`. UI only; no new backend rules.

Match the approved prototype (`tangled-v6.html` in the project folder) in layout and tone: minimal cards (topic, module, status, one percentage with bar, confidence label, View details),
detail page (why flagged with three checks, confusion groups with highlighted phrases and a Misconception label, collapsed not-counted list, Mark as addressed, Not a real problem),
simple Quiz results page (hardest item callout, % correct bar, most common wrong option), course materials page, topics setup page.
Requirements: loading, empty and error states on every page; "Not enough data yet" state when fewer than 4 students have asked; accessible (labels, focus, contrast); responsive down to tablet; light and dark via prefers-color-scheme.
Shared API client with typed responses; no `any`. Code-split routes with React.lazy.
Tests: add Vitest + React Testing Library with tests for Topics (empty/loaded), TopicDetail highlight, Quiz page.
Do NOT: add charts, new pages, settings, notifications, themes switcher.
Human check: click through every page with real data from the pilot seed; resize to tablet width.
