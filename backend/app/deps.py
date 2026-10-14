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


def current_student(x_student_code: str = Header(default=""), s: Session = Depends(session)) -> Student:
    st = s.exec(select(Student).where(Student.code == x_student_code)).first()
    if not st:
        raise HTTPException(401, "Unknown student code")
    return st
