from fastapi.testclient import TestClient
from app.main import app


def register(client, email):
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_register_login_me_and_course_lifecycle():
    with TestClient(app) as client:
        token = register(client, "a@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/v1/auth/me", headers=headers).json()["email"] == "a@example.com"
        assert client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "password123"}).status_code == 200
        course = client.post("/api/v1/courses", json={"name": "Data Science", "class_size": 20}, headers=headers).json()
        assert len(course["join_code"]) == 6
        assert "/join/" + course["join_code"] == course["join_link"]
        assert client.patch(f"/api/v1/courses/{course['id']}", json={"joining_open": False}, headers=headers).json()["joining_open"] is False


def test_course_isolation_and_regenerate_invalidates_old_code():
    with TestClient(app) as client:
        token_a = register(client, "owner-a@example.com")
        token_b = register(client, "owner-b@example.com")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}
        course = client.post("/api/v1/courses", json={"name": "Private"}, headers=headers_a).json()
        assert client.get(f"/api/v1/courses/{course['id']}", headers=headers_b).status_code == 404
        regenerated = client.post(f"/api/v1/courses/{course['id']}/join-code/regenerate", headers=headers_a).json()
        assert regenerated["join_code"] != course["join_code"]
        assert regenerated["join_link"] != course["join_link"]
        assert client.get("/api/v1/courses", headers=headers_b).json() == []
