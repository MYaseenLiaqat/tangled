"""End-to-end Phase 2 flow: instructor registration through course setup."""
from fastapi.testclient import TestClient
from app.main import app


def test_instructor_can_create_and_update_course():
    with TestClient(app) as client:
        response = client.post("/api/v1/auth/register", json={"email": "flow@example.com", "password": "password123"})
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        course = client.post("/api/v1/courses", json={"name": "Machine Learning"}, headers=headers).json()
        assert client.get("/api/v1/courses", headers=headers).json()[0]["name"] == "Machine Learning"
        updated = client.patch(f"/api/v1/courses/{course['id']}", json={"name": "ML", "class_size": 24}, headers=headers).json()
        assert updated["name"] == "ML"
        assert updated["class_size"] == 24
