"""Regression tests for the launch blockers found in the 2026-11-16 demo-readiness audit."""
import asyncio
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import settings
from app.db import engine
from app.main import app, mount_frontend
from app.models import AnalysisJob, Course, Instructor, Message, Student
from app.services import analysis


# --- 1. production serving: deep links must load the app, not 404 ---------------------------------

def spa_client(tmp_path) -> TestClient:
    (tmp_path / "index.html").write_text("<html>tangled app</html>", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log(1)", encoding="utf-8")
    site = FastAPI()

    @site.get("/api/v1/ping")
    def ping():
        return {"ok": True}

    assert mount_frontend(site, str(tmp_path))
    return TestClient(site)


def test_join_link_and_refresh_serve_the_app(tmp_path):
    client = spa_client(tmp_path)
    for path in ("/", "/join/ABC123", "/student", "/courses/1/topics/2"):
        response = client.get(path)
        assert response.status_code == 200, path
        assert "tangled app" in response.text, path


def test_real_files_api_and_missing_assets_are_not_swallowed(tmp_path):
    client = spa_client(tmp_path)
    assert client.get("/assets/app.js").text == "console.log(1)"
    assert client.get("/api/v1/ping").json() == {"ok": True}
    assert client.get("/api/v1/does-not-exist").status_code == 404
    assert client.get("/health/nope").status_code == 404
    assert client.get("/assets/missing.js").status_code == 404


def test_mount_is_skipped_without_a_build(tmp_path):
    assert mount_frontend(FastAPI(), str(tmp_path)) is False


# --- 3. rate-limited analysis is retried automatically with backoff --------------------------------

def job(status: str, attempts: int, seconds_ago: float) -> AnalysisJob:
    return AnalysisJob(message_id=1, course_id=1, status=status, attempts=attempts,
                       updated_at=datetime.now(timezone.utc) - timedelta(seconds=seconds_ago))


def test_retry_backoff_schedule():
    now = datetime.now(timezone.utc)
    base = settings.analysis_retry_base_s
    assert analysis.due_for_retry(job("failed", 1, base + 1), now)
    assert not analysis.due_for_retry(job("failed", 1, base - 1), now)
    assert not analysis.due_for_retry(job("failed", 2, base + 1), now)       # second retry waits 2x
    assert analysis.due_for_retry(job("failed", 2, 2 * base + 1), now)
    assert not analysis.due_for_retry(job("done", 1, 10_000), now)
    assert not analysis.due_for_retry(job("failed", settings.analysis_max_retries, 10_000), now)
    assert analysis.due_for_retry(job("pending", 0, 0), now)                 # never started
    assert not analysis.due_for_retry(job("pending", 1, 1), now)             # still in flight


def test_rate_limited_analysis_recovers_on_the_next_sweep(monkeypatch):
    with TestClient(app):
        pass  # runs migrations on the test database
    with Session(engine) as s:
        instructor = Instructor(email="retry-sweep@example.com", password_hash="x")
        s.add(instructor); s.commit(); s.refresh(instructor)
        course = Course(instructor_id=instructor.id, name="Retry", join_code="RTRY01")
        s.add(course); s.commit(); s.refresh(course)
        student = Student(course_id=course.id, consent_version="v")
        s.add(student); s.commit(); s.refresh(student)
        message = Message(course_id=course.id, student_id=student.id, text="I don't understand this")
        s.add(message); s.commit(); s.refresh(message)
        message_id, course_id = message.id, course.id

    calls = {"n": 0}

    async def flaky(message, passage):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("429 rate limited")
        return analysis.Classification(intent="confusion", confidence=0.9, misconception=False,
                                       evidence_phrase="I don't understand")

    monkeypatch.setattr(analysis, "_classify", flaky)
    asyncio.run(analysis.analyze(message_id))
    with Session(engine) as s:
        failed = s.exec(select(AnalysisJob).where(AnalysisJob.message_id == message_id)).one()
        assert failed.status == "failed" and failed.attempts == 1

    later = datetime.now(timezone.utc) + timedelta(seconds=settings.analysis_retry_base_s + 1)
    assert asyncio.run(analysis.retry_due_jobs(later)) >= 1
    with Session(engine) as s:
        done = s.exec(select(AnalysisJob).where(AnalysisJob.message_id == message_id)).one()
        assert done.status == "done" and done.attempts == 2
        assert s.get(Message, message_id).intent == "confusion"
        assert done.course_id == course_id
