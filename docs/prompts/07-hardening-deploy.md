# Phase 7: Privacy, hardening, deployment (F11, F12, E1)
Read `.github/copilot-instructions.md` and `docs/SCOPE.md`. Build ONLY F11, F12, E1.

Privacy: instructor "Delete course" removes rows, vectors and files in one transaction-safe job, with a typed confirmation; privacy page; consent text versioned and stored with the Student row.
Security: CORS from env, security headers, upload size limits at the proxy and app, request-size limit on chat, argon2 parameters documented, JWT expiry, rate limit on login and join endpoints, no secrets in logs; add `docs/SECURITY.md` listing known limits.
Deploy: one multi-stage Dockerfile (build frontend, copy into the API image, serve static files from FastAPI); entrypoint runs `alembic upgrade head` then uvicorn with ONE worker (documented why: local Chroma and SQLite are single-process);
`docker-compose.yml` with a mounted `data/` volume; `scripts/backup.sh` (copies sqlite + chroma + uploads with a timestamp); `docs/DEPLOY.md` with exact steps for a small VPS (or Render/Railway) including HTTPS and environment variables.
Observability: request-id logs, `/health/ready`, a simple metrics log line per chat (latency, retrieved count, refusal yes/no; no content).
Tests: delete-course leaves zero rows/vectors/files for that course and does not touch another course; rate limits; health endpoints.
Do NOT: add Kubernetes, Redis, Postgres, S3 adapters (they are future swaps behind the interfaces; only document the swap steps in `docs/SCALING.md`).
Done when: `docker compose up --build` serves the whole app on one port; tests pass.
