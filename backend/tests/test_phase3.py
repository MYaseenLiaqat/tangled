from fastapi.testclient import TestClient
from app.main import app


def auth(client, email="phase3@example.com"):
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def course(client, headers):
    return client.post("/api/v1/courses", json={"name": "Topics"}, headers=headers).json()


def test_topic_limit_and_course_isolation():
    with TestClient(app) as client:
        headers = auth(client)
        first = course(client, headers)
        second = course(client, headers)
        for number in range(10):
            response = client.post(f"/api/v1/courses/{first['id']}/topics",
                                   json={"name": f"Topic {number}", "module_label": "Module",
                                         "description": "A useful topic."}, headers=headers)
            assert response.status_code == 200
        assert client.post(f"/api/v1/courses/{first['id']}/topics",
                           json={"name": "Too many", "module_label": "Module",
                                 "description": "A useful topic."}, headers=headers).status_code == 400
        assert client.get(f"/api/v1/courses/{second['id']}/topics", headers=headers).json() == []


def test_material_validation_and_pdf_scan_message(monkeypatch):
    with TestClient(app) as client:
        headers = auth(client, "materials@example.com")
        course_data = course(client, headers)
        base = f"/api/v1/courses/{course_data['id']}/materials"
        invalid = client.post(base, files={"files": ("notes.pdf", b"not a pdf", "application/pdf")}, headers=headers)
        assert invalid.status_code == 400
        monkeypatch.setattr("app.routers.courses.FastAPIJobs.enqueue", lambda self, *args, **kwargs: None)
        scan = client.post(base, files={"files": ("scan.pdf", b"%PDF-1.7 fake", "application/pdf")}, headers=headers)
        assert scan.status_code == 200
        assert scan.json()[0]["status"] == "processing"
