# Phase 1: Baseline (no new features)
Goal: turn the downloaded foundation into a clean, scalable skeleton. Do NOT add product features this phase.
Read `.github/copilot-instructions.md` and `docs/SCOPE.md` first.

Tasks:
1. Add Alembic to `backend/` with an initial migration of the current models. `init()`/`create_all` must be removed; the app runs migrations on start (`alembic upgrade head`).
2. Restructure config: `app/config.py` Settings with env vars for DATABASE_URL, JWT_SECRET, ENV (dev|prod; prod refuses to start with default secrets), LLM settings, thresholds (MIN_SIMILARITY, MIN_CONF, MIN_STUDENTS, QUIZ_LOW), MAX_UPLOAD_MB, RATE_LIMIT_PER_MIN.
3. Create interfaces in `app/ports/`: `VectorStore` (add, query, delete_by_material, count), `FileStorage` (save, open, delete), `Jobs` (enqueue). One implementation each in `app/adapters/` (Chroma, local disk, FastAPI background tasks). Move all Chroma/disk code behind them. Services use only the interfaces.
4. Move the API under `/api/v1`. Add `/health/live` and `/health/ready` (ready checks the DB).
5. Add structured JSON logging with a request id; never log message text or tokens.
6. Add `.github/workflows/ci.yml`: on push run backend `pytest -q` and frontend `npm ci && npm run build`.
7. Keep the existing tests passing (adjust paths). Add one test per interface using an in-memory fake.
Do NOT: add auth, courses, new endpoints beyond health, new UI, or new dependencies except alembic and structlog (or std logging).
Done when: `pytest -q` and `npm run build` pass, `alembic upgrade head` creates the DB from empty, app starts with one command.
Human check: run the app, open /docs, confirm /health/ready returns ok.
