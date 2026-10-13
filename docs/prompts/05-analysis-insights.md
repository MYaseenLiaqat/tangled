# Phase 5: Analysis, quiz import, insights (F7, F8, insight rules)
Read `.github/copilot-instructions.md` and `docs/SCOPE.md`. Build ONLY F7, F8 and the insight rules exactly as written in SCOPE.md.

Analysis: implement the background job that labels each on-topic message (confusion / information / other, misconception flag, evidence phrase that must be a substring of the message, confidence).
Backend selectable by `INTENT_BACKEND`: `llm` (rubric judge, JSON mode, temperature 0, tolerant JSON parsing) or `logreg` (trained model file). Add `python -m app.cli retry_unlabelled` to relabel failures.
Quiz import: aggregate CSV `item,concept,option,count,correct` (concept = topic key). Validate strictly, report row errors, no student identities.
Rewrite `quiz_rate` to use aggregates. Insights service: pure functions per SCOPE.md (`classify`, share, Wilson lower bound for display), plus course-scoped queries. Groups: agglomerative clustering over embeddings of confusion messages; group title = a short LLM summary of the group (one call per group, cached on the group) with a fallback to the most central message.
Endpoints: GET /courses/{id}/topics (flagged + not-flagged reasons + summary), GET /courses/{id}/topics/{tid}, POST /courses/{id}/topics/{tid}/verdict, GET/POST quiz.
Minimum cell size: never display a count under 5 as an exact number to the instructor; show "fewer than 5" (but still evaluate rules on exact numbers).
Tests: table-driven tests for every rule boundary (3 vs 4 students, quiz exactly at QUIZ_LOW, High vs Medium), info questions never counted, gap messages never counted, false-alarm verdict resets the window, JSON parsing failure leaves the message unlabelled.
Do NOT: add per-student views, rankings, prediction, new signals, new thresholds UI.
Done when: tests + build pass. Human check: use `python -m app.cli demo_seed` is NOT yet available; instead insert 6 synthetic students' messages through the API with a script in `scripts/` and confirm a card appears.
