from contextlib import asynccontextmanager
import json
import logging
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import text
from .config import settings
from .db import engine, migrate
from .routers import auth, courses, student


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({"level": record.levelname, "message": record.getMessage(),
                           "logger": record.name, "request_id": getattr(record, "request_id", None)})


logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
for handler in logging.getLogger().handlers:
    handler.setFormatter(JsonFormatter())
logger = logging.getLogger("tangled")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_runtime()
    migrate()
    yield


app = FastAPI(title="Tangled API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
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
