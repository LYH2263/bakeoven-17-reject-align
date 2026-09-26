from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

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
    """拒绝记录：对手色块（已占炉）与本次拟排色块的端点都与甘特一致。"""

    __tablename__ = "conflict_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_code: Mapped[str] = mapped_column(String(40))
    oven_id: Mapped[int] = mapped_column(Integer)
    detail: Mapped[str] = mapped_column(String(240))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 本次想排入却被拒绝的色块
    attempt_phase: Mapped[str | None] = mapped_column(String(20), nullable=True)  # ferment | bake
    attempt_start_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempt_end_min: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 对手（已存在）色块
    rival_batch_id: Mapped[int | None] = mapped_column(ForeignKey("batches.id"), nullable=True)
    rival_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    rival_phase: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rival_start_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rival_end_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
