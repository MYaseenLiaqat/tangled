import os
from alembic import command
from alembic.config import Config
from sqlmodel import Session, create_engine
from .config import settings

os.makedirs("data", exist_ok=True)
_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_args)


def migrate() -> None:
    config = Config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")


def session():
    with Session(engine) as s:
        yield s
