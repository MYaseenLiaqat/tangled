from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select
from .config import settings
from .db import session
from .models import Student


def teacher_auth(authorization: str = Header(default="")) -> None:
    if authorization not in (settings.teacher_token, f"Bearer {settings.teacher_token}"):
        raise HTTPException(401, "Invalid teacher token")


def current_student(x_student_code: str = Header(default=""), s: Session = Depends(session)) -> Student:
    st = s.exec(select(Student).where(Student.code == x_student_code)).first()
    if not st:
        raise HTTPException(401, "Unknown student code")
    return st
