from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    ferment_min: Mapped[int] = mapped_column(Integer)
    bake_min: Mapped[int] = mapped_column(Integer)


class Oven(Base):
    __tablename__ = "ovens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(40), unique=True)
    capacity_note: Mapped[str] = mapped_column(String(80), default="")


class Batch(Base):
    __tablename__ = "batches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    oven_id: Mapped[int] = mapped_column(ForeignKey("ovens.id"))
    code: Mapped[str] = mapped_column(String(40), unique=True)
    start_min: Mapped[int] = mapped_column(Integer)  # minutes from 00:00
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ConflictLog(Base):
    __tablename__ = "conflict_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_code: Mapped[str] = mapped_column(String(40))
    oven_id: Mapped[int] = mapped_column(Integer)
    detail: Mapped[str] = mapped_column(String(240))
    # 对手（已排产）信息：与甘特 /gantt 上对手色块的端点一致
    opponent_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    opponent_phase: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ferment | bake
    opponent_start_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opponent_end_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 这次想排入的阶段和起止
    candidate_phase: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ferment | bake
    candidate_start_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    candidate_end_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
