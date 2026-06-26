"""MediaPilot 产品截图脚本

App.jsx 用 isHeroPage 客户端状态控制视图（不是 URL 路由），直接 goto /trending
看到的还是 HeroSection。所以这里用点击 feature-card 的方式进入内容页。

保存到 docs/screenshots/。
运行前提：前端 5173、后端 8000 都在运行。
用法：python scripts/screenshot.py
"""
import json
import sys
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
API = "http://localhost:8000"
SAVE_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

USERNAME = "qa_smoke"
PASSWORD = "qa123456"

# HeroSection 上的 feature card 标题 → 内容页 tab id
HERO_FEATURES = {
    "拍摄脚本": "shoot-script",
    "热点搜索": "trending",
    "口播文案": "copywriting",
    "视频分析": "video-analysis",
    "语音转写": "transcription",
    "话题订阅": "subscription",
}

# 侧边栏 tab 标题 → tab id
SIDEBAR_TABS = {
    "热点搜索": "trending",
    "口播文案": "copywriting",
    "拍摄脚本": "shoot-script",
    "话题订阅": "subscription",
    "内容库": "content-library",
    "智能转录": "transcription",
    "视频分析": "video-analysis",
    "AI模板": "templates",
}


def login_via_api():
    """通过 API 登录，返回 user_data（含 token）"""
    resp = requests.post(
        f"{API}/api/v1/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()["data"]
    return {
        "id": data["user"]["id"],
        "username": data["user"]["username"],
        "email": data["user"]["email"],
        "quota_balance": data["user"]["quota_balance"],
        "isAdmin": False,
        "token": data["token"],
        "refreshToken": data["refresh_token"],
    }


def click_hero_feature(page, feature_title):
    """在 HeroSection 上点击指定 feature card"""
    card = page.locator(f".feature-card:has-text('{feature_title}')").first
    card.wait_for(state="visible", timeout=5000)
    card.click()


def click_sidebar_tab(page, tab_title):
    """在 ContentPage 侧边栏点击指定 tab"""
    tab = page.locator(f".tab:has-text('{tab_title}')").first
    tab.wait_for(state="visible", timeout=5000)
    tab.click()


def goto_content_page(page, tab_id):
    """
    跳转到指定内容页。先回到 HeroSection（goto /），
    再通过 feature card 或 sidebar tab 切换。
    """
    page.goto(f"{BASE}/", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(800)

    # 找一个能直接进内容页的 feature card
    hero_entry = None
    for title, tid in HERO_FEATURES.items():
        if tid == tab_id:
            hero_entry = title
            break

    if hero_entry:
        click_hero_feature(page, hero_entry)
        page.wait_for_timeout(1200)
        return

    # tab 不在 HeroSection（如 content-library）：先进任意 feature，再点 sidebar tab
    click_hero_feature(page, "拍摄脚本")
    page.wait_for_timeout(1200)

    sidebar_title = None
    for title, tid in SIDEBAR_TABS.items():
        if tid == tab_id:
            sidebar_title = title
            break
    if sidebar_title:
        click_sidebar_tab(page, sidebar_title)
        page.wait_for_timeout(1200)


def shoot():
    user_data = login_via_api()
    print(f"API 登录成功: {user_data['username']} (id={user_data['id']})")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )
        page = context.new_page()
        results = []

        # 1. 未登录态登录页
        try:
            page.goto(f"{BASE}/login", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(800)
            page.screenshot(path=str(SAVE_DIR / "login.png"), full_page=True)
            results.append(("login", "ok"))
        except Exception as e:
            results.append(("login", f"fail: {e}"))

        # 2. 注入 localStorage 模拟登录态
        try:
            page.goto(f"{BASE}/", wait_until="domcontentloaded", timeout=15000)
            page.evaluate(
                "(user) => localStorage.setItem('mediapilot-user', JSON.stringify(user))",
                user_data,
            )
            page.wait_for_timeout(500)
            results.append(("inject-token", "ok"))
        except Exception as e:
            results.append(("inject-token", f"fail: {e}"))

        # 3. HeroSection 首页（登录态）
        try:
            page.goto(f"{BASE}/", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1200)
            page.screenshot(path=str(SAVE_DIR / "home.png"), full_page=True)
            results.append(("home", "ok"))
        except Exception as e:
            results.append(("home", f"fail: {e}"))

        # 4. 各功能页：通过点击 feature card 进入
        page_targets = [
            ("trending", "热点搜索"),
            ("copywriting", "口播文案"),
            ("shoot-script", "拍摄脚本"),
            ("subscription", "话题订阅"),
            ("content-library", "内容库"),
            ("transcription", "智能转录"),
            ("video-analysis", "视频分析"),
        ]
        for name, tab_title in page_targets:
            try:
                goto_content_page(page, name)
                page.wait_for_timeout(1800)
                page.screenshot(path=str(SAVE_DIR / f"{name}.png"), full_page=True)
                results.append((name, "ok"))
            except Exception as e:
                results.append((name, f"fail: {e}"))

        # 5. 热点搜索：输入关键词 + 搜索 + 截图
        try:
            goto_content_page(page, "trending")
            page.wait_for_timeout(1500)
            inputs = page.locator("input").all()
            keyword_typed = False
            for inp in inputs:
                placeholder = inp.get_attribute("placeholder") or ""
                if any(k in placeholder for k in ["关键词", "搜索", "输入", "关键字"]):
                    inp.fill("AI")
                    keyword_typed = True
                    break
            if not keyword_typed and len(inputs) > 0:
                inputs[0].fill("AI")
            search_clicked = False
            for btn_text in ["搜索", "搜 索", "开始搜索", "热点搜索"]:
                try:
                    btn = page.get_by_role("button", name=btn_text)
                    if btn.count() > 0:
                        btn.first.click()
                        search_clicked = True
                        break
                except Exception:
                    continue
            if not search_clicked:
                page.keyboard.press("Enter")
            page.wait_for_timeout(8000)
            page.screenshot(path=str(SAVE_DIR / "trending.png"), full_page=True)
            results.append(("trending-search", "ok"))
        except Exception as e:
            results.append(("trending-search", f"fail: {e}"))

        browser.close()

        print("\n=== 截图结果 ===")
        for name, status in results:
            print(f"  {name:25s} {status}")
        print(f"\n保存目录: {SAVE_DIR}")
        ok = sum(1 for _, s in results if s == "ok")
        print(f"成功: {ok}/{len(results)}")


if __name__ == "__main__":
    shoot()
