"""
Calendar e2e — Day 9-10 内容发布日历
"""
from datetime import datetime, timedelta


P = "/api/v1/calendar"


def _payload(**overrides):
    base = {
        "title": "默认事件",
        "content": "事件描述",
        "scheduled_date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
        "platform": "douyin",
        "status": "pending",
    }
    base.update(overrides)
    return base


def test_health(client):
    r = client.get(f"{P}/health")
    assert r.status_code == 200


def test_create_and_get(client, auth_headers):
    r = client.post(f"{P}/events", json=_payload(title="发布抖音"), headers=auth_headers)
    assert r.status_code == 201, r.text
    eid = r.json()["data"]["id"]

    r = client.get(f"{P}/events/{eid}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["title"] == "发布抖音"


def test_invalid_status_rejected(client, auth_headers):
    r = client.post(f"{P}/events", json=_payload(status="floating"), headers=auth_headers)
    assert r.status_code == 400


def test_list_filter_by_date_range(client, auth_headers):
    # 创建 3 个事件
    t1 = (datetime.utcnow() + timedelta(days=1)).isoformat()
    t2 = (datetime.utcnow() + timedelta(days=5)).isoformat()
    t3 = (datetime.utcnow() + timedelta(days=20)).isoformat()
    for t, title in [(t1, "near"), (t2, "mid"), (t3, "far")]:
        client.post(f"{P}/events", json=_payload(scheduled_date=t, title=title), headers=auth_headers)

    # 只查未来 10 天
    start = datetime.utcnow().isoformat()
    end = (datetime.utcnow() + timedelta(days=10)).isoformat()
    r = client.get(f"{P}/events", params={"start_date": start, "end_date": end}, headers=auth_headers)
    assert r.status_code == 200
    titles = [e["title"] for e in r.json()["data"]]
    assert "near" in titles and "mid" in titles
    assert "far" not in titles


def test_update_event(client, auth_headers):
    r = client.post(f"{P}/events", json=_payload(title="原标题"), headers=auth_headers)
    eid = r.json()["data"]["id"]

    r = client.put(f"{P}/events/{eid}",
                   json={"title": "新标题", "status": "completed"},
                   headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["data"]["title"] == "新标题"
    assert r.json()["data"]["status"] == "completed"


def test_delete_event(client, auth_headers):
    r = client.post(f"{P}/events", json=_payload(title="待删"), headers=auth_headers)
    eid = r.json()["data"]["id"]
    r = client.delete(f"{P}/events/{eid}", headers=auth_headers)
    assert r.status_code == 200

    r = client.get(f"{P}/events/{eid}", headers=auth_headers)
    assert r.status_code == 404


def test_delete_nonexistent_returns_404(client, auth_headers):
    r = client.delete(f"{P}/events/999999", headers=auth_headers)
    assert r.status_code == 404


def test_upcoming_events(client, auth_headers):
    t = (datetime.utcnow() + timedelta(days=2)).isoformat()
    client.post(f"{P}/events", json=_payload(scheduled_date=t, title="upcoming-1"), headers=auth_headers)
    # 60 天后
    far = (datetime.utcnow() + timedelta(days=60)).isoformat()
    client.post(f"{P}/events", json=_payload(scheduled_date=far, title="far-1"), headers=auth_headers)

    r = client.get(f"{P}/events/upcoming?days=7", headers=auth_headers)
    assert r.status_code == 200
    titles = [e["title"] for e in r.json()["data"]]
    assert "upcoming-1" in titles
    assert "far-1" not in titles


def test_isolated_per_user(client, auth_headers):
    client.post(f"{P}/events", json=_payload(title="A 的事件"), headers=auth_headers)

    r2 = client.post("/api/v1/auth/register", json={
        "username": "cal_b", "password": "pass123456", "email": "calb@test.com"
    })
    headers_b = {"Authorization": f"Bearer {r2.json()['data']['token']}"}

    r = client.get(f"{P}/events", headers=headers_b)
    assert r.json()["data"] == []


def test_requires_auth(client):
    r = client.get(f"{P}/events")
    assert r.status_code in (401, 403)
