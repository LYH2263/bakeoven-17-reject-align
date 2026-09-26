"""端到端：拒绝记录与甘特色块对齐；端点相接创建成功。

种子数据（一层 1 号炉）：
  BO-0900 乡村欧包 09:00 开工 → 发酵 [540,580) 烘烤 [580,615)
  BO-1030 黄油可颂 10:30 开工 → 发酵 [630,655) 烘烤 [655,675)
"""

# 种子产品/炉位 id
RUSTIC = 1  # 乡村欧包：酵 40 / 烤 35
OVEN1 = 1  # 一层 1 号炉


def _gantt_block(client, code: str, phase: str) -> dict:
    blocks = client.get("/api/gantt").json()
    hits = [b for b in blocks if b["code"] == code and b["phase"] == phase]
    assert hits, f"甘特上缺少 {code}/{phase} 色块"
    return hits[0]


def _latest_conflict(client) -> dict:
    rows = client.get("/api/conflicts").json()
    assert rows
    return rows[0]


def test_overlap_rejected_log_matches_gantt(client):
    # 09:40 开工：发酵与 BO-0900 发酵端点相接（允许），但发酵撞上 BO-0900 烘烤
    res = client.post(
        "/api/batches",
        json={"product_id": RUSTIC, "oven_id": OVEN1, "start_min": 9 * 60 + 40},
    )
    assert res.status_code == 409

    # 批次未创建
    codes = [b["code"] for b in client.get("/api/batches").json()]
    assert "BO-580" not in codes

    log = _latest_conflict(client)
    bake = _gantt_block(client, "BO-0900", "bake")

    # 对手信息：BO-0900 的烘烤区间，与甘特色块端点完全一致
    assert log["opponent_code"] == "BO-0900"
    assert log["opponent_phase"] == "bake"
    assert (log["opponent_start_min"], log["opponent_end_min"]) == (
        bake["start_min"],
        bake["end_min"],
    )
    assert (log["opponent_start_min"], log["opponent_end_min"]) == (10 * 60 - 20, 10 * 60 + 15)

    # 这次想排入的是发酵段 09:40–10:20
    assert log["candidate_phase"] == "ferment"
    assert (log["candidate_start_min"], log["candidate_end_min"]) == (580, 620)

    # 详情文案使用中文阶段名
    assert "BO-0900" in log["detail"]
    assert "烘烤" in log["detail"] and "发酵" in log["detail"]


def test_endpoint_touching_succeeds_and_no_new_log(client):
    before = len(client.get("/api/conflicts").json())

    # 紧贴 BO-1030 烘烤结束 675 开工：发酵 [675,715) 烘烤 [715,750)
    res = client.post(
        "/api/batches",
        json={"product_id": RUSTIC, "oven_id": OVEN1, "start_min": 675},
    )
    assert res.status_code == 200, res.text
    created = res.json()
    assert created["code"] == "BO-675"

    # 甘特两段首尾相接：BO-1030 烘烤结束 == 新批次发酵开始
    prev_bake = _gantt_block(client, "BO-1030", "bake")
    new_ferment = _gantt_block(client, "BO-675", "ferment")
    new_bake = _gantt_block(client, "BO-675", "bake")
    assert prev_bake["end_min"] == new_ferment["start_min"] == 675
    assert new_ferment["end_min"] == new_bake["start_min"] == 715

    # 拒绝记录条数不增加
    after = len(client.get("/api/conflicts").json())
    assert after == before
