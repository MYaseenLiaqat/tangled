from fastapi.testclient import TestClient
from app.main import app


def test_quiz_import_is_aggregate_case_insensitive_and_replaces():
    with TestClient(app) as client:
        token = client.post("/api/v1/auth/register",
                            json={"email": "phase5-quiz@example.com", "password": "password123"}).json()["access_token"]
        headers = {"Authorization": "Bearer " + token}
        course = client.post("/api/v1/courses", headers=headers, json={"name": "Quiz"}).json()
        client.post(f"/api/v1/courses/{course['id']}/topics", headers=headers,
                    json={"name": "Foundation", "module_label": "M", "description": "Basics."})
        csv = "item,concept,option,count,correct\nq1,foundation,A,6,true\nq1,FOUNDATION,B,4,false\n"
        response = client.post(f"/api/v1/courses/{course['id']}/quiz/import",
                               headers=headers, files={"file": ("quiz.csv", csv, "text/csv")})
        assert response.status_code == 200
        assert response.json()["unmatched_concepts"] == []
        assert client.get(f"/api/v1/courses/{course['id']}/quiz", headers=headers).json()[0]["correct_rate"] == 0.6


def test_quiz_import_rejects_student_identifiers_and_reports_rows():
    with TestClient(app) as client:
        token = client.post("/api/v1/auth/register",
                            json={"email": "phase5-errors@example.com", "password": "password123"}).json()["access_token"]
        headers = {"Authorization": "Bearer " + token}
        course = client.post("/api/v1/courses", headers=headers, json={"name": "Errors"}).json()
        csv = "item,concept,option,count,correct,email\nq1,Unknown,A,nope,true,x@example.com\n"
        response = client.post(f"/api/v1/courses/{course['id']}/quiz/import",
                               headers=headers, files={"file": ("quiz.csv", csv, "text/csv")})
        assert response.status_code == 400
