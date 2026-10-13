from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import init
from .routers import student, teacher


@asynccontextmanager
async def lifespan(_: FastAPI):
    init()
    yield


app = FastAPI(title="Tangled API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
app.include_router(student.router, prefix="/api/student", tags=["student"])
app.include_router(teacher.router, prefix="/api/teacher", tags=["teacher"])


@app.get("/api/health")
def health():
    return {"ok": True}
