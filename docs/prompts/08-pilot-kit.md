# Phase 8: Pilot kit (no new product features)
Read `.github/copilot-instructions.md` and `docs/SCOPE.md`.

1. `python -m app.cli demo_seed --course <id>`: creates a clearly labelled DEMO course dataset (synthetic students, messages, quiz aggregates) so the dashboard can be demoed even if the live pilot is quiet. Demo data is flagged in the DB and the UI shows a "Demo data" banner.
2. Evaluation tools: `python -m ml.export_labels` (course-scoped, message text + turn number, no identities) and `python -m ml.evaluate` (baseline vs logistic regression, precision/recall/F1, confusion matrix, threshold for target precision, writes `evaluation_report.md`).
3. `docs/PILOT_RUNBOOK.md`: day-by-day plan for the 1-2 week pilot (day 0 setup, day 1 student onboarding script, mid-pilot quiz, instructor review session, final labelling day), what to say to students, what data is collected, how to delete it afterwards.
4. `docs/REPORT_TEMPLATE.md`: capstone report skeleton (problem, method, architecture, evaluation, limitations, privacy, startup path) with the metrics from SCOPE.md.
5. A smoke script `scripts/smoke.sh` that registers an instructor, creates a course, uploads a sample file, joins as a student, chats and reads the dashboard against a running server.
Do NOT: add features. Done when: smoke script passes locally and docs exist.
