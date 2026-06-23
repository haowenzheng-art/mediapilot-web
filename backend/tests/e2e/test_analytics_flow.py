"""
Analytics e2e — Day 8 数据看板
"""
import pytest


P = "/api/v1/analytics"


def test_health(client):
    r = client.get(f"{P}/health")
    assert r.status_code == 200


def test_dashboard_empty_user(client, auth_headers):
    """新用户的看板：所有计数为 0，daily_content 长度 = days"""
    r = client.get(f"{P}/dashboard?days=7", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["window_days"] == 7
    assert data["overview"]["total_content"] == 0
    assert data["overview"]["unread_push"] == 0
    assert len(data["daily_content"]) == 7
    assert all(d["total"] == 0 for d in data["daily_content"])
    assert data["top_hot_topics"] == []


def test_dashboard_counts_after_content_creation(client, auth_headers):
    # 通过 content_library API 创建几条
    for i in range(3):
        payload = {
            "content_type": "copywriting",
            "content_id": f"a-{i}",
            "title": f"标题 {i}",
            "hot_topic_id": "topic-x",
            "hot_topic_title": "X 热点",
            "hot_topic_source": "微博",
            "mode": "from_zero",
            "persona": "测试",
        }
        client.post("/api/v1/content-library/contents", json=payload, headers=auth_headers)

    # 再来一条不同类型
    payload2 = {
        "content_type": "shoot_script",
        "content_id": "ss-1",
        "title": "脚本",
        "hot_topic_id": "topic-y",
        "hot_topic_title": "Y 热点",
        "hot_topic_source": "知乎",
        "mode": "from_zero",
        "persona": "测试",
    }
    client.post("/api/v1/content-library/contents", json=payload2, headers=auth_headers)

    r = client.get(f"{P}/dashboard?days=30", headers=auth_headers)
    data = r.json()["data"]
    assert data["overview"]["total_content"] == 4
    assert data["content_type_split"].get("copywriting") == 3
    assert data["content_type_split"].get("shoot_script") == 1

    # top_hot_topics 应排序：topic-x（3 条）在前
    tops = data["top_hot_topics"]
    assert len(tops) == 2
    assert tops[0]["hot_topic_id"] == "topic-x"
    assert tops[0]["content_count"] == 3


def test_dashboard_isolated_per_user(client, auth_headers):
    """A 的活动不应出现在 B 的看板"""
    client.post("/api/v1/content-library/contents", json={
        "content_type": "copywriting", "content_id": "iso-a", "title": "A",
        "hot_topic_id": "iso-topic", "hot_topic_title": "iso",
        "hot_topic_source": "微博", "mode": "from_zero", "persona": "测试",
    }, headers=auth_headers)

    r2 = client.post("/api/v1/auth/register", json={
        "username": "ana_user_b", "password": "pass123456", "email": "anab@test.com"
    })
    headers_b = {"Authorization": f"Bearer {r2.json()['data']['token']}"}

    r = client.get(f"{P}/dashboard?days=7", headers=headers_b)
    data = r.json()["data"]
    assert data["overview"]["total_content"] == 0


def test_dashboard_rejects_invalid_days(client, auth_headers):
    r = client.get(f"{P}/dashboard?days=200", headers=auth_headers)
    assert r.status_code == 422
    r = client.get(f"{P}/dashboard?days=1", headers=auth_headers)
    assert r.status_code == 422


def test_dashboard_requires_auth(client):
    r = client.get(f"{P}/dashboard")
    assert r.status_code in (401, 403)
