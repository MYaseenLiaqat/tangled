import jwt
from fastapi.testclient import TestClient
from app.config import settings
from app.main import app


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
