from fastapi.testclient import TestClient
from app.main import app


def test_auth_and_empty_dashboard():
    with TestClient(app) as c:
        assert c.get("/health/live").json()["ok"]
        assert c.get("/api/v1/teacher/topics").status_code == 401
        t = c.get("/api/v1/teacher/topics", headers={"Authorization": "tok"}).json()
        assert t["flagged"] == []
        codes = c.post("/api/v1/teacher/students?count=2", headers={"Authorization": "tok"}).json()["codes"]
        assert c.post("/api/v1/student/login", json={"code": codes[0]}).json()["ok"]
        assert c.post("/api/v1/student/login", json={"code": "NOPE"}).status_code == 401
        assert c.get("/api/v1/student/materials", headers={"X-Student-Code": codes[0]}).json() == []
