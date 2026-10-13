import asyncio
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from ..config import settings
from ..adapters.files import LocalFileStorage
from ..adapters.jobs import FastAPIJobs
from ..db import session
from ..deps import current_student
from ..models import Concept, Material, Message, Student
from ..services import analysis, rag

router = APIRouter()


class Login(BaseModel):
    code: str


class ChatIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    session_id: str = ""


class FeedbackIn(BaseModel):
    message_id: int
    value: str  # clear | unclear


@router.post("/login")
def login(b: Login, s: Session = Depends(session)):
    if not s.exec(select(Student).where(Student.code == b.code)).first():
        raise HTTPException(401, "Unknown student code")
    return {"ok": True}


@router.get("/materials")
def materials(_: Student = Depends(current_student), s: Session = Depends(session)):
    return [{"id": m.id, "filename": m.filename, "kind": m.kind, "size_kb": m.size_kb} for m in s.exec(select(Material)).all()]


@router.get("/materials/{mid}/file")
def material_file(mid: int, code: str, s: Session = Depends(session)):
    # the code is a query parameter because iframes cannot send custom headers
    if not s.exec(select(Student).where(Student.code == code)).first():
        raise HTTPException(401, "Unknown student code")
    m = s.get(Material, mid)
    p = Path(settings.upload_dir) / f"{mid}_{m.filename}" if m else None
    if not p or not p.exists():
        raise HTTPException(404)
    return FileResponse(p, filename=m.filename)


@router.post("/chat")
async def chat(b: ChatIn, bg: BackgroundTasks, st: Student = Depends(current_student), s: Session = Depends(session)):
    hits = await asyncio.to_thread(rag.retrieve, b.text)   # blocking vector search kept off the event loop
    answer, sources = await rag.answer(b.text, hits)
    key = rag.topic_of(hits)
    concept = s.exec(select(Concept).where(Concept.key == key)).first() if key else None
    m = Message(student_id=st.id, session_id=b.session_id, text=b.text, answer=answer, concept_id=concept.id if concept else None,
                similarity=hits[0]["sim"] if hits else 0.0, intent="" if concept else "gap")  # no topic match = possible material gap
    s.add(m)
    s.commit()
    s.refresh(m)
    if concept:
        FastAPIJobs(bg).enqueue(analysis.analyze, m.id)
    return {"message_id": m.id, "answer": answer, "sources": sources}


@router.post("/feedback")
def feedback(b: FeedbackIn, st: Student = Depends(current_student), s: Session = Depends(session)):
    m = s.get(Message, b.message_id)
    if not m or m.student_id != st.id or b.value not in ("clear", "unclear"):
        raise HTTPException(400)
    m.feedback = b.value
    s.add(m)
    s.commit()
    return {"ok": True}
