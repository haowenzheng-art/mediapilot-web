"""
用户偏好设置 e2e — Day 6-7 Settings 后端
覆盖：GET / PUT (部分更新) / POST reset / 校验拒绝 / 未登录 401
"""


P = "/api/v1/user/preferences"


def test_get_default_preferences(client, auth_headers):
    """新用户读取偏好应返回默认值"""
    r = client.get(P, headers=auth_headers)
    assert r.status_code == 200
    prefs = r.json()["data"]["preferences"]
    assert prefs["theme"] == "dark"
    assert prefs["language"] == "zh-CN"
    assert prefs["notifications"] is True
    assert prefs["default_platform"] == "douyin"


def test_partial_update_preserves_other_keys(client, auth_headers):
    r = client.put(P, json={"theme": "light"}, headers=auth_headers)
    assert r.status_code == 200
    prefs = r.json()["data"]["preferences"]
    assert prefs["theme"] == "light"
    # 其它字段仍为默认
    assert prefs["language"] == "zh-CN"

    # 再更新 language，theme 应保留
    r = client.put(P, json={"language": "en-US"}, headers=auth_headers)
    prefs = r.json()["data"]["preferences"]
    assert prefs["theme"] == "light"
    assert prefs["language"] == "en-US"


def test_update_rejects_invalid_theme(client, auth_headers):
    r = client.put(P, json={"theme": "neon"}, headers=auth_headers)
    assert r.status_code == 422


def test_update_rejects_invalid_platform(client, auth_headers):
    r = client.put(P, json={"default_platform": "instagram"}, headers=auth_headers)
    assert r.status_code == 422


def test_reset_clears_preferences(client, auth_headers):
    client.put(P, json={"theme": "light", "language": "en-US"}, headers=auth_headers)
    r = client.post(f"{P}/reset", headers=auth_headers)
    assert r.status_code == 200
    prefs = r.json()["data"]["preferences"]
    assert prefs["theme"] == "dark"  # 回到默认
    assert prefs["language"] == "zh-CN"


def test_requires_auth(client):
    r = client.get(P)
    assert r.status_code in (401, 403)


def test_preferences_isolated_per_user(client, auth_headers):
    """A 用户改了偏好，B 用户读不应受影响"""
    client.put(P, json={"theme": "light"}, headers=auth_headers)

    r2 = client.post("/api/v1/auth/register", json={
        "username": "pref_user_b", "password": "pass123456", "email": "pref_b@test.com"
    })
    assert r2.status_code == 200
    headers_b = {"Authorization": f"Bearer {r2.json()['data']['token']}"}

    r = client.get(P, headers=headers_b)
    assert r.json()["data"]["preferences"]["theme"] == "dark"
