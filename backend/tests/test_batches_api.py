"""端到端接口测试：拒绝记录必须与甘特色块端点一致；端点相接不算冲突。"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.router import api_router
from app.database import Base, get_db
from app.models.models import Batch, ConflictLog, Oven, Product


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSession()
    # 种子最小集：乡村欧包(酵40/烤35) + 一层 1 号炉 + BO-0900 09:00 开
    bread = Product(name="乡村欧包", ferment_min=40, bake_min=35)
    oven = Oven(label="一层 1 号炉", capacity_note="盘炉")
    db.add_all([bread, oven])
    db.flush()
    db.add(Batch(product_id=bread.id, oven_id=oven.id, code="BO-0900", start_min=9 * 60))
    db.commit()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    app = FastAPI()
    app.include_router(api_router, prefix="/api")

    def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    return TestClient(app)


def _gantt_bake_block(client, code):
    blocks = client.get("/api/gantt").json()
    hits = [b for b in blocks if b["code"] == code and b["phase"] == "bake"]
    assert len(hits) == 1
    return hits[0]


def test_overlap_rejection_log_matches_gantt(client, db_session):
    # 乡村欧包 10:00 开：酵[600,640) 烤[640,675) —— 与 BO-0900 烤[580,615) 也有发酵冲突，
    # 但用例要求新行记录的是对手烘烤色块（端点与甘特一致）。
    resp = client.post(
        "/api/batches",
        json={"product_id": 1, "oven_id": 1, "start_min": 600},
    )
    assert resp.status_code == 409

    logs = client.get("/api/conflicts").json()
    assert len(logs) == 1
    row = logs[0]

    block = _gantt_bake_block(client, "BO-0900")
    # 对手色块端点 == 甘特上 BO-0900 烘烤块端点 [09:40,10:15)
    assert row["rival_code"] == "BO-0900"
    assert row["rival_phase"] == "bake"
    assert (row["rival_start_min"], row["rival_end_min"]) == (
        block["start_min"],
        block["end_min"],
    )
    assert (row["rival_start_min"], row["rival_end_min"]) == (580, 615)
    # 本次拟排的是发酵段（与对手烘烤撞上的那一格），端点同样取自同一组区间
    assert row["attempt_phase"] == "ferment"
    assert (row["attempt_start_min"], row["attempt_end_min"]) == (600, 640)
    # 阶段名用中文
    assert "BO-0900" in row["detail"] and "烘烤" in row["detail"] and "发酵" in row["detail"]
    # 被拒的批次没有进批次表
    assert db_session.scalars(select(Batch).where(Batch.code == "BO-600")).first() is None


def test_bake_against_bake_reports_bake_interval(client, db_session):
    # 题述试法：乡村欧包在 1 号炉上与 BO-0900 的烘烤重叠。
    # 09:20 开：酵[560,600) 烤[600,635)，拟排烘烤与 BO-0900 烤[580,615) 真重叠。
    resp = client.post(
        "/api/batches",
        json={"product_id": 1, "oven_id": 1, "start_min": 9 * 60 + 20},
    )
    assert resp.status_code == 409
    row = client.get("/api/conflicts").json()[0]
    # 新行双方都是烘烤段；对手烘烤区间等于 BO-0900 甘特色块
    block = _gantt_bake_block(client, "BO-0900")
    assert row["attempt_phase"] == "bake"
    assert (row["attempt_start_min"], row["attempt_end_min"]) == (600, 635)
    assert row["rival_phase"] == "bake"
    assert (row["rival_start_min"], row["rival_end_min"]) == (
        block["start_min"],
        block["end_min"],
    )
    assert (row["rival_start_min"], row["rival_end_min"]) == (580, 615)
    assert len(db_session.scalars(select(ConflictLog)).all()) == 1


def test_endpoint_touching_succeeds_and_gantt_joins(client, db_session):
    # BO-0900 烤段收尾于 615；新批次 09:40 之前的可行解：10:15 开，酵[615,655) 烤[655,690)
    before = len(client.get("/api/conflicts").json())
    assert before == 0

    resp = client.post(
        "/api/batches",
        json={"product_id": 1, "oven_id": 1, "start_min": 615},
    )
    assert resp.status_code == 200, resp.text
    created = resp.json()
    assert created["ferment_end"] == 655 and created["bake_end"] == 690

    # 拒绝记录条数不增加
    after = client.get("/api/conflicts").json()
    assert len(after) == before

    blocks = client.get("/api/gantt").json()
    oven_blocks = sorted(
        [b for b in blocks if b["oven_id"] == 1], key=lambda b: b["start_min"]
    )
    # 甘特两段首尾相接：BO-0900 烤段终点 == 新批次发酵段起点
    bo_bake = next(b for b in oven_blocks if b["code"] == "BO-0900" and b["phase"] == "bake")
    new_ferment = next(b for b in oven_blocks if b["code"] == created["code"] and b["phase"] == "ferment")
    assert bo_bake["end_min"] == new_ferment["start_min"] == 615
    # 新批次自身两段也首尾相接
    new_bake = next(b for b in oven_blocks if b["code"] == created["code"] and b["phase"] == "bake")
    assert new_ferment["end_min"] == new_bake["start_min"] == 655


def test_successful_create_adds_no_conflict(client, db_session):
    # 空闲时段创建成功
    resp = client.post(
        "/api/batches",
        json={"product_id": 1, "oven_id": 1, "start_min": 12 * 60},
    )
    assert resp.status_code == 200, resp.text
    assert len(client.get("/api/conflicts").json()) == 0
    assert len(db_session.scalars(select(ConflictLog)).all()) == 0
