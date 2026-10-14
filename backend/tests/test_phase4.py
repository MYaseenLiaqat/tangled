import asyncio
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import jwt
from fastapi.testclient import TestClient
from app.config import settings
from app.db import engine
from app.main import app
from app.models import Material
from app.services import rag
from app.services.tokens import signed_material_url
from sqlmodel import Session


def register(client, email):
    return client.post("/api/v1/auth/register",
                        json={"email": email, "password": "password123"}).json()["access_token"]


def test_join_requires_consent_and_returns_scoped_student_token():
    with TestClient(app) as client:
        instructor = register(client, "phase4-owner@example.com")
        course = client.post("/api/v1/courses", headers={"Authorization": "Bearer " + instructor},
                             json={"name": "Consent"}).json()
        assert client.post("/api/v1/student/join", json={"code": course["join_code"], "consent": False}).status_code == 400
        response = client.post("/api/v1/student/join",
                               json={"code": course["join_code"], "consent": True})
        assert response.status_code == 200
        payload = jwt.decode(response.json()["access_token"], settings.jwt_secret, algorithms=["HS256"])
        assert payload["role"] == "student"
        assert payload["course_id"] == course["id"]
        assert payload["student_id"]


def test_role_boundaries_reject_tokens_in_both_directions():
    with TestClient(app) as client:
        instructor = register(client, "phase4-roles@example.com")
        headers = {"Authorization": "Bearer " + instructor}
        course = client.post("/api/v1/courses", headers=headers, json={"name": "Roles"}).json()
        student = client.post("/api/v1/student/join",
                              json={"code": course["join_code"], "consent": True}).json()["access_token"]
        assert client.get("/api/v1/student/materials", headers=headers).status_code == 401
        assert client.get("/api/v1/courses", headers={"Authorization": "Bearer " + student}).status_code == 401


def test_pdf_signed_url_returns_inline_pdf_and_rejects_tampering(tmp_path, monkeypatch):
    with TestClient(app) as client:
        instructor = register(client, "phase4-pdf@example.com")
        headers = {"Authorization": "Bearer " + instructor}
        course = client.post("/api/v1/courses", headers=headers, json={"name": "PDF"}).json()
        joined = client.post("/api/v1/student/join",
                             json={"code": course["join_code"], "consent": True}).json()
        with Session(engine) as db:
            material = Material(course_id=course["id"], filename="outline.pdf", kind="PDF", status="indexed")
            db.add(material)
            db.commit()
            db.refresh(material)
            monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
            (Path(settings.upload_dir) / f"{material.id}_{material.filename}").write_bytes(b"%PDF-1.7")
            signed = signed_material_url(material.id, jwt.decode(
                joined["access_token"], settings.jwt_secret, algorithms=["HS256"])["student_id"])
        response = client.get(signed)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "inline" in response.headers["content-disposition"]
        parsed = urlparse(signed)
        query = parse_qs(parsed.query)
        query["signature"] = ["tampered"]
        tampered = parsed._replace(query="&".join(f"{key}={values[0]}" for key, values in query.items())).geturl()
        assert client.get(tampered).status_code == 401


def test_grounding_threshold_controls_llm_call(monkeypatch):
    calls = []

    async def fake_chat(messages, **kwargs):
        calls.append(messages)
        return "Grounded answer [1]"

    monkeypatch.setattr(rag.llm, "chat", fake_chat)
    high = [{"text": "Foundation modules", "meta": {"material": "outline.pdf", "section": "Foundation"}, "sim": 0.8}]
    low = [{"text": "Unrelated", "meta": {"material": "outline.pdf", "section": "Other"}, "sim": 0.1}]
    assert asyncio.run(rag.answer("what will I study in foundation", high))[0] == "Grounded answer [1]"
    assert asyncio.run(rag.answer("unrelated", low)) == (rag.REFUSAL, [])
    assert len(calls) == 1
