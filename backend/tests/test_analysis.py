import asyncio
from app.models import AnalysisJob, Concept, Message, Student
from app.services import analysis
from app.services.analysis import parse_json
from sqlmodel import Session, select
from app.db import engine


def test_parse_json_tolerates_fences_and_extra_text():
    result = parse_json('```json\n{"intent":"confusion","confidence":0.8,"misconception":false,"evidence_phrase":"do not get"}\n```')
    assert result.intent == "confusion"


def test_invalid_json_marks_job_failed(monkeypatch):
    async def bad_chat(*args, **kwargs):
        return "not json"

    monkeypatch.setattr(analysis.llm, "chat", bad_chat)
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app):
        with Session(engine) as s:
            student = Student(course_id=1, consent_version="test")
            s.add(student)
            s.commit()
            s.refresh(student)
            message = Message(course_id=1, student_id=student.id, text="I do not get this")
            s.add(message)
            s.commit()
            s.refresh(message)
            job = AnalysisJob(message_id=message.id, course_id=1)
            s.add(job)
            s.commit()
            asyncio.run(analysis.analyze(message.id))
            s.refresh(job)
            assert job.status == "failed"
