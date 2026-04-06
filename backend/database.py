"""
SentinelX — Database Session Factory
======================================
Single source of truth for the SQLAlchemy engine and session.
Both main.py (API) and tasks.py (Celery) import from here.
"""
from __future__ import annotations

import os
import sqlalchemy
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# All credentials come from environment — never hard-coded.
DATABASE_URL: str = os.environ["DATABASE_URL"]

engine = sqlalchemy.create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # detect stale connections
    pool_size=10,
    max_overflow=20,
    connect_args={
        "options": "-c statement_timeout=30000"  # 30s query timeout at DB level
    },
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a DB session, ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
