from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import Batch, ConflictLog, Oven, Product


def seed_if_empty(db: Session) -> None:
    if db.scalar(select(Product.id).limit(1)):
        return
    products = [
        Product(name="乡村欧包", ferment_min=40, bake_min=35),
        Product(name="黄油可颂", ferment_min=25, bake_min=20),
        Product(name="布朗尼", ferment_min=0, bake_min=30),
    ]
    ovens = [
        Oven(label="一层 1 号炉", capacity_note="盘炉"),
        Oven(label="一层 2 号炉", capacity_note="盘炉"),
        Oven(label="二层石板炉", capacity_note="石板"),
    ]
    db.add_all(products + ovens)
    db.flush()
    db.add_all(
        [
            Batch(product_id=products[0].id, oven_id=ovens[0].id, code="BO-0900", start_min=9 * 60, status="scheduled"),
            Batch(product_id=products[1].id, oven_id=ovens[0].id, code="BO-1030", start_min=10 * 60 + 30, status="scheduled"),
            Batch(product_id=products[2].id, oven_id=ovens[1].id, code="BO-1000", start_min=10 * 60, status="scheduled"),
        ]
    )
    db.flush()
    bo_0900 = db.scalar(select(Batch).where(Batch.code == "BO-0900"))
    # BO-0900：乡村欧包 09:00 起，发酵 [540,580)、烘烤 [580,615)
    db.add(
        ConflictLog(
            batch_code="BO-试排",
            oven_id=ovens[0].id,
            detail="与对手批次 BO-0900 的烘烤段 [09:40,10:15) 重叠；本次拟排烘烤段 [10:00,10:35)",
            attempt_phase="bake",
            attempt_start_min=10 * 60,
            attempt_end_min=10 * 60 + 35,
            rival_batch_id=bo_0900.id,
            rival_code="BO-0900",
            rival_phase="bake",
            rival_start_min=9 * 60 + 40,
            rival_end_min=10 * 60 + 15,
        )
    )
    db.commit()
