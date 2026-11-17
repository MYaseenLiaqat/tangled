import asyncio
from contextlib import asynccontextmanager
import json
import logging
import os
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import text
from .config import settings
from .db import engine, migrate
from .routers import auth, courses, student
from .services import analysis


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({"level": record.levelname, "message": record.getMessage(),
                           "logger": record.name, "request_id": getattr(record, "request_id", None)})


def configure_logging() -> None:
    """JSON logs at INFO. Re-applied after migrations, because alembic.ini resets the root logger."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


configure_logging()
logger = logging.getLogger("tangled")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_runtime()
    migrate()
    configure_logging()
    sweeper = (asyncio.create_task(analysis.retry_loop())
               if settings.analysis_retry_interval_s > 0 else None)
    yield
    if sweeper:
        sweeper.cancel()


app = FastAPI(title="Tangled API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_methods=["*"], allow_headers=["*"])
@app.middleware("http")
async def request_logging(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            body_size = int(content_length)
        except ValueError:
            response = JSONResponse(status_code=400, content={"detail": "Invalid request size."})
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response
        if body_size > settings.request_max_bytes:
            response = JSONResponse(status_code=413, content={"detail": "Request body is too large."})
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "same-origin"
            return response
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-src 'self' blob:; style-src 'self' 'unsafe-inline'"
    logger.info("%s %s %s %.3f", request.method, request.url.path, response.status_code,
                time.perf_counter() - started, extra={"request_id": request_id})
    return response


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["courses"])
app.include_router(student.router, prefix="/api/v1/student", tags=["student"])


@app.get("/health/live")
def health_live():
    return {"ok": True}


@app.get("/health/ready")
def health_ready():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"ok": True}


class SPAStaticFiles(StaticFiles):
    """Serve the built frontend; unknown page routes (e.g. /join/ABC123) get index.html.

    React Router owns those URLs, so a direct visit or refresh must load the app instead of a 404.
    API, health and docs paths, and missing asset files (anything with an extension), still 404.
    """
    API_PREFIXES = ("api/", "health/", "docs", "redoc", "openapi.json")

    async def get_response(self, path: str, scope):
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise
            response = None
        if response is not None and response.status_code != 404:
            return response
        clean = path.replace("\\", "/").lstrip("/")  # Starlette passes an OS path (backslashes on Windows)
        if clean.startswith(self.API_PREFIXES) or "." in clean.rsplit("/", 1)[-1]:
            raise StarletteHTTPException(status_code=404)
        return await super().get_response("index.html", scope)


def mount_frontend(target: FastAPI, directory: str) -> bool:
    if not os.path.isfile(os.path.join(directory, "index.html")):
        return False
    target.mount("/", SPAStaticFiles(directory=directory, html=True), name="frontend")
    return True


frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
mount_frontend(app, frontend_dist)
