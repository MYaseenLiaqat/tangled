from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db import engine
from app.main import app
from app.models import AnalysisJob, Message
from app.routers import courses
from app.services import analysis, rag
from app.services.analysis import Classification


def register(client: TestClient, email: str) -> str:
    response = client.post("/api/v1/auth/register",
                           json={"email": email, "password": "password123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_complete_instructor_student_analysis_and_review_journey(monkeypatch):
    async def no_retag(*args):
        return None

    def fake_retrieve(course_id: int, text: str, k: int | None = None):
        return [{"text": "Derivatives measure change.", "sim": 0.9,
                 "meta": {"material": "notes.txt", "section": "Derivatives",
                          "topic_key": topic_key}}]

    async def fake_answer(question: str, hits: list[dict]):
        return "A derivative measures change [1].", [
            {"n": 1, "material": "notes.txt", "section": "Derivatives"}]

    async def fake_classify(message, passage):
        return Classification(intent="confusion", confidence=0.95,
                              misconception=False, evidence_phrase="do not understand")

    monkeypatch.setattr(courses, "process_material", no_retag)
    monkeypatch.setattr(rag, "retrieve", fake_retrieve)
    monkeypatch.setattr(rag, "answer", fake_answer)
    monkeypatch.setattr(analysis, "_classify", fake_classify)

    with TestClient(app) as client:
        instructor_token = register(client, "phase41-owner@example.com")
        instructor_headers = auth(instructor_token)
        course = client.post("/api/v1/courses", headers=instructor_headers,
                             json={"name": "Calculus", "class_size": 4}).json()
        topic = client.post(f"/api/v1/courses/{course['id']}/topics",
                            headers=instructor_headers,
                            json={"name": "Derivatives", "module_label": "Limits",
                                  "description": "Derivatives measure change."}).json()
        topic_key = topic["key"]

        uploaded = client.post(f"/api/v1/courses/{course['id']}/materials",
                               headers=instructor_headers,
                               files={"files": ("notes.txt", b"Derivatives measure change.",
                                                "text/plain")})
        assert uploaded.status_code == 200
        assert uploaded.json()[0]["status"] == "processing"
        assert client.get(f"/api/v1/courses/{course['id']}/materials",
                          headers=instructor_headers).json()[0]["filename"] == "notes.txt"

        quiz = b"item,concept,option,count,correct\nQ1,Derivatives,A,1,false\nQ1,Derivatives,B,1,false\n"
        assert client.post(f"/api/v1/courses/{course['id']}/quiz/import",
                           headers=instructor_headers,
                           files={"file": ("quiz.csv", quiz, "text/csv")}).status_code == 200

        student_tokens = []
        for index in range(4):
            joined = client.post("/api/v1/student/join",
                                 json={"code": course["join_code"], "consent": True})
            assert joined.status_code == 200
            student_tokens.append(joined.json()["access_token"])
            response = client.post(
                "/api/v1/student/chat",
                headers=auth(student_tokens[-1]),
                json={"text": "I do not understand derivatives.", "session_id": f"s{index}"})
            assert response.status_code == 200
            assert response.json()["sources"] == [
                {"n": 1, "material": "notes.txt", "section": "Derivatives"}]

        first_history = client.get("/api/v1/student/messages",
                                   headers=auth(student_tokens[0]))
        assert first_history.status_code == 200
        assert first_history.json()[0]["sources"][0]["material"] == "notes.txt"

        with Session(engine) as session:
            message = session.exec(select(Message).where(
                Message.course_id == course["id"])).first()
            assert message is not None
            job = session.exec(select(AnalysisJob).where(
                AnalysisJob.message_id == message.id)).one()
            assert job.status == "done"
            assert message.intent == "confusion"
            assert message.concept_id == topic["id"]

        insights = client.get(f"/api/v1/courses/{course['id']}/insights",
                              headers=instructor_headers)
        assert insights.status_code == 200
        assert insights.json()["flagged"][0]["name"] == "Derivatives"

        detail = client.get(f"/api/v1/courses/{course['id']}/topics/{topic['id']}/insights",
                            headers=instructor_headers)
        assert detail.status_code == 200
        assert detail.json()["stats"]["confusion_msgs"] == "fewer than 5"
        assert client.post(f"/api/v1/courses/{course['id']}/topics/{topic['id']}/verdict",
                           headers=instructor_headers,
                           json={"verdict": "addressed"}).status_code == 200
        refreshed = client.get(f"/api/v1/courses/{course['id']}/insights",
                               headers=instructor_headers).json()
        assert refreshed["flagged"][0]["status"] == "addressed"


def test_student_join_is_idempotent_for_same_valid_token_and_isolated_between_students():
    with TestClient(app) as client:
        instructor_token = register(client, "phase41-idempotent@example.com")
        course = client.post("/api/v1/courses", headers=auth(instructor_token),
                             json={"name": "Privacy"}).json()
        first = client.post("/api/v1/student/join",
                            json={"code": course["join_code"], "consent": True}).json()
        repeated = client.post("/api/v1/student/join",
                               headers=auth(first["access_token"]),
                               json={"code": course["join_code"], "consent": True}).json()
        assert repeated["access_token"] == first["access_token"]
        second = client.post("/api/v1/student/join",
                             json={"code": course["join_code"], "consent": True}).json()
        assert second["access_token"] != first["access_token"]
        assert client.get("/api/v1/student/messages",
                          headers=auth(second["access_token"])).json() == []


def test_chat_provider_failure_does_not_persist_partial_message(monkeypatch):
    async def failed_answer(question: str, hits: list[dict]):
        raise TimeoutError

    monkeypatch.setattr(rag, "retrieve", lambda *args, **kwargs: [
        {"text": "Grounded", "sim": 0.9, "meta": {"material": "a.txt", "section": "A"}}])
    monkeypatch.setattr(rag, "answer", failed_answer)

    with TestClient(app) as client:
        instructor_token = register(client, "phase41-failure@example.com")
        course = client.post("/api/v1/courses", headers=auth(instructor_token),
                             json={"name": "Failures"}).json()
        student = client.post("/api/v1/student/join",
                              json={"code": course["join_code"], "consent": True}).json()
        response = client.post("/api/v1/student/chat",
                               headers=auth(student["access_token"]),
                               json={"text": "Question", "session_id": "failure"})
        assert response.status_code == 503
        assert client.get("/api/v1/student/messages",
                          headers=auth(student["access_token"])).json() == []


def test_analysis_failure_is_recorded_and_chat_remains_successful(monkeypatch):
    async def failed_classify(message, passage):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(rag, "retrieve", lambda *args, **kwargs: [
        {"text": "Grounded", "sim": 0.9, "meta": {"material": "a.txt", "section": "A"}}])

    async def grounded_answer(question: str, hits: list[dict]):
        return "Grounded answer", []

    monkeypatch.setattr(rag, "answer", grounded_answer)
    monkeypatch.setattr(analysis, "_classify", failed_classify)

    with TestClient(app) as client:
        instructor_token = register(client, "phase41-analysis-failure@example.com")
        course = client.post("/api/v1/courses", headers=auth(instructor_token),
                             json={"name": "Analysis failures"}).json()
        student = client.post("/api/v1/student/join",
                              json={"code": course["join_code"], "consent": True}).json()
        response = client.post("/api/v1/student/chat",
                               headers=auth(student["access_token"]),
                               json={"text": "Question", "session_id": "analysis-failure"})
        assert response.status_code == 200
        with Session(engine) as session:
            message = session.exec(select(Message).where(
                Message.session_id == "analysis-failure")).one()
            job = session.exec(select(AnalysisJob).where(
                AnalysisJob.message_id == message.id)).one()
            assert message.intent == "analysis_failed"
            assert job.status == "failed"
