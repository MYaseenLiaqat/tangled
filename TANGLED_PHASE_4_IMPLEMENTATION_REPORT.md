# Tangled Phase 4 Implementation Report

## Scope

Phase 4 connected the existing instructor, student, materials, chat, and consent surfaces without changing classifier prompts, learning-signal thresholds, aggregation rules, RAG behavior, or unrelated database entities.

## Implemented

- Protected instructor and student application routes with token-presence guards while retaining backend authorization as the source of truth.
- Added instructor course settings controls for name, optional class size, joining open/closed state, join-code regeneration, and destructive course deletion confirmation.
- Replaced the stale materials page API calls with the existing course-scoped material APIs.
- Added student loading, empty, busy, duplicate-submit, and tutor-error states.
- Persisted answer citations on messages through `sources_json`, returned them from student message history, and rendered only valid citations and source metadata.
- Preserved closed-course handling and consent enforcement on the student join flow.

## Boundaries

The existing pseudonymous student model remains unchanged. Frontend token guards are not a security boundary; every backend route still validates the token and course ownership. Non-PDF material previews and other features explicitly outside `docs/SCOPE.md` remain out of scope.

## Migration

Alembic migration `0007_message_sources` was upgraded successfully from `0006_insight_groups` to head against the configured local SQLite database.

## Phase 4.1 requirement checklist

| Requirement | Status |
|---|---|
| Instructor registration, login, logout | Complete and tested |
| Course creation, listing, opening, editing, and persistent settings | Complete and tested |
| Join-code display, regeneration, and closed-course handling | Complete and tested |
| Topic creation, editing, deletion, and course ownership | Complete and tested |
| Material upload, listing, processing status, and deletion | Implemented but not fully tested with real indexing |
| Valid join requires consent | Complete and tested |
| Invalid and closed join handling | Complete and tested |
| Duplicate join prevention for the same valid anonymous token | Complete and tested |
| Returning student access with a persisted token | Complete and tested at API level |
| Conversation history and citation persistence | Complete and tested |
| Course context in the student UI | Implemented but not fully tested in a browser |
| Student and cross-course isolation | Complete and tested |
| Chat loading, provider errors, and duplicate-submit protection | Implemented but not fully tested in a browser |
| Message-to-analysis-to-topic-to-insight pipeline | Complete and tested with mocked providers |
| Analysis failure recording and retryable job state | Complete and tested with mocked providers |
| Distinct-student aggregation and information exclusion | Complete and tested |
| Insight detail and review verdict persistence | Complete and tested |
| Real-provider end-to-end journey | Implemented but not fully tested |
| Full browser journey and deployment startup | Implemented but not fully tested |

Anonymous duplicate enrollment across different browsers or devices is not identifiable by design; preventing it would require collecting an identity outside the MVP privacy contract. Real LLM, vector-store, and material-indexing behavior remains separate from the mocked integration evidence.

## Phase 4.2 final functional gap check

The final audit found no critical missing MVP workflow, disconnected frontend API call, or new authorization bypass. The complete mocked instructor-to-student-to-instructor journey is covered by `backend/tests/test_phase4_1.py`.

Remaining release blockers are verification gaps rather than identified code defects:

- Real LLM and vector-provider behavior has not been rerun as part of this final check.
- A real browser journey has not been executed.
- Material processing and citation groundedness still require a configured-provider/manual check.
- Deployment startup migration execution is covered by the migration command, but not by a deployed container run.

The MVP is functionally complete for mocked/in-process verification, but should not be called production-validated until those checks are completed.
