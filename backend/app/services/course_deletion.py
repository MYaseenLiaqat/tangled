import logging
from pathlib import Path
from sqlmodel import Session, select
from sqlalchemy import delete
from ..adapters.chroma import ChromaVectorStore
from ..adapters.files import LocalFileStorage
from ..db import engine
from ..models import AnalysisJob, Concept, Course, InsightGroup, Material, Message, QuizAggregate, QuizItem, QuizResponse, Student, Verdict

logger = logging.getLogger("tangled.course_deletion")


def delete_course(course_id: int) -> None:
    material_files: list[str] = []
    with Session(engine) as s:
        material_files = [f"{row.id}_{row.filename}" for row in
                          s.exec(select(Material).where(Material.course_id == course_id)).all()]
        for model in (AnalysisJob, QuizResponse, Message, QuizAggregate, InsightGroup,
                      Verdict, Material, Student, QuizItem, Concept):
            s.exec(delete(model).where(model.course_id == course_id))
        s.exec(delete(Course).where(Course.id == course_id))
        s.commit()
    storage = LocalFileStorage()
    for filename in material_files:
        try:
            storage.delete(filename)
        except OSError:
            logger.warning("course file cleanup failed course_id=%s", course_id)
    try:
        ChromaVectorStore().delete_by_course(course_id)
    except Exception:
        logger.warning("course vector cleanup failed course_id=%s", course_id)
