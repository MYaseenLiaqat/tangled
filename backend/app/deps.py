from datetime import datetime, timezone
import jwt
from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select
from .config import settings
from .db import session
from .models import Course, Instructor, Student


def current_instructor(authorization: str = Header(default=""), s: Session = Depends(session)) -> Instructor:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing instructor token")
    try:
        payload = jwt.decode(authorization[7:], settings.jwt_secret, algorithms=["HS256"])
        if payload.get("role") != "instructor":
            raise ValueError
        instructor_id = int(payload["sub"])
        if datetime.fromtimestamp(payload["exp"], timezone.utc) <= datetime.now(timezone.utc):
            raise ValueError
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(401, "Invalid instructor token")
    instructor = s.get(Instructor, instructor_id)
    if not instructor:
        raise HTTPException(401, "Invalid instructor token")
    return instructor


def get_owned_course(course_id: int, instructor: Instructor = Depends(current_instructor),
                     s: Session = Depends(session)) -> Course:
    course = s.exec(select(Course).where(Course.id == course_id, Course.instructor_id == instructor.id)).first()
    if not course:
        raise HTTPException(404, "Course not found")
    return course


def current_student(authorization: str = Header(default=""), s: Session = Depends(session)) -> Student:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing student token")
    try:
        payload = jwt.decode(authorization[7:], settings.jwt_secret, algorithms=["HS256"])
        if payload.get("role") != "student":
            raise ValueError
        student_id = int(payload["student_id"])
        course_id = int(payload["course_id"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(401, "Invalid student token")
    student = s.exec(select(Student).where(Student.id == student_id, Student.course_id == course_id)).first()
    if not student:
        raise HTTPException(401, "Invalid student token")
    return student
