
# -*- coding: utf-8 -*-
"""
MediaPilot - Auto Demo
Shows all features automatically
"""
import sys
import os
import random

project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)


class MockDataGenerator:
    """Mock data generator"""

    def __init__(self):
        self.platforms = ["Douyin", "Xiaohongshu", "Weibo"]

    def search_trending(self, keyword):
        """Search trending topics"""
        topics = [
            f"{keyword} new trends",
            f"{keyword} viral content analysis",
            f"How to do {keyword}",
            f"{keyword} mistakes to avoid",
            f"{keyword} beginner tutorial"
        ]
        results = []
        for i, title in enumerate(topics):
            results.append({
                "title": title,
                "heat_index": random.randint(10000, 999999),
                "platform": random.choice(self.platforms),
                "trend": random.choice(["rising", "stable", "falling"])
            })
        return sorted(results, key=lambda x: x["heat_index"], reverse=True)

    def search_competitors(self, niche):
        """Search competitor accounts"""
        nicknames = [
            f"{niche} expert",
            f"{niche} master",
            f"{niche} academy",
            f"{niche} sister",
            f"{niche} brother"
        ]
        accounts = []
        for i, nickname in enumerate(nicknames):
            followers = random.randint(10000, 1000000)
            accounts.append({
                "account_id": f"account_{i:04d}",
                "nickname": nickname,
                "platform": random.choice(self.platforms),
                "followers": followers,
                "total_likes": random.randint(followers * 2, followers * 20),
                "video_count": random.randint(50, 500),
                "avg_likes": round(random.uniform(100, 5000), 1)
            })
        return sorted(accounts, key=lambda x: x["followers"], reverse=True)

    def generate_script(self, topic):
        """Generate shot list script"""
        return {
            "script": [
                {"scene": 1, "duration": "0:00-0:05", "visual": "Hook opening", "audio": "Hello everyone! Today I'll share a super useful tip!"},
                {"scene": 2, "duration": "0:05-0:15", "visual": "Show topic", "audio": f"Today let's talk about {topic}"},
                {"scene": 3, "duration": "0:15-0:30", "visual": "Explain details", "audio": "How to do it? First..."},
                {"scene": 4, "duration": "0:30-0:45", "visual": "Summary", "audio": "That's all for today"},
                {"scene": 5, "duration": "0:45-0:60", "visual": "CTA", "audio": "Remember to like and follow!"}
            ],
            "copywriting": {
                "title": f"Viral title for {topic} - 90% don't know!",
                "hooks": ["Secrets you don't know!", "Save this!", "Last one is amazing"],
                "call_to_action": "Like and follow, more next time!",
                "tags": [f"#{topic}", "#newmedia", "#tips"]
            }
        }


print("="*60)
print("   MediaPilot - Auto Demo")
print("="*60)
print()
print("[INFO] This is a pure offline demo")
print("[INFO] No internet needed, no dependencies needed!")
print()

data_gen = MockDataGenerator()

# Feature 1: Trending search
print("="*60)
print("Feature 1: Search Trending Topics")
print("="*60)
keyword = "Beauty"
print(f"\nSearching: '{keyword}'")
trending = data_gen.search_trending(keyword)
print("\nTop 5:")
for i, item in enumerate(trending[:5], 1):
    print(f"\n{i}. {item['title']}")
    print(f"   Heat: {item['heat_index']:,} | Platform: {item['platform']} | Trend: {item['trend']}")

# Feature 2: Competitors
print("\n" + "="*60)
print("Feature 2: Find Competitor Accounts")
print("="*60)
niche = "Skincare"
print(f"\nSearching: '{niche}'")
competitors = data_gen.search_competitors(niche)
print("\nAccounts:")
print("\nID           Nickname        Platform     Followers   Avg Likes")
print("-"*65)
for item in competitors:
    print("%-12s %-15s %-12s %10d %12.1f" % (
        item['account_id'],
        item['nickname'],
        item['platform'],
        item['followers'],
        item['avg_likes']
    ))

# Feature 3: Script generation
print("\n" + "="*60)
print("Feature 3: Generate Shot List Script")
print("="*60)
topic = "How to make short videos"
print(f"\nTopic: '{topic}'")
script = data_gen.generate_script(topic)
print("\nShot List:")
for shot in script["script"]:
    print(f"\n[Scene {shot['scene']}] ({shot['duration']})")
    print(f"  Visual: {shot['visual']}")
    print(f"  Audio: {shot['audio']}")

copy = script["copywriting"]
print("\nCopywriting:")
print(f"  Title: {copy['title']}")
print(f"  Hooks: {', '.join(copy['hooks'])}")
print(f"  CTA: {copy['call_to_action']}")
print(f"  Tags: {' '.join(copy['tags'])}")

print("\n" + "="*60)
print("   Demo Complete!")
print("="*60)
print()
print("All features work perfectly!")
print()
print("To run the interactive version:")
print("  python demo_ascii.py")
print()

try:
    input("Press Enter to exit...")
except:
    pass

