# Tangled MVP scope (the contract)

**Product:** an instructor creates a course, shares a join code/link, uploads course materials; students join anonymously, read the
materials and ask the AI; Tangled analyses the questions and shows the instructor only the topics where students genuinely show confusion.

## In scope (build exactly this)
| ID | Feature | Acceptance criteria |
|---|---|---|
| F1 | Instructor account | Register and log in with email + password; JWT; password hashed (argon2). No email sending, no password reset (manual CLI reset is allowed). |
| F2 | Course + join | Instructor creates a course (name, optional class size). System issues a 6-char join code and a join link. Instructor can close/reopen joining and regenerate the code. |
| F3 | Topics to track (concepts) | Instructor adds/edits/deletes up to 10 topics (name, module label, one-sentence description). Changing topics re-tags indexed materials in the background. |
| F4 | Materials | Upload PDF, PPTX, DOCX, IPYNB, MD, TXT (max 25 MB each, 50 per course). Status processing/indexed/failed with a readable error. Delete a file (removes its vectors). |
| F5 | Student join | Join via link or code, must accept a consent notice. Gets an anonymous ID and a token. No name or email collected. |
| F6 | Student app | List materials, preview PDFs, chat with the AI (answers from materials with citations; grounded refusal when not covered), buttons Clear / Still unclear. |
| F7 | Background analysis | Each on-topic message is classified confusion / information / other (+ misconception flag + evidence phrase). Failures are retried by a CLI job. |
| F8 | Quiz import | Instructor uploads an AGGREGATE CSV (no student identities): `item,concept,option,count,correct`. |
| F9 | Topics dashboard | Cards only for topics that need attention (rules below). Detail page: why flagged, confusion groups with highlighted phrases, not-counted info questions, buttons "Mark as addressed" and "Not a real problem". |
| F10 | Quiz results page | Per item: % correct, most common wrong option. Plain and simple. |
| F11 | Privacy basics | Consent screen on join, privacy text, instructor can delete a course and all its data (rows, vectors, files). |
| F12 | Deployable | One Docker image serves API + built frontend. Migrations run on start. Health endpoints. Backup script. |
| E1 | Engineering baseline | pytest suite, CI on every push, structured JSON logs, per-student rate limits, LLM timeouts/retries. |

## Insight rules (do not change without a change request)
A topic is "needs attention" only if: at least `MIN_STUDENTS` (default 4) DISTINCT students have a confusion message (confidence at least
`MIN_CONF`) AND a second signal agrees (quiz correct rate below `QUIZ_LOW`, or at least 3 students asked about it more than once).
Confidence High = 6+ students and quiz agrees; otherwise Medium. Information questions are never counted. Messages with no matching topic
are stored as `gap` and not counted. Share = confused students / class size (or joined students if class size is empty).

## Out of scope (do NOT build, do NOT scaffold)
LMS/LTI integration, embeddable widget, SSO/OAuth, billing/payments, multiple instructors or organisations or roles, email of any kind,
password reset by email, per-student reports or rankings or at-risk prediction, student-level quiz matching, chat history UI,
auto-generated quizzes, auto-suggested topics, OCR for scanned PDFs, non-PDF previews, websockets/real-time, admin super-panel,
i18n, mobile app, voice, notifications, grading, per-course threshold settings UI, analytics beyond the two dashboards.

## Scale seams (already required, so scaling later is configuration, not a rewrite)
Vertical: raise workers/CPU; async I/O; blocking vector calls run in threads. Horizontal later by swapping implementations behind the
interfaces: SQLite -> Postgres (`DATABASE_URL`), local Chroma -> server-mode vector DB (`VectorStore`), local disk -> object storage
(`FileStorage`), background tasks -> a queue (`Jobs`). MVP runs ONE worker because local Chroma and SQLite are single-process.

## Pilot success metrics (what we report)
Instructor false-alarm rate ("Not a real problem" presses / cards shown); classifier precision/recall vs the follow-up baseline on hand-labelled
messages; agreement of topic confusion with quiz results (descriptive); answer groundedness spot-check; median answer latency.

## Later (explicitly NOT now, in rough order)
Embeddable widget + LTI 1.3, SSO, multi-instructor orgs, Postgres + server vector DB + queue, retention/consent governance for institutions, a formal evaluation study.
