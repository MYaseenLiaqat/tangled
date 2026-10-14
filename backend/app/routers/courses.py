import re
import secrets
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from ..adapters.files import LocalFileStorage
from ..adapters.jobs import FastAPIJobs
from ..config import settings
from ..db import session
from ..deps import current_instructor, get_owned_course
from ..models import Concept, Course, Instructor, Material
from ..services.ingest import EXT, KIND
from ..services.materials import process_material, retag_course

router = APIRouter()
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_join_code(s: Session) -> str:
    while True:
        code = "".join(secrets.choice(ALPHABET) for _ in range(6))
        if not s.exec(select(Course).where(Course.join_code == code)).first():
            return code


class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    class_size: int | None = Field(default=None, ge=1)


class CourseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    class_size: int | None = Field(default=None, ge=1)
    joining_open: bool | None = None


class TopicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    module_label: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=300)


class TopicUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    module_label: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=300)


def validate_description(description: str) -> str:
    if len(re.findall(r"[.!?]", description)) > 1:
        raise ValueError("Description must be one sentence")
    return description


def topic_key(name: str, course_id: int, s: Session) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "topic"
    key = base
    suffix = 1
    while s.exec(select(Concept).where(Concept.key == key)).first():
        suffix += 1
        key = f"{base}-{course_id}-{suffix}"
    return key


def output(course: Course) -> dict:
    return {"id": course.id, "name": course.name, "class_size": course.class_size,
            "join_code": course.join_code, "join_link": f"/join/{course.join_code}",
            "joining_open": course.joining_open, "created_at": course.created_at}


@router.post("")
def create(body: CourseCreate, instructor: Instructor = Depends(current_instructor), s: Session = Depends(session)):
    course = Course(instructor_id=instructor.id, name=body.name, class_size=body.class_size, join_code=new_join_code(s))
    s.add(course)
    s.commit()
    s.refresh(course)
    return output(course)


@router.get("")
def list_courses(instructor: Instructor = Depends(current_instructor), s: Session = Depends(session)):
    return [output(c) for c in s.exec(select(Course).where(Course.instructor_id == instructor.id)).all()]


@router.get("/{course_id}")
def get_course(course: Course = Depends(get_owned_course)):
    return output(course)


@router.patch("/{course_id}")
def update_course(body: CourseUpdate, course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    values = body.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(course, key, value)
    s.add(course)
    s.commit()
    s.refresh(course)
    return output(course)


@router.post("/{course_id}/join-code/regenerate")
def regenerate(course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    course.join_code = new_join_code(s)
    s.add(course)
    s.commit()
    s.refresh(course)
    return output(course)


@router.get("/{course_id}/topics")
def list_topics(course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    topics = s.exec(select(Concept).where(Concept.course_id == course.id)).all()
    return [{"id": t.id, "name": t.name, "module_label": t.module, "description": t.description, "key": t.key}
            for t in topics]


@router.post("/{course_id}/topics")
def create_topic(body: TopicCreate, background: BackgroundTasks,
                 course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    if len(s.exec(select(Concept).where(Concept.course_id == course.id)).all()) >= 10:
        raise HTTPException(400, "A course can have at most 10 topics")
    try:
        description = validate_description(body.description)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    topic = Concept(course_id=course.id, key=topic_key(body.name, course.id, s), name=body.name,
                    module=body.module_label, description=description)
    s.add(topic)
    s.commit()
    s.refresh(topic)
    FastAPIJobs(background).enqueue(retag_course, course.id)
    return {"id": topic.id, "name": topic.name, "module_label": topic.module,
            "description": topic.description, "key": topic.key}


@router.patch("/{course_id}/topics/{topic_id}")
def update_topic(topic_id: int, body: TopicUpdate, background: BackgroundTasks,
                 course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    topic = s.exec(select(Concept).where(Concept.id == topic_id, Concept.course_id == course.id)).first()
    if not topic:
        raise HTTPException(404, "Topic not found")
    values = body.model_dump(exclude_unset=True)
    if "description" in values:
        try:
            values["description"] = validate_description(values["description"])
        except ValueError as exc:
            raise HTTPException(422, str(exc))
    if "module_label" in values:
        values["module"] = values.pop("module_label")
    for key, value in values.items():
        setattr(topic, key, value)
    s.add(topic)
    s.commit()
    s.refresh(topic)
    FastAPIJobs(background).enqueue(retag_course, course.id)
    return {"id": topic.id, "name": topic.name, "module_label": topic.module,
            "description": topic.description, "key": topic.key}


@router.delete("/{course_id}/topics/{topic_id}")
def delete_topic(topic_id: int, background: BackgroundTasks,
                 course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    topic = s.exec(select(Concept).where(Concept.id == topic_id, Concept.course_id == course.id)).first()
    if not topic:
        raise HTTPException(404, "Topic not found")
    s.delete(topic)
    s.commit()
    FastAPIJobs(background).enqueue(retag_course, course.id)
    return {"ok": True}


def safe_filename(filename: str) -> str:
    name = Path(filename or "upload").name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return name[:120] or "upload"


def valid_content(ext: str, data: bytes) -> bool:
    if ext == ".pdf":
        return data.startswith(b"%PDF-")
    if ext in (".pptx", ".docx"):
        return data.startswith(b"PK")
    if ext == ".ipynb":
        try:
            import json
            return isinstance(json.loads(data.decode("utf-8")), dict)
        except (UnicodeDecodeError, ValueError):
            return False
    return b"\x00" not in data


@router.get("/{course_id}/materials")
def list_materials(course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    materials = s.exec(select(Material).where(Material.course_id == course.id)).all()
    return [{"id": m.id, "filename": m.filename, "kind": m.kind, "size_kb": m.size_kb,
             "chunks": m.chunks, "status": m.status, "error": m.error} for m in materials]


@router.post("/{course_id}/materials")
def upload_materials(background: BackgroundTasks, files: list[UploadFile] = File(...),
                     course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    current = len(s.exec(select(Material).where(Material.course_id == course.id)).all())
    if current + len(files) > 50:
        raise HTTPException(400, "A course can have at most 50 materials")
    storage = LocalFileStorage()
    results = []
    for upload in files:
        filename = safe_filename(upload.filename or "")
        ext = Path(filename).suffix.lower()
        if ext not in EXT:
            raise HTTPException(400, f"Unsupported file type: {ext}")
        data = upload.file.read()
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit")
        if not valid_content(ext, data):
            raise HTTPException(400, "File content does not match its extension")
        material = Material(course_id=course.id, filename=filename, kind=KIND[ext],
                            size_kb=max(1, len(data) // 1024), status="processing")
        s.add(material)
        s.commit()
        s.refresh(material)
        path = storage.save(f"{material.id}_{filename}", data)
        FastAPIJobs(background).enqueue(process_material, material.id, course.id, str(path))
        results.append({"id": material.id, "filename": filename, "kind": material.kind,
                        "size_kb": material.size_kb, "chunks": 0, "status": material.status, "error": ""})
    return results


@router.delete("/{course_id}/materials/{material_id}")
def delete_material(material_id: int, course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    material = s.exec(select(Material).where(Material.id == material_id, Material.course_id == course.id)).first()
    if not material:
        raise HTTPException(404, "Material not found")
    LocalFileStorage().delete(f"{material.id}_{material.filename}")
    from ..adapters.chroma import ChromaVectorStore
    ChromaVectorStore().delete_by_material(course.id, material.id)
    s.delete(material)
    s.commit()
    return {"ok": True}
