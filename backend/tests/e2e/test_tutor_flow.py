"""
Product Tutor e2e — Day 13-15 AIChat 产品教程
"""

P = "/api/v1/ai/tutor"


def test_list_faqs(client):
    r = client.get(f"{P}/faqs")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 5
    ids = {f["id"] for f in body["faqs"]}
    # 核心 FAQ 必须存在
    assert "trending-search" in ids
    assert "copywriting-modes" in ids
    assert "shoot-script" in ids


def test_tutor_matches_trending(client):
    r = client.post(P, json={"query": "怎么搜索热点"})
    assert r.status_code == 200
    body = r.json()
    assert body["matched"] is True
    assert body["source"] == "kb"
    assert body["faq_id"] == "trending-search"
    assert "热点搜索" in body["answer"]
    assert body["action_url"] == "/trending"


def test_tutor_matches_copywriting(client):
    r = client.post(P, json={"query": "口播文案有哪些模式"})
    assert r.status_code == 200
    body = r.json()
    assert body["matched"] is True
    assert body["faq_id"] == "copywriting-modes"
    assert body["action_url"] == "/copywriting"


def test_tutor_matches_subscription(client):
    r = client.post(P, json={"query": "想自动推送一个话题怎么订阅"})
    assert r.status_code == 200
    body = r.json()
    assert body["matched"] is True
    assert body["faq_id"] == "subscribe-topic"


def test_tutor_matches_quota(client):
    r = client.post(P, json={"query": "配额是怎么扣的"})
    assert r.status_code == 200
    body = r.json()
    assert body["matched"] is True
    assert body["faq_id"] == "quota"


def test_tutor_matches_english_keywords(client):
    """关键词列表包含英文别名，应该也能命中"""
    r = client.post(P, json={"query": "How does the dashboard work"})
    assert r.status_code == 200
    body = r.json()
    assert body["matched"] is True
    assert body["faq_id"] == "analytics"


def test_tutor_fallback_when_unmatched(client, monkeypatch):
    """完全无关问题：禁用 LLM 时走 fallback"""
    from backend.core import ai_service
    monkeypatch.setattr(ai_service.ai_manager, "is_available", lambda: False)
    r = client.post(P, json={"query": "今天天气怎么样啊"})
    assert r.status_code == 200
    body = r.json()
    assert body["matched"] is False
    assert body["source"] == "fallback"
    assert "覆盖范围" in body["answer"]


def test_tutor_empty_query_rejected(client):
    r = client.post(P, json={"query": ""})
    # Pydantic min_length=1
    assert r.status_code == 422
