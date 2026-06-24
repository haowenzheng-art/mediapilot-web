"""
Competitors e2e — Day 11-12 对标账号
"""

P = "/api/v1/competitors"


def _search_payload(**overrides):
    base = {
        "niche": "美妆",
        "platforms": ["douyin", "xiaohongshu"],
        "min_followers": 10000,
        "max_followers": 1000000,
        "min_avg_likes": 100,
    }
    base.update(overrides)
    return base


def test_health(client):
    r = client.get(f"{P}/health")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "ok"


def test_search_returns_demo_data(client, auth_headers):
    r = client.post(f"{P}/search", json=_search_payload(), headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"]
    data = body["data"]
    # 无平台 API 密钥时应返回 mock 数据并标记 is_demo
    assert data["is_demo"] is True
    assert data["niche"] == "美妆"
    assert data["total_count"] >= 1
    assert len(data["competitors"]) >= 1
    # 字段完整性
    first = data["competitors"][0]
    assert "nickname" in first
    assert "platform" in first
    assert "followers" in first


def test_search_requires_auth(client):
    r = client.post(f"{P}/search", json=_search_payload())
    assert r.status_code in (401, 403)


def test_search_deducts_quota(client, auth_headers):
    # 第一次搜索
    r = client.post(f"{P}/search", json=_search_payload(niche="健身"), headers=auth_headers)
    assert r.status_code == 200
    # 用 /api/v1/auth/me 看配额已扣
    me = client.get("/api/v1/auth/me", headers=auth_headers).json()["data"]
    assert me["quota_balance"] < 100


def test_export_csv(client, auth_headers):
    r = client.get(f"{P}/export?niche=美妆&format=csv", headers=auth_headers)
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    # CSV 内容含表头
    assert b"nickname" in r.content or "nickname" in r.text


def test_export_xlsx(client, auth_headers):
    r = client.get(f"{P}/export?niche=美妆&format=xlsx", headers=auth_headers)
    assert r.status_code == 200
    assert "spreadsheet" in r.headers["content-type"]


def test_export_invalid_format(client, auth_headers):
    r = client.get(f"{P}/export?niche=美妆&format=pdf", headers=auth_headers)
    # FastAPI 校验 pattern → 422
    assert r.status_code == 422
