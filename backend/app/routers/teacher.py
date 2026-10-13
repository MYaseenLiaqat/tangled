import csv
import io
import secrets
from collections import Counter
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, select
from ..config import settings
from ..db import session
from ..deps import teacher_auth
from ..models import Concept, Material, QuizItem, QuizResponse, Student, Verdict
from ..services import insights
from ..services.ingest import EXT, KIND, ingest

router = APIRouter(dependencies=[Depends(teacher_auth)])


class VerdictIn(BaseModel):
    verdict: str  # addressed | false_alarm


@router.get("/topics")
def topics(s: Session = Depends(session)):
    return insights.topics(s)


@router.get("/topics/{cid}")
def topic(cid: int, s: Session = Depends(session)):
    d = insights.detail(s, cid)
    if not d:
        raise HTTPException(404)
    return d


@router.post("/topics/{cid}/verdict")
def verdict(cid: int, b: VerdictIn, s: Session = Depends(session)):
    if b.verdict not in ("addressed", "false_alarm"):
        raise HTTPException(400)
    s.add(Verdict(concept_id=cid, verdict=b.verdict))   # false alarms become training/threshold feedback
    s.commit()
    return {"ok": True}


@router.get("/materials")
def materials(s: Session = Depends(session)):
    return s.exec(select(Material)).all()


@router.post("/materials")
def upload(files: list[UploadFile], s: Session = Depends(session)):
    concepts = s.exec(select(Concept)).all()
    out = []
    for f in files:
        ext = Path(f.filename).suffix.lower()
        if ext not in EXT:
            raise HTTPException(400, f"Unsupported file type: {ext}")
        data = f.file.read()
        m = Material(filename=f.filename, kind=KIND[ext], size_kb=max(1, len(data) // 1024), status="processing")
        s.add(m); s.commit(); s.refresh(m)
        p = Path(settings.upload_dir) / f"{m.id}_{f.filename}"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        m.chunks = ingest(p, m.id, concepts)   # synchronous for the pilot; move to a job queue if files get large
        m.status = "indexed"
        s.add(m); s.commit(); out.append(m)
    return out


@router.post("/students")
def make_codes(count: int = 24, s: Session = Depends(session)):
    codes = [secrets.token_hex(3).upper() for _ in range(min(count, 200))]
    for c in codes:
        s.add(Student(code=c))
    s.commit()
    return {"codes": codes}


@router.post("/quiz/import")
def quiz_import(file: UploadFile, s: Session = Depends(session)):
    """CSV columns: item, concept, student_code, answer, correct"""
    rows = list(csv.DictReader(io.StringIO(file.file.read().decode("utf-8-sig"))))
    n = 0
    for r in rows:
        c = s.exec(select(Concept).where(Concept.key == r["concept"].strip())).first()
        st = s.exec(select(Student).where(Student.code == r["student_code"].strip())).first()
        if not c or not st:
            continue
        it = s.exec(select(QuizItem).where(QuizItem.key == r["item"].strip())).first() or QuizItem(key=r["item"].strip(), concept_id=c.id)
        s.add(it); s.commit(); s.refresh(it)
        s.add(QuizResponse(item_id=it.id, student_id=st.id, option=r["answer"].strip(), correct=r["correct"].strip().lower() in ("yes", "true", "1")))
        n += 1
    s.commit()
    return {"imported": n}


@router.get("/quiz")
def quiz(s: Session = Depends(session)):
    out = []
    for it in s.exec(select(QuizItem)).all():
        rs = s.exec(select(QuizResponse).where(QuizResponse.item_id == it.id)).all()
        if not rs:
            continue
        wrong = Counter(r.option for r in rs if not r.correct).most_common(1)
        c = s.get(Concept, it.concept_id)
        out.append({"item": it.key, "topic": c.name, "correct_rate": round(sum(r.correct for r in rs) / len(rs), 3), "responses": len(rs),
                    "top_wrong": {"option": wrong[0][0], "count": wrong[0][1]} if wrong else None})
    return sorted(out, key=lambda x: x["correct_rate"])
