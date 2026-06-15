"""
快速测试 MediaPilot 后端 API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# 颜色定义
class TestResult:
    def __init__(self, name: str, passed: bool, details: str = ""):
        self.name = name
        self.passed = passed
        self.details = details

    def __repr__(self):
        status = "✅ 通过" if self.passed else "❌ 失败"
        return f"[{status}] {self.name}: {self.details}"

# 测试函数
def test_health():
    """测试健康检查"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200 and resp.json().get("status") == "healthy":
            return TestResult("健康检查", True)
        return TestResult("健康检查", False, str(resp.status_code))
    except Exception as e:
        return TestResult("健康检查", False, str(e))

def test_login():
    """测试登录"""
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "testphase5", "password": "Test123456"},
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success") and "token" in data.get("data", {}):
                return TestResult("登录", True, f"Token: {data['data']['token'][:20]}...")
        return TestResult("登录", False, str(resp.status_code))
    except Exception as e:
        return TestResult("登录", False, str(e))

def test_competitor_search(token: str):
    """测试对标账号搜索"""
    try:
        resp = requests.post(
            f"{BASE_URL}/competitors/search",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "niche": "tech",
                "platforms": ["douyin"],
                "min_followers": 10000,
                "max_followers": 1000000,
                "min_avg_likes": 100
            },
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                result = data.get("data", {})
                competitors = result.get("competitors", [])
                return TestResult("对标搜索", True, f"找到 {len(competitors)} 个对标账号")
        return TestResult("对标搜索", False, str(resp.status_code))
    except Exception as e:
        return TestResult("对标搜索", False, str(e))

def test_trending_search(token: str):
    """测试热点搜索"""
    try:
        resp = requests.post(
            f"{BASE_URL}/trending/search",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "keyword": "AI",
                "platforms": ["douyin"],
                "days": 7
            },
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                result = data.get("data", {})
                topics = result.get("hot_topics", [])
                return TestResult("热点搜索", True, f"找到 {len(topics)} 个热点话题")
        return TestResult("热点搜索", False, str(resp.status_code))
    except Exception as e:
        return TestResult("热点搜索", False, str(e))

# 主测试函数
def run_all_tests():
    """运行所有测试"""
    print("=== MediaPilot 后端 API 测试 ===\n")

    # 测试 1: 健康检查
    health = test_health()
    print(health)

    # 如果健康检查失败，停止
    if not health.passed:
        print("\n❌ 健康检查失败，停止测试")
        return

    # 测试 2: 登录
    login = test_login()
    print(login)

    if not login.passed:
        print("\n❌ 登录失败，停止测试")
        return

    token = login.details.split(": ")[1].strip()

    # 测试 3: 热点搜索
    trending = test_trending_search(token)
    print(trending)

    # 测试 4: 对标账号搜索
    competitors = test_competitor_search(token)
    print(competitors)

    # 汇总
    all_passed = all([t.passed for t in [health, login, trending, competitors]])
    print(f"\n=== 测试结果 ===")
    print(f"通过: {sum([t.passed for t in [health, login, trending, competitors])}/4")
    print(f"总数: 4")

if __name__ == "__main__":
    run_all_tests()
