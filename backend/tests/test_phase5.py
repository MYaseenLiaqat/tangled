from fastapi.testclient import TestClient
from app.main import app


def register(client, email):
    return client.post("/api/v1/auth/register",
                       json={"email": email, "password": "password123"}).json()["access_token"]


def test_topic_list_is_course_scoped_and_instructor_only():
    with TestClient(app) as client:
        owner = register(client, "phase5-topic-owner@example.com")
        other = register(client, "phase5-topic-other@example.com")
        owner_headers = {"Authorization": "Bearer " + owner}
        other_headers = {"Authorization": "Bearer " + other}
        course = client.post("/api/v1/courses", headers=owner_headers,
                             json={"name": "Topic list"}).json()
        created = client.post(f"/api/v1/courses/{course['id']}/topics", headers=owner_headers,
                              json={"name": "Foundation", "module_label": "Module 1",
                                    "description": "Core foundations."})
        assert created.status_code == 200
        topics = client.get(f"/api/v1/courses/{course['id']}/topic-list",
                            headers=owner_headers)
        assert topics.status_code == 200
        assert topics.json() == [{"id": created.json()["id"], "name": "Foundation",
                                  "description": "Core foundations.", "module_label": "Module 1"}]
        updated = client.patch(f"/api/v1/courses/{course['id']}/topics/{created.json()['id']}",
                               headers=owner_headers,
                               json={"name": "Updated foundation", "description": "Updated basics."})
        assert updated.status_code == 200
        assert updated.json()["name"] == "Updated foundation"
        deleted = client.delete(f"/api/v1/courses/{course['id']}/topics/{created.json()['id']}",
                                headers=owner_headers)
        assert deleted.status_code == 200
        assert deleted.json() == {"ok": True}
        assert client.get(f"/api/v1/courses/{course['id']}/topic-list",
                          headers=other_headers).status_code == 404
        student = client.post("/api/v1/student/join",
                              json={"code": course["join_code"], "consent": True}).json()["access_token"]
        assert client.get(f"/api/v1/courses/{course['id']}/topic-list",
                          headers={"Authorization": "Bearer " + student}).status_code == 401


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
