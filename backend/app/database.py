from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# create_all 只补缺失的表，不补列；旧数据卷上的 conflict_logs 需要这些新列
_CONFLICT_LOG_COLUMNS = {
    "attempt_phase": "VARCHAR(20)",
    "attempt_start_min": "INTEGER",
    "attempt_end_min": "INTEGER",
    "rival_batch_id": "INTEGER",
    "rival_code": "VARCHAR(40)",
    "rival_phase": "VARCHAR(20)",
    "rival_start_min": "INTEGER",
    "rival_end_min": "INTEGER",
}


def ensure_conflict_log_columns() -> None:
    """Idempotently add structured conflict columns to a pre-existing table."""
    inspector = inspect(engine)
    if "conflict_logs" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("conflict_logs")}
    with engine.begin() as conn:
        for name, ddl in _CONFLICT_LOG_COLUMNS.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE conflict_logs ADD COLUMN {name} {ddl}"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
