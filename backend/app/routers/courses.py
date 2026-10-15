import re
import secrets
import csv
import io
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from ..adapters.files import LocalFileStorage
from ..adapters.jobs import FastAPIJobs
from ..config import settings
from ..db import session
from ..deps import current_instructor, get_owned_course
from ..models import Concept, Course, Instructor, Material, QuizAggregate, Verdict
from ..services import insights
from ..services.ingest import EXT, KIND
from ..services.materials import process_material, retag_course
from ..services.course_deletion import delete_course

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


class CourseDelete(BaseModel):
    confirmation: str = Field(min_length=1)


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


@router.delete("/{course_id}")
def delete(body: CourseDelete, course: Course = Depends(get_owned_course)):
    if body.confirmation != course.name:
        raise HTTPException(400, "Type the course name exactly to confirm deletion")
    delete_course(course.id or 0)
    return {"ok": True}


@router.post("/{course_id}/join-code/regenerate")
def regenerate(course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    course.join_code = new_join_code(s)
    s.add(course)
    s.commit()
    s.refresh(course)
    return output(course)


@router.get("/{course_id}/topics")
def list_topics(course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    return insights.topics(s, course.id or 0)


@router.get("/{course_id}/topic-list")
def topic_list(course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    topics = s.exec(select(Concept).where(Concept.course_id == course.id)).all()
    return [{"id": topic.id, "name": topic.name, "description": topic.description,
             "module_label": topic.module} for topic in topics]


@router.get("/{course_id}/insights")
def course_insights(course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    return insights.topics(s, course.id or 0)


@router.get("/{course_id}/topics/{topic_id}/insights")
async def topic_insights(topic_id: int, course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    result = await insights.detail(s, course.id or 0, topic_id)
    if not result:
        raise HTTPException(404, "Topic not found")
    return result


class VerdictIn(BaseModel):
    verdict: str


@router.post("/{course_id}/topics/{topic_id}/verdict")
def topic_verdict(topic_id: int, body: VerdictIn, course: Course = Depends(get_owned_course),
                  s: Session = Depends(session)):
    if body.verdict not in {"addressed", "false_alarm"}:
        raise HTTPException(400, "Invalid verdict")
    topic = s.exec(select(Concept).where(Concept.id == topic_id,
                                         Concept.course_id == course.id)).first()
    if not topic:
        raise HTTPException(404, "Topic not found")
    s.add(Verdict(course_id=course.id, concept_id=topic_id, verdict=body.verdict))
    s.commit()
    return {"ok": True}


@router.get("/{course_id}/quiz")
def quiz(course: Course = Depends(get_owned_course), s: Session = Depends(session)):
    rows = s.exec(select(QuizAggregate).where(QuizAggregate.course_id == course.id)).all()
    out = {}
    for row in rows:
        item = out.setdefault(row.item, {"item": row.item, "concept": row.concept_name,
                                         "total": 0, "correct": 0, "options": {}, "wrong_options": {}})
        item["total"] += row.count
        item["correct"] += row.count if row.correct else 0
        item["options"][row.option] = row.count
        if not row.correct:
            item["wrong_options"][row.option] = item["wrong_options"].get(row.option, 0) + row.count
    return [{"item": item["item"], "topic": item["concept"],
             "correct_rate": round(item["correct"] / item["total"], 3) if item["total"] else 0,
             "responses": item["total"], "options": item["options"],
             "top_wrong": max(item["wrong_options"], key=item["wrong_options"].get)
             if item["wrong_options"] else None} for item in out.values()]


@router.post("/{course_id}/quiz/import")
def import_quiz(file: UploadFile, course: Course = Depends(get_owned_course),
                s: Session = Depends(session)):
    raw = file.file.read()
    if len(raw) > settings.max_quiz_import_mb * 1024 * 1024:
        raise HTTPException(413, "Quiz file exceeds the size limit")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    except UnicodeDecodeError:
        raise HTTPException(400, "Quiz CSV must be UTF-8")
    required = {"item", "concept", "option", "count", "correct"}
    headers = set(reader.fieldnames or [])
    if headers.intersection({"name", "email", "id", "roll"}):
        raise HTTPException(400, "Quiz CSV must not contain student identifiers")
    if headers != required:
        raise HTTPException(400, "Quiz CSV headers must be item, concept, option, count, correct")
    concepts = {topic.name.casefold(): topic for topic in
                s.exec(select(Concept).where(Concept.course_id == course.id)).all()}
    rows, errors, unmatched = [], [], []
    for number, row in enumerate(reader, start=2):
        try:
            item, concept_name, option = row["item"].strip(), row["concept"].strip(), row["option"].strip()
            count = int(row["count"])
            correct_text = row["correct"].strip().casefold()
            if not item or not concept_name or not option or count < 0 or correct_text not in {"true", "false", "1", "0", "yes", "no"}:
                raise ValueError("invalid item, concept, option, count, or correct value")
            concept = concepts.get(concept_name.casefold())
            if not concept:
                unmatched.append({"row": number, "concept": concept_name})
            rows.append((item, concept_name, option, count, correct_text in {"true", "1", "yes"}, concept))
        except (KeyError, ValueError) as exc:
            errors.append({"row": number, "error": str(exc)})
    if errors:
        raise HTTPException(422, {"errors": errors, "unmatched_concepts": unmatched})
    for old in s.exec(select(QuizAggregate).where(QuizAggregate.course_id == course.id)).all():
        s.delete(old)
    for item, concept_name, option, count, correct, concept in rows:
        s.add(QuizAggregate(course_id=course.id, item=item, concept_name=concept_name,
                            concept_id=concept.id if concept else None, option=option,
                            count=count, correct=correct))
    s.commit()
    return {"imported": len(rows), "unmatched_concepts": unmatched}


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
