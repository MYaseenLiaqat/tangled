import logging
from pathlib import Path
import jwt
from fastapi.testclient import TestClient
from starlette.requests import Request
from sqlmodel import Session, select
from app.config import settings
from app.db import engine
from app.main import app
from app.models import AnalysisJob, Concept, Course, InsightGroup, Material, Message, QuizAggregate, Student, Verdict
from app.services import course_deletion, rate_limit


def register(client, email):
    return client.post("/api/v1/auth/register",
                       json={"email": email, "password": "password123"}).json()["access_token"]


def test_delete_course_removes_owned_data_files_and_vectors(monkeypatch, tmp_path):
    deleted_vectors = []
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(course_deletion, "ChromaVectorStore",
                        lambda: type("Vectors", (), {"delete_by_course": lambda self, course_id: deleted_vectors.append(course_id)})())
    with TestClient(app) as client:
        token = register(client, "phase7-delete@example.com")
        headers = {"Authorization": "Bearer " + token}
        first = client.post("/api/v1/courses", headers=headers, json={"name": "Delete me"}).json()
        second = client.post("/api/v1/courses", headers=headers, json={"name": "Keep me"}).json()
        topic = client.post(f"/api/v1/courses/{first['id']}/topics", headers=headers,
                            json={"name": "Topic", "module_label": "M", "description": "Basics."}).json()
        with Session(engine) as s:
            student = Student(course_id=first["id"], consent_version="test")
            material = Material(course_id=first["id"], filename="notes.txt", kind="TXT")
            s.add(student)
            s.add(material)
            s.commit()
            s.refresh(student)
            s.refresh(material)
            message = Message(course_id=first["id"], student_id=student.id, text="known private question")
            s.add(message)
            s.commit()
            s.refresh(message)
            s.add(AnalysisJob(message_id=message.id, course_id=first["id"]))
            s.add(QuizAggregate(course_id=first["id"], item="q", concept_id=topic["id"],
                                concept_name="Topic", option="A", count=1, correct=False))
            s.add(InsightGroup(course_id=first["id"], concept_id=topic["id"],
                               fingerprint="x", title="title"))
            s.add(Verdict(course_id=first["id"], concept_id=topic["id"], verdict="addressed"))
            s.commit()
            (tmp_path / f"{material.id}_{material.filename}").write_text("file")
        response = client.request("DELETE", f"/api/v1/courses/{first['id']}",
                                  headers=headers, json={"confirmation": "Delete me"})
        assert response.status_code == 200
        assert not (tmp_path / f"{material.id}_{material.filename}").exists()
        assert deleted_vectors == [first["id"]]
        with Session(engine) as s:
            assert s.get(Course, first["id"]) is None
            for model in (Student, Message, AnalysisJob, QuizAggregate, InsightGroup,
                          Verdict, Material, Concept):
                assert not s.exec(select(model).where(model.course_id == first["id"])).all()
            assert s.get(Course, second["id"]) is not None


def test_production_runtime_checks():
    original = (settings.env, settings.jwt_secret, settings.llm_api_key, settings.cors_origins)
    try:
        settings.env = "prod"
        settings.jwt_secret = "short"
        settings.llm_api_key = ""
        settings.cors_origins = "*"
        try:
            settings.validate_runtime()
        except ValueError as exc:
            assert "JWT_SECRET" in str(exc)
            assert "LLM_API_KEY" in str(exc)
            assert "CORS_ORIGINS" in str(exc)
        else:
            raise AssertionError("production checks did not reject unsafe settings")
    finally:
        settings.env, settings.jwt_secret, settings.llm_api_key, settings.cors_origins = original


def test_rate_limit_is_enforced_and_request_headers_are_safe(monkeypatch):
    rate_limit._events.clear()
    monkeypatch.setattr(settings, "login_rate_limit_per_min", 1)
    with TestClient(app) as client:
        payload = {"email": "phase7-rate@example.com", "password": "password123"}
        assert client.post("/api/v1/auth/login", json=payload).status_code in (401, 429)
        assert client.post("/api/v1/auth/login", json=payload).status_code == 429
        response = client.get("/health/live")
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"


def test_chat_logs_do_not_include_message_text(monkeypatch, caplog):
    rate_limit._events.clear()
    with TestClient(app) as client:
        token = register(client, "phase7-privacy@example.com")
        headers = {"Authorization": "Bearer " + token}
        course = client.post("/api/v1/courses", headers=headers, json={"name": "Privacy"}).json()
        student = client.post("/api/v1/student/join",
                              json={"code": course["join_code"], "consent": True}).json()["access_token"]
        caplog.set_level(logging.INFO)
        private_text = "unique private message 7f91"
        monkeypatch.setattr("app.routers.student.rag.retrieve", lambda *args: [])
        response = client.post("/api/v1/student/chat",
                               headers={"Authorization": "Bearer " + student},
                               json={"text": private_text})
        assert response.status_code == 200
        assert private_text not in caplog.text
        instructor_response = client.get(f"/api/v1/courses/{course['id']}/insights", headers=headers)
        assert instructor_response.status_code == 200
        assert private_text not in instructor_response.text
        assert "student_id" not in instructor_response.text


def test_request_body_limit_returns_friendly_error(monkeypatch):
    monkeypatch.setattr(settings, "request_max_bytes", 10)
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/login",
                               json={"email": "large@example.com", "password": "password123"})
        assert response.status_code == 413
        assert response.json()["detail"] == "Request body is too large."


def test_thirty_students_can_join_and_chat_from_one_ip(monkeypatch):
    rate_limit._events.clear()
    monkeypatch.setattr(settings, "trusted_proxy", "")
    monkeypatch.setattr(settings, "join_rate_limit_per_min", 100)
    monkeypatch.setattr(settings, "chat_ip_rate_limit_per_min", 120)
    monkeypatch.setattr(settings, "chat_student_rate_limit_per_min", 60)
    monkeypatch.setattr("app.routers.student.rag.retrieve", lambda *args: [])
    with TestClient(app, client=("198.51.100.10", 5000)) as client:
        token = register(client, "phase7-classroom@example.com")
        headers = {"Authorization": "Bearer " + token}
        course = client.post("/api/v1/courses", headers=headers,
                             json={"name": "Classroom"}).json()
        student_tokens = []
        for _ in range(30):
            response = client.post("/api/v1/student/join",
                                   json={"code": course["join_code"], "consent": True})
            assert response.status_code == 200
            student_tokens.append(response.json()["access_token"])
        for student_token in student_tokens:
            response = client.post("/api/v1/student/chat",
                                   headers={"Authorization": "Bearer " + student_token},
                                   json={"text": "What is this?"})
            assert response.status_code == 200


def test_forwarded_client_ip_is_used_only_for_trusted_proxy(monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy", "10.0.0.0/8")
    trusted_request = Request({
        "type": "http",
        "client": ("10.1.2.3", 5000),
        "headers": [(b"x-forwarded-for", b"198.51.100.10")],
    })
    assert rate_limit.client_ip(trusted_request) == "198.51.100.10"
    untrusted_request = Request({
        "type": "http",
        "client": ("192.0.2.10", 5000),
        "headers": [(b"x-forwarded-for", b"198.51.100.10")],
    })
    assert rate_limit.client_ip(untrusted_request) == "192.0.2.10"
