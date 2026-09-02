import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    return url


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(database_url(), pool_pre_ping=True, pool_recycle=300)
    return _engine


def new_session():
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)()
