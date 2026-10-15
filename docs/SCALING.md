# Scaling Tangled

The current deployment intentionally runs one worker because SQLite, local Chroma, and FastAPI background tasks are single-process components.

## Vertical scaling

Increase CPU and memory for the one container, keep one worker, and monitor request latency, embedding memory, LLM latency, and disk usage. Move uploads and backups to a larger persistent volume.

## Horizontal scale path

1. Change `DATABASE_URL` to PostgreSQL and review migrations.
2. Replace FastAPI background tasks behind the `Jobs` port with a shared queue and worker service.
3. Replace local Chroma behind `VectorStore` with a shared vector database.
4. Replace local `FileStorage` behind its port with object storage.
5. Move rate-limit state to a shared store.
6. Run multiple API workers behind the reverse proxy only after those swaps are complete.

Do not run multiple workers with the current SQLite, local Chroma, in-process limiter, and background-task setup.
