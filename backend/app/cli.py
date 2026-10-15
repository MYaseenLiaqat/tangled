import argparse
import asyncio
from sqlmodel import Session, select
from .config import settings
from .db import engine
from .models import AnalysisJob
from .services.analysis import analyze


def retry_unlabelled() -> None:
    with Session(engine) as s:
        jobs = s.exec(select(AnalysisJob).where(AnalysisJob.status.in_(["pending", "failed"]),
                                                AnalysisJob.attempts < settings.analysis_max_retries)).all()
        ids = [job.message_id for job in jobs]
    for message_id in ids:
        asyncio.run(analyze(message_id))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["retry_unlabelled"])
    args = parser.parse_args()
    if args.command == "retry_unlabelled":
        retry_unlabelled()


if __name__ == "__main__":
    main()
