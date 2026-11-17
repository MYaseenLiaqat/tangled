import argparse
import asyncio
from sqlmodel import Session, select
from .config import settings
from .db import engine
from .models import AnalysisJob
from .services.analysis import analyze
from .services import rag


def retry_unlabelled() -> None:
    with Session(engine) as s:
        jobs = s.exec(select(AnalysisJob).where(AnalysisJob.status.in_(["pending", "failed"]),
                                                AnalysisJob.attempts < settings.analysis_max_retries)).all()
        ids = [job.message_id for job in jobs]
    for message_id in ids:
        asyncio.run(analyze(message_id))


def prewarm() -> None:
    rag.ef()


def retag() -> None:
    """Re-index every course's materials so chunks carry the current topic tags."""
    from .models import Course
    from .services.materials import retag_course
    with Session(engine) as s:
        course_ids = [course.id for course in s.exec(select(Course)).all()]
    for course_id in course_ids:
        retag_course(course_id)
        print(f"retagged course {course_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["retry_unlabelled", "prewarm", "retag"])
    args = parser.parse_args()
    if args.command == "retry_unlabelled":
        retry_unlabelled()
    elif args.command == "prewarm":
        prewarm()
    elif args.command == "retag":
        retag()


if __name__ == "__main__":
    main()
