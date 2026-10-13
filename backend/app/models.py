from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class Concept(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    name: str
    module: str = ""
    description: str = ""


class Material(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    filename: str
    kind: str
    size_kb: int = 0
    chunks: int = 0
    status: str = "indexed"


class Student(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)  # pseudonymous; no names or emails stored


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
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
    key: str = Field(index=True, unique=True)
    concept_id: int = Field(foreign_key="concept.id")


class QuizResponse(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="quizitem.id", index=True)
    student_id: int = Field(foreign_key="student.id")
    option: str
    correct: bool


class Verdict(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    concept_id: int = Field(foreign_key="concept.id", index=True)
    verdict: str  # addressed | false_alarm
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
