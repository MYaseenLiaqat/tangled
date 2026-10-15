# Security notes

- Production startup refuses the default or short JWT secret, an empty LLM key, and wildcard CORS.
- Passwords use Argon2 through `argon2-cffi`; JWTs expire after 12 hours.
- Requests are capped by `REQUEST_MAX_BYTES`; uploads are capped by `MAX_UPLOAD_MB` and validated by extension and content.
- Login, join, and chat have configurable per-IP limits. Chat also has a per-student limit. The current in-process limiter is suitable for the documented one-worker deployment; a shared store is required before multiple workers.
- Security headers include content-type sniffing protection, frame protection, a referrer policy, and a restrictive content security policy.
- Logs contain request IDs and chat timing metrics only. Message text, answers, tokens, keys, and secrets are not logged.
- SQLite, local files, local Chroma, and FastAPI background tasks are single-worker MVP components.
