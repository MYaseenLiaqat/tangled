from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class Instructor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Course(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    instructor_id: int = Field(foreign_key="instructor.id", index=True)
    name: str
    class_size: int | None = None
    join_code: str = Field(index=True, unique=True)
    joining_open: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Concept(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    course_id: int | None = Field(default=None, foreign_key="course.id", index=True)
    key: str = Field(index=True, unique=True)
    name: str
    module: str = ""
    description: str = ""


class Material(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    course_id: int | None = Field(default=None, foreign_key="course.id", index=True)
    filename: str
    kind: str
    size_kb: int = 0
    chunks: int = 0
    status: str = "indexed"
    error: str = ""


class Student(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    course_id: int = Field(foreign_key="course.id", index=True)
    code: str | None = Field(default=None, index=True, unique=True)
    consent_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    course_id: int | None = Field(default=None, foreign_key="course.id", index=True)
    student_id: int = Field(foreign_key="student.id", index=True)
    session_id: str = ""
    text: str
    answer: str = ""
    concept_id: int | None = Field(default=None, foreign_key="concept.id", index=True)
    similarity: float = 0.0
    intent: str = ""          # confusion | information | other | gap ("" = not yet analysed)
    intent_conf: float = 0.0
    misconception: bool = False
    phrase: str = ""          # exact words that show the intent (for highlighting)
    feedback: str = ""        # clear | unclear (student button)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)


class QuizItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    course_id: int | None = Field(default=None, foreign_key="course.id", index=True)
    key: str = Field(index=True, unique=True)
    concept_id: int = Field(foreign_key="concept.id")


class QuizResponse(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    course_id: int | None = Field(default=None, foreign_key="course.id", index=True)
    item_id: int = Field(foreign_key="quizitem.id", index=True)
    student_id: int = Field(foreign_key="student.id")
    option: str
    correct: bool


class Verdict(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    course_id: int | None = Field(default=None, foreign_key="course.id", index=True)
    concept_id: int = Field(foreign_key="concept.id", index=True)
    verdict: str  # addressed | false_alarm
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
