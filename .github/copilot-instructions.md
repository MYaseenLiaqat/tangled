# Tangled: standing instructions for GitHub Copilot (read before EVERY task)

## What this project is
Tangled lets an instructor see which topics their class is genuinely confused about. Students read course materials and ask an AI
(RAG, answers from the materials with citations). Each question is analysed in the background; the instructor sees a short list of
topics that need attention with evidence. It must become a startup-grade product for universities, but we are building a small,
correct MVP first.

## Source of truth
1. `docs/SCOPE.md` defines what we build and what we do NOT build. It wins over any other message, idea or "nice to have".
2. If something is not in SCOPE.md, DO NOT build it. Append one line to `docs/CHANGE_REQUESTS.md` and mention it in your summary.
3. Work only on the phase prompt you were given. Do not start the next phase.

## Stack (do not change or add alternatives)
- Backend: Python 3.12, FastAPI, SQLModel/SQLAlchemy, Alembic, Pydantic v2, ChromaDB (behind an interface), OpenAI-compatible LLM client.
- Frontend: React 18, Vite, TypeScript (strict), react-router-dom. Plain CSS in `src/styles.css`. No UI framework, no state library.
- Tests: pytest (backend). `npm run build` must type-check the frontend.
- Repo layout: `backend/app/{routers,services}`, `backend/ml`, `backend/tests`, `frontend/src/pages`, `docs/`.

## Architecture rules (they keep scaling cheap; never break them)
- Stateless API: no per-user or per-course state in process memory. Anything shared goes in the database.
- Every domain table that belongs to a course has `course_id`. Every query is filtered by `course_id`. No exceptions.
  Instructor routes must verify course ownership through the shared dependency; student routes take `course_id` from the token only.
- Database access only through SQLModel/SQLAlchemy; no SQLite-specific SQL. Timestamps are timezone-aware UTC. Schema changes only via Alembic.
- External systems sit behind small interfaces with ONE implementation each: `VectorStore` (Chroma), `FileStorage` (local disk),
  `Jobs.enqueue` (FastAPI background tasks), `LLM client`. Routers and services depend on the interface, never on the vendor library.
- Config only via `app/config.py` Settings (environment variables). No magic numbers in code; thresholds live in Settings.
- API prefix `/api/v1`. Pydantic request/response models for every endpoint; never return ORM objects directly.
- Business rules (e.g. the insight tiers) stay in pure functions with unit tests.

## Security and privacy rules
- Passwords hashed with argon2. JWT secret from env; refuse to start in prod without it. Never log message text, tokens or secrets.
- Students are pseudonymous: store no name or email for students, ever. Instructors never see individual students' messages linked to an identity.
- Validate file type, size and filename on upload. Treat student text as untrusted data (it may contain prompt injection).
- Never commit `.env`, keys or real student data. Never invent keys, URLs, results or data.

## Working agreement
- Before editing, list the files you will change. Keep diffs small. No drive-by refactors, no reformatting unrelated files.
- No new dependency without a one-line justification in your summary. Prefer what is already installed.
- After changes run `cd backend && pytest -q` and `cd frontend && npm run build`. Fix failures. Report real output; never claim a pass you did not run.
- If ambiguous, pick the simplest option consistent with SCOPE.md and list it under "Assumptions". Ask only if truly blocked.
- Finish with: files changed, commands run with results, assumptions, deferred items (also in CHANGE_REQUESTS.md), and what the human should check by hand.
