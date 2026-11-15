# Tangled — Final MVP Verification Report

**Audit type:** Read-only implementation audit  
**Audit date:** 2026-11-15  
**Repository:** `MYaseenLiaqat/tangled`  
**Branch:** `integration/renaissance`  
**HEAD:** `4e8f6f9 Polish Tangled frontend UI`  
**Scope:** Existing repository only; no application files were modified.

## 1. Executive Summary

Tangled is a substantive MVP implementation. It has a FastAPI backend, React/Vite frontend, SQLModel/Alembic persistence, instructor JWT authentication, course/topic/material management, anonymous student joining with consent, Chroma-backed RAG code, background analysis, aggregate quiz import, insight rules, evidence grouping, verdicts, privacy-oriented aggregation, and deployment files.

The implementation is **not fully verified as a working product**. The automated suites pass when run from their correct directories, but most AI behavior is tested with fakes rather than real embeddings, Chroma, document ingestion, or an external LLM. The frontend returns citation metadata from the API but does not render it. The global request limit is 2 MB while material uploads advertise a 25 MB limit. Consent links to an unimplemented `/consent` route. Background jobs are in-process FastAPI tasks and are not durable across restarts.

**Final verdict: `PARTIALLY FUNCTIONAL`.**

The project can demonstrate authentication, course setup, topic setup, selected API behavior, dashboard rendering, and tested decision rules. It cannot honestly be called presentation-ready for the complete teacher → student → RAG → analysis → dashboard journey until a real material/embedding/LLM smoke test and the P0 integration issues are resolved.

## 2. Requirement-by-Requirement Verification Matrix

| ID | Requirement | Status | Evidence | Verification method | Gap or limitation |
|---|---|---|---|---|---|
| R01 | Instructor registration | Implemented and verified | `backend/app/routers/auth.py`, `register()` around line 35 | `backend`: `pytest -q`; API lifecycle tests | Registration is API/UI tested; no email verification is in scope. |
| R02 | Instructor login | Implemented and verified | `backend/app/routers/auth.py`, `login()` around line 46 | API tests passed | Login rate limiting is process-local. |
| R03 | Instructor token handling | Implemented and verified | `auth.token_for()`, `deps.current_instructor()` | API tests validate protected access and role boundaries | No refresh token or frontend expiry/logout flow. |
| R04 | Instructor logout | Not implemented | `frontend/src/App.tsx` has no logout control; no logout API route | Route enumeration and frontend inspection | Token removal must be manual/browser-local. |
| R05 | Course creation | Implemented and verified | `POST /api/v1/courses`, `courses.create()` | `test_api.py`, `test_flow.py` passed | No frontend course deletion control. |
| R06 | Course listing | Implemented and verified | `GET /api/v1/courses`, `courses.list_courses()` | API tests passed | Requires a valid instructor token. |
| R07 | Course update | Implemented and verified | `PATCH /api/v1/courses/{course_id}` | API tests passed | UI only exposes limited course controls. |
| R08 | Course ownership isolation | Implemented and verified | `deps.get_owned_course()` filters instructor ID | Cross-owner API test passed | No evidence of a separate integration test across every course endpoint, though shared dependency covers them. |
| R09 | Join-code generation | Implemented and verified | `courses.new_join_code()`, `courses.output()` | API test checks six-character code | Code is returned by API. |
| R10 | Join-code regeneration | Implemented and verified | `POST /api/v1/courses/{course_id}/join-code/regenerate` | API test confirms old/new codes differ | Frontend API helper exists but no visible regeneration control. |
| R11 | Join link generation/display | Partially implemented | `courses.output()` returns `join_link`; `Courses` displays only `join_code` | Source inspection | Instructor UI does not display a clickable/copyable join link. |
| R12 | Open/close joining | Implemented and verified | `Course.joining_open`, `CourseUpdate`, `student.join()` | API test closes joining; join endpoint checks it | No obvious frontend control in the inspected course list/workspace. |
| R13 | Topic creation | Implemented and verified | `POST /api/v1/courses/{course_id}/topics`, `create_topic()` | Phase 3/5 API tests passed | Retagging is background-task based. |
| R14 | Topic editing | Implemented and verified | `PATCH /api/v1/courses/{course_id}/topics/{topic_id}` | Phase 5 API test passed | Retagging behavior is not real-provider tested. |
| R15 | Topic deletion | Implemented and verified | `DELETE /api/v1/courses/{course_id}/topics/{topic_id}` | Phase 5 API test passed | Existing message/topic relationships are not comprehensively integration-tested after deletion. |
| R16 | Topic limit of ten | Implemented and verified | `create_topic()` checks count | Phase 3 API test passed | No issue found in tested path. |
| R17 | Material upload | Partially implemented | `POST /api/v1/courses/{course_id}/materials`, `upload_materials()` | Validation test passed for invalid PDF and processing state | `REQUEST_MAX_BYTES=2_000_000` conflicts with `MAX_UPLOAD_MB=25`; many allowed files cannot reach per-file validation. |
| R18 | Supported material formats | Implemented but unverified with real files | `backend/app/services/ingest.py`: PDF, PPTX, DOCX, IPYNB, MD, TXT | Source inspection; no real ingestion suite | Real parser execution and representative files were not run during audit. |
| R19 | Filename/content validation | Implemented and verified | `safe_filename()`, `valid_content()` | Phase 3 validation test passed | Signature checks are basic; they do not prove complete file safety. |
| R20 | Material storage | Implemented but unverified operationally | `LocalFileStorage.save()` | Source inspection and unit/endpoint use | No live upload/index/delete smoke test against a fresh data directory. |
| R21 | Processing status/error | Implemented | `Material.status/error`, `process_material()` | Source inspection; processing response tested | Real processing failures and UI polling were not exercised with real documents. |
| R22 | Material deletion | Implemented and verified at service/API level | `DELETE /api/v1/courses/{course_id}/materials/{material_id}` | Deletion code inspection and course deletion tests | Real Chroma vector deletion was not tested against a populated collection. |
| R23 | Fresh database setup | Implemented | `backend/app/db.py:migrate()`, Alembic revisions | TestClient startup applies migrations; local DB inspected | No separate clean-database migration command was executed during this audit. |
| R24 | Student join by code | Implemented and verified | `GET /api/v1/student/join/{code}`, `POST /api/v1/student/join` | Consent/join API test passed | Student entry requires manually opening `/join/{code}` because link display is incomplete. |
| R25 | Consent enforcement | Implemented and verified at API level | `JoinIn`, `student.join()` rejects false consent | Phase 4 test passed | Frontend links to missing `/consent`; consent text is not implemented as an application route. |
| R26 | Anonymous student identity | Implemented and verified | `Student` has course ID, consent version, timestamps; no name/email | Model and API inspection/tests | Student token contains internal student ID, appropriately scoped but still sensitive if exposed. |
| R27 | Student token/session persistence | Partially implemented | `student_token` in `localStorage`; `Student` creates `crypto.randomUUID()` | Frontend inspection | Token persists, but session ID is component/browser-local and there is no logout/session management. |
| R28 | Student materials list | Implemented | `GET /api/v1/student/materials`, `Student` page | Source inspection | Error handling collapses failures to an empty list. |
| R29 | PDF preview | Implemented and verified at API level | Signed URL functions and `material_file()` | PDF URL/tampering test passed | Browser display was not run. |
| R30 | Non-PDF preview | Not implemented by design | `student_material()` only adds `file_url` for PDFs | Source inspection | This matches the declared MVP scope. |
| R31 | Student chat | Partially implemented | `POST /api/v1/student/chat`, `Student.ask()` | Endpoint logic and mocked chat tests | Real RAG/LLM execution unverified; UI has no robust chat error/loading state. |
| R32 | Chat history | Implemented but limited | `GET /api/v1/student/messages`, page loads messages | Source inspection | No selectable session/history UI; broader chat-history UI is out of scope. |
| R33 | Clear/Still unclear feedback | Implemented | `POST /api/v1/student/feedback`, `Student.setFeedback()` | Source inspection and endpoint logic | Feedback is not currently used in insight rules. |
| R34 | Course-scoped retrieval | Implemented but unverified with real Chroma | `ChromaVectorStore.query()` uses `where={"course_id": course_id}` | Source inspection; retrieval fakes in tests | No populated multi-course Chroma integration test. |
| R35 | Similarity threshold/refusal | Implemented and unit-tested with fakes | `rag.grounding_refused()`, `rag.answer()` | Phase 4 test verifies low similarity avoids LLM call | Threshold behavior with actual embeddings is unverified. |
| R36 | Grounded answer prompt | Implemented but unverified | `rag.SYSTEM`, `rag.answer()` | Prompt/source inspection | Provider behavior and citation correctness are not measured. |
| R37 | Citation generation | Partially implemented | `rag.answer()` returns `sources`; prompt requests `[1]` citations | Source inspection | The API returns source metadata, but `Student.tsx` does not display it; answer citation text is not validated against returned sources. |
| R38 | Grounded refusal | Implemented and verified with mocked retrieval | `rag.REFUSAL`, `grounding_refused()` | Test confirms refusal and no fake LLM call | Real out-of-scope question was not tested. |
| R39 | LLM timeout/retry | Implemented in client configuration | `services/llm.py`, `Settings.llm_timeout/max_retries` | Source inspection | No real provider outage/timeout test. |
| R40 | Embedding provider | Implemented but unverified | Chroma ONNX MiniLM default embedding function | Source inspection | Model download/cache and runtime were not executed during audit. |
| R41 | Message classification labels | Implemented | `analysis.Classification`, rubric prompt | Unit/API tests for parsing/failure | No accuracy evaluation. |
| R42 | Information exclusion | Implemented and verified at rule level | `insights.build_stats()` counts only `intent=="confusion"` | `test_insights.py` rule tests | Real classifier output distribution is unverified. |
| R43 | Topic assignment | Implemented | Retrieval metadata via `rag.topic_of()` and `_topic_for()` embedding fallback | Source inspection | Correctness with real course topics/materials unverified. |
| R44 | Evidence phrase extraction | Implemented and verified syntactically | `analysis.analyze()` requires phrase substring | Analysis test covers invalid JSON; phrase behavior inspected | No real provider output test. |
| R45 | Misconception flag | Implemented but not validated | LLM schema and `Message/AnalysisJob.misconception` | Source inspection | Dashboard does not show message-level misconception evidence; no quality evaluation. |
| R46 | Repeat-question detection | Implemented and verified at rule level | `persist_students=sum(count >= 2...)` | Insight tests passed | Repetition means multiple confusion messages, not semantic duplicate-question detection. |
| R47 | Distinct-student aggregation | Implemented and verified | Sets of `student_id` in `build_stats()` | Insight rules/API privacy tests | Depends on correct student token/course association. |
| R48 | Quiz aggregate import | Implemented and verified | `POST /api/v1/courses/{course_id}/quiz/import` | Phase 5 tests passed | Only aggregate CSV is supported; no student-level matching, as required. |
| R49 | Quiz corroboration | Implemented and verified at rule level | `_quiz_rate()`, `rules.classify()` | Insight boundary tests passed | Real imported quiz plus analyzed messages was not run end-to-end. |
| R50 | Insight thresholds | Implemented and verified | `settings.min_students=4`, `min_conf=.70`, `quiz_low=.60`, `rules.classify()` | `test_insights.py` passed | No empirical validation of whether thresholds are useful. |
| R51 | Insight grouping | Implemented but unverified with real data | `_cluster()`, `_group_title()`, `InsightGroup` | Source inspection; UI mock test | Real embedding clustering and LLM titles were not executed. |
| R52 | Verdicts | Implemented and verified | `POST .../verdict`, `Verdict`, `TopicDetail.mark()` | Source inspection and API path | No frontend end-to-end browser test. |
| R53 | Aggregate/privacy dashboard | Implemented and verified at API shape | `insights.topics/detail()` omit student IDs | Privacy test checks no private text/student ID in response | Evidence phrases can still contain raw student wording; no names/emails are stored. |
| R54 | Course deletion | Backend implemented and tested; UI incomplete | `course_deletion.delete_course()`, `DELETE /api/v1/courses/{course_id}` | Phase 7 deletion test passed | No frontend deletion workflow. |
| R55 | Health endpoints | Implemented | `/health/live`, `/health/ready` | Route inspection | Docker health behavior not run because Docker unavailable. |
| R56 | One-image deployment | Implemented but unverified | Root `Dockerfile`, `docker-entrypoint.sh`, `docker-compose.yml` | File inspection | Docker executable unavailable. |
| R57 | CI | Implemented | `.github/workflows/ci.yml` | File inspection | CI was not executed in GitHub during this audit. |
| R58 | ML evaluation | Tooling exists but evaluation result unavailable | `backend/ml/evaluate.py`, `export_labels.py` | Repository inspection | No verified labelled dataset, precision, recall, F1, or confusion matrix was found. |

## 3. AI Engineering Assessment

### 3.1 Document ingestion and supported formats

`backend/app/services/ingest.py` defines:

- `_pdf()` using `pypdf`
- `_pptx()` using `python-pptx`
- `_docx()` using `python-docx`
- `_nb()` using JSON notebook cells
- `_txt()` for Markdown and text
- `EXT` and `KIND` mappings for `.pdf`, `.pptx`, `.docx`, `.ipynb`, `.md`, and `.txt`

`backend/app/services/materials.py:process_material()` performs an additional selectable-text check for PDFs and stores `processing`, `indexed`, or `failed`.

The parsers and chunker were inspected but not run against real representative files during this audit. The repository has local upload data, but its presence is not proof that the current code successfully indexed those files.

### 3.2 Chunking

`ingest.chunk()` splits text on blank-line paragraphs, accumulates paragraphs to a nominal size of 900 characters, and breaks oversized content into slices while allowing up to approximately `size * 1.5`. The unit test verifies the resulting chunks stay under 1400 characters for its fixture.

There is no environment setting for chunk size; 900 is a code-level default.

### 3.3 Embeddings and vector persistence

`backend/app/adapters/chroma.py:ChromaVectorStore` uses Chroma `PersistentClient`, collection `materials`, cosine distance, and Chroma’s default ONNX MiniLM embedding function. `rag.ef()` configures the ONNX cache under `EMBEDDING_CACHE_DIR`.

`ingest.ingest()` generates embeddings, assigns nearest topic metadata, and adds documents with metadata including `course_id`, `material_id`, material name, section, and topic key.

This is implemented but not real-service verified. Tests monkeypatch retrieval or call higher-level logic with supplied hits; they do not demonstrate model download, actual embedding generation, Chroma persistence, or retrieval quality.

### 3.4 Retrieval isolation and similarity

`ChromaVectorStore.query()` passes `where={"course_id": course_id}`. `rag.retrieve()` forwards the student’s course ID. `rag.grounding_refused()` rejects empty results or a best similarity below `MIN_SIMILARITY`, default `0.25`.

The isolation logic is present. A populated multi-course Chroma integration test was not run, so cross-course isolation is not operationally proven.

### 3.5 Prompt construction and answer generation

`rag.SYSTEM` instructs the model to treat `UNTRUSTED_DATA` blocks as data, answer only from numbered excerpts, cite `[1]`-style sources, and abstain if excerpts do not contain the answer. `rag.answer()` injects the question and retrieved excerpts into a second prompt and calls `services.llm.chat()`.

`services/llm.py` uses an OpenAI-compatible asynchronous client with configurable base URL, model, timeout, retries, JSON mode fallback, and maximum output tokens.

The prompt and client are implemented. No real provider call was made in this audit, so groundedness, prompt-injection resistance, answer quality, and provider compatibility remain unverified.

### 3.6 Citations and traceability

The API constructs source metadata:

```text
{"n": ..., "material": ..., "section": ...}
```

The model is instructed to include numbered citations in answer text. However, the student page renders only `m.answer` and does not render the returned `sources` array. The student therefore cannot inspect source references in the current UI. There is also no server-side validation that answer citation numbers correspond to returned source entries.

### 3.7 Abstention and failures

Low-similarity questions are refused without an LLM call. LLM API, timeout, connection, and timeout errors in `student.chat()` become HTTP 503 responses. Analysis failures are saved as `analysis_failed`.

Embedding/model initialization failures are not handled by a dedicated user-facing path. Material processing catches exceptions and stores a readable error, but the student materials endpoint/page can reduce failures to an empty state.

### 3.8 Real versus mocked AI execution

Verified:

- Prompt construction by source inspection.
- Low-similarity refusal using fake hits.
- JSON parsing and invalid-analysis failure handling.
- Course ID metadata filtering by source inspection.

Not verified:

- Real document parsing/indexing.
- Real ONNX embedding generation.
- Real Chroma persistence/querying.
- Real LLM answer generation.
- Real LLM classification.
- Citation correctness.
- End-to-end groundedness.

## 4. ML and Learning-Signal Assessment

### 4.1 Labels and classifier

`analysis.Classification` supports `confusion`, `information`, and `other`, plus confidence, misconception, and evidence phrase. `analysis.RUBRIC` tells the LLM to classify one student message and return JSON.

Two backends are available:

1. `INTENT_BACKEND=llm`: OpenAI-compatible rubric judge.
2. `INTENT_BACKEND=logreg`: loads a Joblib model from `INTENT_MODEL_PATH`, predicts probabilities from embeddings, and converts low-probability confusion to `other`.

The classifier has not been evaluated against a verified labelled dataset. No measured precision, recall, F1, or confusion matrix is available.

### 4.2 Confusion versus information

`insights.build_stats()` selects only messages where `intent == "confusion"` and confidence meets `MIN_CONF`. It separately counts information messages. Therefore ordinary information questions are not included in confusion counts if classification labels are correct.

This behavior is covered by pure-rule tests, not by a real provider evaluation.

### 4.3 Topic assignment

For chat messages, `rag.topic_of()` weights retrieved passage similarity by `topic_key`. For analysis fallback, `_topic_for()` embeds the message and topic descriptions and chooses the highest cosine similarity if it reaches `MIN_SIMILARITY`.

A message without a matching topic becomes a gap and is not counted as confusion for a topic. Correctness depends on actual embedding quality and metadata, neither of which was live-tested.

### 4.4 Evidence phrase and misconception

The classifier returns `evidence_phrase`. `analysis.analyze()` rejects a result if the phrase is not a substring of the original message, then truncates it to `MAX_EVIDENCE_PHRASE_CHARS`.

Misconception is stored on `Message` and `AnalysisJob`. The topic detail UI displays a generic “Misconception signal where identified” pill for groups, but does not show which individual message was marked or why. No quality assessment of the flag exists.

### 4.5 Repetition and distinct students

`build_stats()` builds a map of confusion messages per `student_id`. It counts:

- distinct confused students using the map keys;
- persistent students using counts of at least two confusion messages.

This prevents one student’s repeated messages from being counted as multiple students. It is tested through pure decision-rule tests, but not through a complete live multi-student analysis workflow.

### 4.6 Quiz corroboration and thresholds

`_quiz_rate()` computes aggregate correct rate from `QuizAggregate`. `rules.classify()` requires:

- at least `MIN_STUDENTS` distinct confused students;
- confidence at least `MIN_CONF` through the upstream filter;
- either quiz rate below `QUIZ_LOW` or at least three persistent students.

Default settings are four students, 0.70 minimum confidence, and 0.60 quiz threshold. Confidence is High only when at least six students are confused and the quiz signal agrees; otherwise it is Medium.

The pure rules are well covered by `backend/tests/test_insights.py`.

### 4.7 False-positive safeguards

Implemented safeguards include:

- information messages excluded;
- gaps not counted;
- distinct-student threshold;
- corroborating quiz or persistence signal;
- minimum classifier confidence;
- false-alarm verdict;
- aggregate-only instructor views;
- low similarity treated as a material gap rather than confusion.

These are design safeguards, not evidence that the classifier is accurate. No human-labelled evaluation metrics were found.

### 4.8 Retry and duplicate processing

`AnalysisJob.message_id` is unique. `analysis.analyze()` returns for completed jobs, increments attempts, and marks jobs failed after the configured retry count. `python -m app.cli retry_unlabelled` retries pending/failed jobs below the attempt limit.

The job execution mechanism is `FastAPI BackgroundTasks`, so work is process-local and can be lost on restart. The database job row provides recoverability only if the CLI retry command is manually or externally run. There is no durable queue or worker in the repository.

## 5. Software Engineering Assessment

### 5.1 Database schema and relationships

`backend/app/models.py` defines:

- `Instructor`
- `Course`
- `Concept`
- `Material`
- `Student`
- `Message`
- `AnalysisJob`
- `QuizAggregate`
- `InsightGroup`
- legacy/unused-looking `QuizItem` and `QuizResponse`
- `Verdict`

Course-owned data has `course_id` in the current models. Shared course ownership is enforced through `get_owned_course()` for instructor endpoints, and student identity is scoped by token course ID plus database lookup.

The migration history includes the initial legacy schema and later course ownership/consent/analysis changes. Fresh migration setup is implemented, but a separate clean-database migration run was not executed during this audit.

### 5.2 API validation and errors

Pydantic models validate credentials, course names, topic fields, join codes, chat length, and verdict values. Uploads validate extension, basic content signatures, count, and size. Errors generally use explicit HTTP exceptions.

The frontend `friendlyError()` parses JSON API details. Some pages have retry/error states, but student chat catches no exception and the materials loader converts failures to an empty list.

### 5.3 Authentication and authorization

Instructor passwords use Argon2. JWTs contain role, subject, issued-at, and expiration. Student tokens contain role, student ID, course ID, issued-at, and expiration. `current_instructor()` and `current_student()` reject wrong roles and missing records.

The backend boundaries are tested. The frontend has no route guard, logout, refresh, or expired-token handling.

### 5.4 Upload limits and storage safety

Per-file configuration is 25 MB and Nginx allows 25 MB. The application middleware rejects request bodies over 2,000,000 bytes. This is a material functional defect because multipart overhead plus a valid file over roughly 2 MB will be rejected before the intended file limit.

Filenames are reduced to a basename and restricted characters. Files are stored under the configured upload directory using `<material_id>_<filename>`. Vector and file deletion paths exist.

### 5.5 Background processing and data integrity

Material indexing and topic retagging use FastAPI background tasks. Analysis jobs are created in the database before enqueueing. This is adequate for a one-worker MVP under ideal conditions but not durable. A process crash can leave `processing` materials or pending analysis jobs.

Course deletion deletes rows in a database session, then files and vectors. Vector/file cleanup failures are logged but do not roll back the committed database deletion, so cleanup can become incomplete.

### 5.6 Logging and observability

`main.py` configures JSON-style request logs with request IDs. Chat logs include timing, student ID, retrieval count, and refusal status, not message content. Analysis logs include message ID and error type.

There is no job dashboard, structured material-indexing event history, provider usage tracing, or alerting.

### 5.7 Configuration and secrets

Settings are loaded through `pydantic-settings` and `.env`. Production startup rejects a short/default JWT secret, missing LLM key, and wildcard CORS. `.env` is ignored by Git and `.env.example` contains variable names.

Development mode still permits unsafe defaults and logs warnings. That is acceptable for local development but must not be used for a public demonstration.

### 5.8 Dependencies and deployment

Dependencies are declared in `backend/requirements.txt` and `frontend/package.json` with lockfile support on the frontend. The root Dockerfile builds the frontend and runs the backend in one image; the entrypoint runs migrations and prewarming before Uvicorn.

Docker was unavailable in the audit environment, so Compose/image startup was not validated.

## 6. Frontend Assessment

### 6.1 Routes and screens

Routes are defined in `frontend/src/App.tsx`:

- `/`: `Auth`
- `/courses`: `Courses`
- `/join/:code`: `Join`
- `/student`: `Student`
- `/courses/:id/topics`: `Topics`
- `/courses/:id/topics/:topicId`: `TopicDetail`
- `/courses/:id/quiz`: `Quiz`
- `/courses/:id/materials`: `CourseMaterials`
- `/courses/:id/setup`: `TopicsSetup`

### 6.2 Working journeys

- Instructor register/login form calls the correct API methods and stores the token.
- Course creation and listing call real endpoints.
- Topic setup supports add/edit/delete and displays a 10-topic count.
- Material upload calls the backend and polls processing status while any item is `processing`.
- Join page accepts a code and consent checkbox.
- Student page lists materials, loads saved messages, sends questions, and records feedback.
- Dashboard, topic detail, quiz, and setup screens use backend API helpers rather than production mock data.

### 6.3 Incomplete or broken UI

1. **Citations not rendered:** `Student.tsx` appends the answer but ignores `sources`.
2. **Dead consent link:** `Join.tsx` links to `/consent`; `App.tsx` defines no such route.
3. **No visible join link:** `Courses` shows a code but not the returned `join_link`.
4. **No logout:** no control removes `instructor_token` or `student_token`.
5. **No route guards:** direct navigation to protected screens triggers API failures rather than redirecting to authentication.
6. **Student chat error handling:** `Student.ask()` has no `try/catch`, loading state, or disabled submit state.
7. **Student materials errors:** the initial material load catches errors and sets `[]`, which can look like an empty course.
8. **No frontend course deletion:** backend endpoint exists but no screen invokes it.
9. **No frontend course join open/close/regenerate controls:** API helpers exist for some operations, but the inspected UI does not expose a complete course-sharing management flow.
10. **Evidence detail is derived text:** `TopicDetail.Highlight` highlights words by regex in evidence phrases; it does not display raw message records or a server-provided span.

### 6.4 Mocked or hardcoded content

The production React pages call API helpers. The frontend tests mock API responses, and the HTML files under `docs/design/` are explicitly presentation prototypes with mock data. Those design files are not the production application.

## 7. End-to-End Workflow Verification

| Step | Status | Trace and blocker |
|---|---|---|
| 1. Instructor registers and logs in | Verified working | `Auth` calls `/auth/register` or `/auth/login`; backend tests passed. |
| 2. Instructor creates a course | Verified working | `Courses` calls `POST /courses`; backend tests passed. |
| 3. Instructor configures topics | Verified working | `TopicsSetup` calls topic CRUD endpoints; API tests passed. |
| 4. Instructor uploads materials | Partially working | Upload/status code exists, but global 2 MB body limit conflicts with 25 MB requirement. |
| 5. Backend extracts/chunks/embeds/indexes | Implemented but unverified | `process_material()` → `ingest()` → `rag.ef()` → Chroma; no live provider/file test. |
| 6. Student joins correct course | Verified at API level | Join code is looked up and course ID is placed in the student token. |
| 7. Student provides consent | Verified at API level; partially working in UI | Backend rejects false consent; `/consent` link is dead. |
| 8. Student asks a question | Partially working | Chat API/UI exist; frontend lacks robust error/loading handling. |
| 9. Relevant course material is retrieved | Implemented but unverified | Chroma query filters course ID; real populated collection not tested. |
| 10. AI generates grounded response | Implemented but unverified | Prompt, refusal, and OpenAI-compatible client exist; no real provider call. |
| 11. Student inspects citations and feedback | Partially working | Feedback works; citation metadata is not rendered. |
| 12. Background analysis classifies interaction | Partially working | Job/classifier/retry code exists; real LLM analysis and durable execution unverified. |
| 13. Topic/evidence assignment | Implemented but unverified | Retrieval metadata and embedding fallback exist; no real-quality verification. |
| 14. Distinct-student aggregation | Verified at rule/API logic level | Sets by student ID and tests exist; complete live multi-student flow not run. |
| 15. Quiz corroboration | Verified at rule/import level | Aggregate CSV and threshold rules are tested; combined live flow not run. |
| 16. Teacher dashboard displays candidates | Partially working | Real endpoints and UI exist; meaningful output depends on unverified AI pipeline. |
| 17. Teacher records verdict | Implemented and verified at API/UI logic level | Verdict endpoint and buttons exist; browser end-to-end execution not run. |

**First practical break for a fresh demo:** material upload is unreliable for normal files above the 2 MB request cap.  
**First unverified core dependency:** real parsing → embeddings → Chroma → LLM answer generation.

## 8. Test Results

### 8.1 Backend tests

Command run from the repository root:

```text
pytest -q
```

Result: collection failed with nine `ModuleNotFoundError: No module named 'app'` errors because the backend package is not on the root Python path.

Correct command:

```powershell
Set-Location backend
pytest -q
```

Observed result:

```text
36 passed, 1 warning in 16.31s
```

The warning was a Starlette/AnyIO deprecation warning.

### 8.2 Frontend tests

Command from `frontend`:

```powershell
Set-Location frontend
npm run test
```

Observed result:

```text
1 test file passed
6 tests passed
```

React Router future-flag warnings were emitted.

### 8.3 TypeScript and production build

Command:

```powershell
Set-Location frontend
npm run build
```

Observed result:

```text
tsc --noEmit passed
vite production build passed
44 modules transformed
```

The root-level `npm run build` was also attempted and failed with `ENOENT` because the root has no `package.json`.

### 8.4 Database migration/fresh setup

The application startup calls `migrate()` and configures Alembic to the current database URL. TestClient startup exercised migration setup against the test database, and the local database schema was inspected without reading row contents.

No separate clean-directory command such as a disposable database migration was run during this audit. Therefore a standalone fresh migration result is **not claimed**.

### 8.5 Integration tests

The backend suite contains API/flow tests, but there is no browser-level full-stack integration test. The tests use fakes for retrieval/LLM behavior where needed. No real teacher-to-student-to-dashboard integration was executed.

### 8.6 Docker/deployment validation

Attempted:

```powershell
docker compose config --quiet
```

Result: unavailable because `docker` was not installed or present on PATH.

The Python environment reported Python 3.13.5, Node 22.13.1, npm 10.9.2, and Git 2.48.1. The repository documents Python 3.12 and Node 20+.

## 9. Security, Privacy, and Reliability Risks

| Risk | Severity | Evidence | Impact |
|---|---|---|---|
| Request-size limit contradicts material-size limit | High | `config.py` `request_max_bytes=2_000_000` vs `max_upload_mb=25` | Normal valid materials fail before indexing. |
| In-process background jobs | High | `adapters/jobs.py:FastAPIJobs` | Indexing/analysis can be lost on restart; dashboard may remain incomplete. |
| Real provider behavior unverified | High | Tests use fake retrieval/LLM paths | A presentation may fail due to model download, API compatibility, cost, timeout, or prompt behavior. |
| Citation metadata hidden in UI | Medium | `Student.tsx` ignores `sources` | Core evidence/grounding claim is not visible to students. |
| Dead consent route | Medium | `Join.tsx` links `/consent`; no route in `App.tsx` | Consent information is inaccessible through the advertised link. |
| No frontend logout/expiry handling | Medium | `App.tsx`, `api.ts` | Shared demo browsers can retain tokens and confuse role/session testing. |
| Material processing failure can look empty | Medium | `Student.tsx` catches material load errors as `[]` | Users cannot distinguish no materials from an API failure. |
| Cleanup after course deletion is not atomic across systems | Medium | `course_deletion.py` commits DB before file/vector cleanup | Orphaned files/vectors may remain after a cleanup failure. |
| Evidence phrases may contain raw student wording | Medium | `insights.topics/detail()` returns phrases | Aggregate privacy is improved but evidence can still reveal sensitive text. |
| Local rate limiter is process-local | Medium | `services/rate_limit.py` | It is unsuitable for multiple workers or horizontally scaled deployment. |
| Development defaults are unsafe if exposed | Medium | `config.py` permits warnings in `dev` | A misconfigured demo can use default JWT secret or missing LLM key. |
| No classifier evaluation evidence | High | No verified gold dataset/metrics | Insight accuracy cannot be claimed. |

## 10. Redundant or Unnecessary Features

These are not necessarily defects; they are candidates to hide from a narrow MVP presentation after checking dependencies.

1. **Legacy `QuizItem` and `QuizResponse` models:** the implemented product uses aggregate `QuizAggregate` import. The legacy tables are still referenced by course deletion and migrations, so they should not be removed casually. They can be hidden from the presentation unless a dependency audit confirms they are unused.
2. **`/auth/me`:** useful for future session restoration and diagnostics, but not required by the current visible journey.
3. **Logistic-regression backend:** valuable for later evaluation, but the default demo uses the LLM backend. It should remain available unless model artifacts and evaluation workflow are intentionally removed together.
4. **Design HTML prototypes under `docs/design/`:** they are not production routes. They should be excluded from a live demo rather than treated as application functionality.
5. **Non-PDF reader expectation:** do not present non-PDF material preview as an incomplete promise; the scope explicitly limits previews to PDFs.

No feature should be deleted solely based on this list without checking migrations, course deletion, CLI behavior, and documentation dependencies.

## 11. Prioritized Remediation Plan

### P0 — Prevents core MVP functionality or makes the product unsafe/unreliable

#### P0.1 Align request and upload limits

- **Problem:** Global request limit is about 2 MB while material settings and proxy allow 25 MB.
- **Evidence:** `backend/app/config.py`, `backend/app/main.py` request middleware, `nginx.conf`.
- **Why it matters:** Valid course materials fail before the upload handler.
- **Likely files:** `backend/app/config.py`, `backend/app/main.py`, `nginx.conf`, `.env.example`.
- **Recommended fix:** Set request/proxy limits consistently with multipart overhead and the 25 MB per-file requirement.
- **Dependencies:** Deployment environment and chosen maximum request size.
- **Verification:** Upload a real 20–25 MB supported file and confirm processing reaches `indexed` or a readable parser failure.

#### P0.2 Execute a real RAG smoke test

- **Problem:** Real ingestion, ONNX embeddings, Chroma retrieval, and LLM answer generation are unverified.
- **Evidence:** `backend/app/services/ingest.py`, `rag.py`, `adapters/chroma.py`, `services/llm.py`.
- **Why it matters:** This is the product’s central claim.
- **Likely files:** Primarily test/smoke-test setup; no application change is implied by this audit.
- **Recommended fix:** Use a real selectable-text PDF, real configured provider, and a disposable database/vector directory.
- **Dependencies:** LLM credentials, network access, embedding model download, representative course file.
- **Verification:** Confirm indexed status, retrieved course-specific chunks, visible source metadata, grounded answer, and grounded refusal.

#### P0.3 Make citations visible and traceable

- **Problem:** API sources are not rendered and answer citation numbers are not validated.
- **Evidence:** `backend/app/routers/student.py:chat()`, `frontend/src/api.ts`, `frontend/src/pages/Student.tsx`.
- **Why it matters:** Students cannot inspect the evidence supporting an answer.
- **Likely files:** `frontend/src/api.ts`, `frontend/src/pages/Student.tsx`, possibly RAG response validation.
- **Recommended fix:** Render material/section sources and verify citation references are bounded by returned sources.
- **Dependencies:** Real RAG smoke test.
- **Verification:** Ask a grounded question and confirm each displayed citation maps to an actual uploaded material section.

#### P0.4 Verify durable handling of analysis/indexing failures

- **Problem:** FastAPI background tasks are lost on process restart.
- **Evidence:** `backend/app/adapters/jobs.py`, `services/analysis.py`, `services/materials.py`, `app/cli.py`.
- **Why it matters:** Insights may silently remain incomplete.
- **Likely files:** Job adapter, startup/CLI operational path, material/analysis status UI.
- **Recommended fix:** At minimum document and exercise the retry CLI for the controlled demo; longer-term replace the adapter with a durable queue.
- **Dependencies:** One-worker MVP constraint in `docs/SCALING.md`.
- **Verification:** Interrupt/restart after creating a pending job, run retry command, and confirm eventual status/result.

#### P0.5 Establish real classifier evaluation

- **Problem:** No verified gold dataset or measured metrics.
- **Evidence:** `backend/ml/evaluate.py`, `export_labels.py`; no verified dataset/results found.
- **Why it matters:** The product must not claim accurate confusion detection without evidence.
- **Likely files:** ML data workflow and documentation, not necessarily runtime code.
- **Recommended fix:** Label a representative dataset, run evaluation, report precision/recall/F1/confusion matrix, and record threshold choice.
- **Dependencies:** Real pilot messages and human labels.
- **Verification:** Preserve reproducible evaluation output and compare information-question false positives.

### P1 — Important for a credible presentation and complete user experience

#### P1.1 Fix consent navigation

- **Problem:** `/consent` is linked but not routed.
- **Evidence:** `frontend/src/pages/Join.tsx`, `frontend/src/App.tsx`, `docs/CONSENT.md`.
- **Why it matters:** The consent claim is visible but the promised notice is inaccessible.
- **Likely files:** `frontend/src/App.tsx`, a consent page/component, or the join page link.
- **Recommended fix:** Add a real route using the approved consent text or link to a valid existing resource.
- **Dependencies:** Final approved consent wording.
- **Verification:** Click the link from `/join/:code` and confirm the notice loads.

#### P1.2 Display/copy the join link

- **Problem:** Only the join code is shown in `Courses`.
- **Evidence:** `frontend/src/App.tsx`, while backend `courses.output()` returns `join_link`.
- **Why it matters:** The intended link-based student entry is not usable from the instructor UI.
- **Likely files:** `frontend/src/App.tsx`, possibly `api.ts`.
- **Recommended fix:** Display the full origin plus `join_link` and provide a copy action.
- **Dependencies:** Deployment origin.
- **Verification:** Copy link, open a separate browser session, and join.

#### P1.3 Add student chat loading and error states

- **Problem:** `Student.ask()` does not catch errors or expose a busy state.
- **Evidence:** `frontend/src/pages/Student.tsx`.
- **Why it matters:** Provider/network failures appear as broken or unresponsive UI.
- **Likely files:** `frontend/src/pages/Student.tsx`.
- **Recommended fix:** Add busy state, friendly error output, and preserve/retry the unsent question.
- **Dependencies:** Existing `friendlyError()` helper.
- **Verification:** Simulate 503 and confirm a readable error without losing prior messages.

#### P1.4 Distinguish material loading errors from empty state

- **Problem:** Material load failure becomes `[]`.
- **Evidence:** `frontend/src/pages/Student.tsx`.
- **Why it matters:** Students cannot tell whether a course has no materials or the API failed.
- **Likely files:** `frontend/src/pages/Student.tsx`.
- **Recommended fix:** Store/display an explicit error state with retry.
- **Verification:** Simulate a materials 500 and confirm an error state.

#### P1.5 Add logout/session-expiry handling

- **Problem:** No logout controls or redirect on 401.
- **Evidence:** `frontend/src/App.tsx`, `frontend/src/api.ts`.
- **Why it matters:** Separate instructor/student browser demonstrations can retain stale roles.
- **Likely files:** `frontend/src/App.tsx`, `frontend/src/api.ts`.
- **Recommended fix:** Add role-specific logout and centralized 401 cleanup/redirect.
- **Verification:** Logout clears the relevant token and protected pages return to entry.

#### P1.6 Validate course deletion and sharing controls in UI

- **Problem:** Backend supports deletion and code regeneration, but the visible instructor journey does not expose a complete control surface.
- **Evidence:** `courses.py`; `frontend/src/App.tsx`; `api.ts` has regeneration but no deletion helper.
- **Why it matters:** Important privacy and demo operations are API-only.
- **Likely files:** `frontend/src/App.tsx`, `frontend/src/api.ts`, course workspace components.
- **Recommended fix:** Add only the required delete/regenerate/open-close controls with confirmation.
- **Verification:** Perform the operation through UI and confirm course data/vector/file cleanup.

### P2 — Improvement that can wait until after the MVP

1. Replace FastAPI background tasks with a shared durable queue; see `docs/SCALING.md`.
2. Add browser-level full-stack tests.
3. Add explicit misconception evidence details.
4. Improve insight-group title generation and clustering validation.
5. Add stronger file-format signature/virus scanning appropriate to institutional deployment.
6. Add centralized observability for provider latency, indexing failures, and retry backlog.
7. Remove or migrate legacy quiz tables only after dependency confirmation.
8. Add formal retention/deletion governance beyond course deletion.

## 12. Final Verdict

**PARTIALLY FUNCTIONAL**

This verdict is supported by:

- `36 passed` backend tests when run from `backend`;
- `6 passed` frontend tests when run from `frontend`;
- successful TypeScript check and Vite production build;
- implemented authentication, course/topic APIs, consent enforcement, RAG code, analysis code, insight rules, and verdict endpoints;
- documented and verified gaps in real provider execution, upload-size configuration, citation display, consent navigation, durable jobs, frontend error handling, and classifier evaluation.

The repository is beyond a static prototype, but the complete MVP thesis has not been demonstrated end-to-end with real materials and real AI services. It should not be labelled presentation-ready until the P0 items are addressed or explicitly demonstrated with controlled manual evidence.

