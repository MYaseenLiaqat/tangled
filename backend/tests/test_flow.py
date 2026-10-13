"""End to end: students chat -> background analysis -> quiz import -> dashboard flags the topic."""
from fastapi.testclient import TestClient
from sqlmodel import Session
from app.main import app
from app.services import analysis, rag
import seed
from app.db import engine
from app.models import Concept

T = {"Authorization": "tok"}


def test_confusion_flows_to_dashboard(monkeypatch):
    monkeypatch.setattr(rag, "retrieve", lambda q, k=4: [{"text": "Broadcasting rules", "meta": {"concept": "numpy", "material": "w1.pdf", "section": "p.3"}, "sim": 0.8}])
    async def fake_answer(q, hits): return "An answer [1]", [{"n": 1, "material": "w1.pdf", "section": "p.3"}]
    async def fake_judge(text, passage): return {"intent": "confusion", "misconception": True, "confidence": 0.9, "evidence_phrase": "I don't get it"}
    monkeypatch.setattr(rag, "answer", fake_answer)
    monkeypatch.setattr(analysis, "judge", fake_judge)
    monkeypatch.setattr(rag, "ef", lambda: (lambda texts: [[t.count(c) for c in "abcdefghijklmnopqrstuvwxyz"] for t in texts]))
    with TestClient(app) as c:
        with Session(engine) as s:
            for k, n, m, d in seed.CONCEPTS:
                s.add(Concept(key=k, name=n, module=m, description=d))
            s.commit()
        codes = c.post("/api/v1/teacher/students?count=6", headers=T).json()["codes"]
        for code in codes:
            for q in ("Why does broadcasting work? I don't get it", "Still, I don't get it, why (3,) plus (2,3)?"):
                r = c.post("/api/v1/student/chat", json={"text": q, "session_id": code}, headers={"X-Student-Code": code})
                assert r.status_code == 200 and r.json()["sources"]
        csv_body = "item,concept,student_code,answer,correct\n" + "\n".join(f"Q3,numpy,{x},{'D' if i == 0 else 'C'},{'yes' if i == 0 else 'no'}" for i, x in enumerate(codes))
        assert c.post("/api/v1/teacher/quiz/import", files={"file": ("q.csv", csv_body)}, headers=T).json()["imported"] == 6
        t = c.get("/api/v1/teacher/topics", headers=T).json()
        assert [f["name"] for f in t["flagged"]] == ["NumPy arrays"] and t["flagged"][0]["confidence"] == "High"
        d = c.get(f"/api/v1/teacher/topics/{t['flagged'][0]['id']}", headers=T).json()
        assert all(x["ok"] for x in d["checks"]) and d["groups"] and d["groups"][0]["items"][0]["phrase"] == "I don't get it"
        assert c.get("/api/v1/teacher/quiz", headers=T).json()[0]["top_wrong"]["option"] == "C"
        c.post(f"/api/v1/teacher/topics/{d['id']}/verdict", json={"verdict": "false_alarm"}, headers=T)
        assert c.get("/api/v1/teacher/topics", headers=T).json()["flagged"] == []
