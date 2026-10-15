from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Session, select
from ..config import settings
from ..db import session
from ..deps import current_instructor
from ..models import Instructor
from ..services.rate_limit import enforce

router = APIRouter()
passwords = PasswordHasher()


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("Invalid email address")
        return value


def token_for(instructor: Instructor) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": str(instructor.id), "role": "instructor", "iat": now, "exp": now + timedelta(hours=12)},
                      settings.jwt_secret, algorithm="HS256")


@router.post("/register")
def register(body: Credentials, s: Session = Depends(session)):
    if s.exec(select(Instructor).where(Instructor.email == body.email.lower())).first():
        raise HTTPException(409, "Email already registered")
    instructor = Instructor(email=body.email.lower(), password_hash=passwords.hash(body.password))
    s.add(instructor)
    s.commit()
    s.refresh(instructor)
    return {"access_token": token_for(instructor), "token_type": "bearer"}


@router.post("/login")
def login(body: Credentials, request: Request, s: Session = Depends(session)):
    enforce(f"login:{request.client.host if request.client else 'unknown'}", settings.login_rate_limit_per_min)
    instructor = s.exec(select(Instructor).where(Instructor.email == body.email.lower())).first()
    if not instructor:
        raise HTTPException(401, "Invalid email or password")
    try:
        passwords.verify(instructor.password_hash, body.password)
    except Exception:
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": token_for(instructor), "token_type": "bearer"}


@router.get("/me")
def me(instructor: Instructor = Depends(current_instructor)):
    return {"id": instructor.id, "email": instructor.email, "created_at": instructor.created_at}
