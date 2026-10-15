import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from openai import APIError, APITimeoutError
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from ..adapters.jobs import FastAPIJobs
from ..config import settings
from ..db import session
from ..deps import current_student
from ..models import AnalysisJob, Concept, Course, Material, Message, Student
from ..services import rag
from ..services import analysis
from ..services.tokens import signed_material_url, student_token, valid_material_signature
from ..services.rate_limit import client_ip, enforce

router = APIRouter()
logger = logging.getLogger("tangled.student")


class JoinIn(BaseModel):
    code: str = Field(min_length=6, max_length=6)
    consent: bool


class ChatIn(BaseModel):
    text: str = Field(min_length=1, max_length=settings.max_chat_input_chars)
    session_id: str = Field(default="", max_length=100)


class FeedbackIn(BaseModel):
    message_id: int
    value: str


@router.get("/join/{code}")
def join_info(code: str, s: Session = Depends(session)):
    course = s.exec(select(Course).where(Course.join_code == code.upper())).first()
    if not course:
        raise HTTPException(404, "Course not found")
    return {"name": course.name, "joining_open": course.joining_open}


@router.post("/join")
def join(body: JoinIn, request: Request, s: Session = Depends(session)):
    enforce(f"join:{client_ip(request)}", settings.join_rate_limit_per_min)
    if not body.consent:
        raise HTTPException(400, "Consent is required")
    course = s.exec(select(Course).where(Course.join_code == body.code.upper())).first()
    if not course:
        raise HTTPException(404, "Course not found")
    if not course.joining_open:
        raise HTTPException(403, "Joining is closed")
    student = Student(course_id=course.id, consent_version=settings.consent_version)
    s.add(student)
    s.commit()
    s.refresh(student)
    return {"access_token": student_token(student.id, course.id), "token_type": "bearer",
            "course_id": course.id, "course_name": course.name}


def student_material(material: Material, student: Student) -> dict:
    return {"id": material.id, "filename": material.filename, "kind": material.kind,
            "size_kb": material.size_kb, "status": material.status, "chunks": material.chunks,
            "error": material.error, "file_url": signed_material_url(material.id, student.id)
            if material.kind == "PDF" and material.status == "indexed" else None}


@router.get("/materials")
def materials(st: Student = Depends(current_student), s: Session = Depends(session)):
    rows = s.exec(select(Material).where(Material.course_id == st.course_id)).all()
    return [student_material(material, st) for material in rows]


@router.get("/materials/{material_id}/file")
def material_file(material_id: int, student_id: int = Query(...), expires: int = Query(...),
                  signature: str = Query(...), s: Session = Depends(session)):
    if not valid_material_signature(material_id, student_id, expires, signature):
        raise HTTPException(401, "Invalid or expired file URL")
    material = s.get(Material, material_id)
    if not material or material.status != "indexed":
        raise HTTPException(404, "Material not found")
    student = s.get(Student, student_id)
    if not student or student.course_id != material.course_id:
        raise HTTPException(404, "Material not found")
    path = Path(settings.upload_dir) / f"{material.id}_{material.filename}"
    if not path.exists():
        raise HTTPException(404, "Material file not found")
    return FileResponse(path, filename=material.filename, media_type="application/pdf",
                        content_disposition_type="inline")


def enforce_rate_limit(student: Student, s: Session) -> None:
    since = datetime.now(timezone.utc) - timedelta(minutes=1)
    count = len(s.exec(select(Message).where(Message.student_id == student.id,
                                             Message.course_id == student.course_id,
                                             Message.created_at >= since)).all())
    if count >= settings.rate_limit_per_min:
        raise HTTPException(429, "Please wait before sending another question")


@router.post("/chat")
async def chat(body: ChatIn, background: BackgroundTasks,
               request: Request, st: Student = Depends(current_student), s: Session = Depends(session)):
    started = datetime.now(timezone.utc)
    enforce(f"chat-ip:{client_ip(request)}", settings.chat_ip_rate_limit_per_min)
    enforce(f"chat-student:{st.id}", settings.chat_student_rate_limit_per_min)
    enforce_rate_limit(st, s)
    hits = await asyncio.to_thread(rag.retrieve, st.course_id, body.text)
    similarity = hits[0]["sim"] if hits else 0.0
    topic_key = rag.topic_of(hits)
    concept = s.exec(select(Concept).where(Concept.course_id == st.course_id,
                                             Concept.key == topic_key)).first() if topic_key else None
    if rag.grounding_refused(hits):
        message = Message(course_id=st.course_id, student_id=st.id, session_id=body.session_id,
                          text=body.text, answer=rag.REFUSAL, concept_id=None,
                          similarity=similarity, intent="gap")
        s.add(message)
        s.commit()
        s.refresh(message)
        logger.info("chat_metrics student_id=%s latency_ms=%d retrieved=%d refusal=yes",
                    st.id, int((datetime.now(timezone.utc) - started).total_seconds() * 1000), len(hits))
        return {"message_id": message.id, "answer": rag.REFUSAL, "sources": []}
    try:
        answer, sources = await rag.answer(body.text, hits)
    except (APIError, APITimeoutError, ConnectionError, TimeoutError):
        raise HTTPException(503, "The tutor is temporarily unavailable. Please try again.")
    message = Message(course_id=st.course_id, student_id=st.id, session_id=body.session_id,
                      text=body.text, answer=answer, concept_id=concept.id if concept else None,
                      similarity=similarity, intent="" if concept else "gap")
    s.add(message)
    s.commit()
    s.refresh(message)
    if not s.exec(select(AnalysisJob).where(AnalysisJob.message_id == message.id)).first():
        s.add(AnalysisJob(message_id=message.id, course_id=st.course_id))
        s.commit()
    FastAPIJobs(background).enqueue(analysis.analyze, message.id)
    logger.info("chat_metrics student_id=%s latency_ms=%d retrieved=%d refusal=no",
                st.id, int((datetime.now(timezone.utc) - started).total_seconds() * 1000), len(hits))
    return {"message_id": message.id, "answer": answer, "sources": sources}


@router.get("/messages")
def messages(st: Student = Depends(current_student), s: Session = Depends(session)):
    rows = s.exec(select(Message).where(Message.student_id == st.id,
                                        Message.course_id == st.course_id)
                 .order_by(Message.created_at)).all()
    return [{"message_id": row.id, "question": row.text, "answer": row.answer,
             "feedback": row.feedback} for row in rows]


@router.post("/feedback")
def feedback(body: FeedbackIn, st: Student = Depends(current_student), s: Session = Depends(session)):
    if body.value not in ("clear", "unclear"):
        raise HTTPException(400, "Invalid feedback")
    message = s.exec(select(Message).where(Message.id == body.message_id,
                                            Message.student_id == st.id,
                                            Message.course_id == st.course_id)).first()
    if not message:
        raise HTTPException(404, "Message not found")
    message.feedback = body.value
    s.add(message)
    s.commit()
    return {"ok": True}
