# Deploying Tangled on a small VPS

## 1. Install prerequisites

Install Docker Engine and the Compose plugin, then clone this repository on the VPS.

## 2. Configure secrets

Copy `backend/.env.example` to `.env`. Set `ENV=prod`, a random `JWT_SECRET` of at least 32 characters, a valid `LLM_API_KEY`, and `CORS_ORIGINS` for the public origin. Keep `.env` out of version control.

## 3. Start the service

Run:

```sh
docker compose up --build -d
```

The proxy listens on port 80 and forwards `/api` and the frontend to the single-worker FastAPI container. The app runs migrations and pre-warms embeddings before uvicorn starts.

## 4. Add HTTPS

Put a managed TLS reverse proxy such as Caddy or the VPS provider's HTTPS proxy in front of port 80, or terminate TLS at Nginx with certificates from Let's Encrypt. Set `CORS_ORIGINS` to the HTTPS origin, then restart the stack.

## 5. Back up data

Run `TANGLED_DATA_DIR=./backend/data sh scripts/backup.sh ./backups` regularly and copy the resulting archive off the VPS. For the Compose volume, run the script from a temporary helper container or copy the volume contents to `./backend/data` first. The archive contains SQLite, Chroma, and uploaded files. Test restoring an archive on a separate machine.

## 6. Health check and updates

Check `/health/live` and `/health/ready`. Pull updates and run `docker compose up --build -d`; the entrypoint applies migrations before serving traffic.

SQLite and local Chroma are the default MVP storage. PostgreSQL and shared services are the horizontal-scale path described in `docs/SCALING.md`.
