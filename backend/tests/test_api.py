from fastapi.testclient import TestClient
from app.main import app


def test_auth_and_empty_dashboard():
    with TestClient(app) as c:
        assert c.get("/api/health").json()["ok"]
        assert c.get("/api/teacher/topics").status_code == 401
        t = c.get("/api/teacher/topics", headers={"Authorization": "Bearer tok"}).json()
        assert t["flagged"] == []
        codes = c.post("/api/teacher/students?count=2", headers={"Authorization": "Bearer tok"}).json()["codes"]
        assert c.post("/api/student/login", json={"code": codes[0]}).json()["ok"]
        assert c.post("/api/student/login", json={"code": "NOPE"}).status_code == 401
        assert c.get("/api/student/materials", headers={"X-Student-Code": codes[0]}).json() == []
