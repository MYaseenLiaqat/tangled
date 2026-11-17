# Tangled MVP Readiness Checklist

| Check | Status | Evidence |
|---|---|---|
| Instructor registration/login/logout | PASS | Backend integration and frontend tests |
| Course creation/listing/settings | PASS | Backend lifecycle tests and mocked journey |
| Topic creation/edit/delete/ownership | PASS | Backend and frontend tests |
| Material upload/list/status/delete | PASS | API tests and mocked journey; real indexing not tested |
| Clean Alembic migration | PASS | Empty temporary SQLite database reached `0007_message_sources` |
| Backend startup and health | PASS | Uvicorn plus `/health/live` and `/health/ready` |
| Frontend startup | PASS | Vite root returned HTTP 200 |
| Student join and consent | PASS | Integration tests |
| Invalid/closed join handling | PASS | Existing backend tests |
| Returning student access/history | PASS | Integration tests |
| Chat/citations persistence | PASS | Integration tests and frontend tests |
| Out-of-scope refusal with real retrieval | NOT TESTED | Requires real Chroma/material data |
| Analysis persistence and retryable failure state | PASS | Mocked integration tests |
| Instructor insights and review actions | PASS | Mocked integration tests |
| Student privacy and course isolation | PASS | Backend tests |
| Real LLM provider | NOT TESTED | No real-provider run claimed |
| Real embedding/vector retrieval | NOT TESTED | No real-provider run claimed |
| Citation semantic groundedness | NOT TESTED | Requires manual real-document review |
| Separate browser journey | NOT TESTED | Browser automation/manual session not run |
| Docker image/Compose runtime | BLOCKED | Docker executable unavailable |
| Production persistence after restart | NOT TESTED | Requires deployed/container runtime |
| Backend regression suite | PASS | 44 passed, 1 warning |
| Frontend tests | PASS | 10 passed |
| Frontend build/type-check | PASS | Production build passed |
| Diff whitespace validation | PASS | `git diff --check` |

## Final verdict

**NOT READY**

The MVP is suitable for continued local demonstration with mocked/in-process verification. It is not ready for a controlled pilot until real provider, browser, and deployment checks pass.

