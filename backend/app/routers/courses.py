import secrets
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from ..db import session
from ..deps import current_instructor, get_owned_course
from ..models import Course, Instructor

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
