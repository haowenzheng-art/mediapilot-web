
# -*- coding: utf-8 -*-
"""
MediaPilot - Offline Demo (ASCII version)
No dependencies needed, works without internet!
"""
import sys
import os
import random
import json
from datetime import datetime, timedelta

# Add project path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)


class MockDataGenerator:
    """Mock data generator"""

    def __init__(self):
        self.platforms = {
            "douyin": "Douyin",
            "xiaohongshu": "Xiaohongshu",
            "weibo": "Weibo"
        }

    def search_trending(self, keyword, days=7):
        """Search trending topics"""
        topics = [
            f"{keyword} new trends",
            f"{keyword} viral content analysis",
            f"How to do {keyword}",
            f"{keyword} mistakes to avoid",
            f"{keyword} beginner tutorial",
            f"{keyword} operation tips",
            f"{keyword} growth hacking",
            f"{keyword} traffic secrets"
        ]
        results = []
        for i, title in enumerate(topics):
            results.append({
                "title": title,
                "heat_index": random.randint(10000, 999999),
                "platform": random.choice(list(self.platforms.values())),
                "trend": random.choice(["rising", "stable", "falling"]),
                "summary": f"This is a summary about {title}..."
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
                "platform": random.choice(list(self.platforms.values())),
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
                {"scene": 1, "duration": "0:00-0:05", "visual": "Hook opening", "audio": "Hello everyone! Today I'll share a super useful tip!", "notes": "Be impactful"},
                {"scene": 2, "duration": "0:05-0:15", "visual": f"Show topic: {topic}", "audio": f"Today let's talk about {topic}", "notes": ""},
                {"scene": 3, "duration": "0:15-0:30", "visual": "Explain details", "audio": "How to do it? First...", "notes": "Use gestures"},
                {"scene": 4, "duration": "0:30-0:45", "visual": "Summary", "audio": "That's all for today", "notes": ""},
                {"scene": 5, "duration": "0:45-0:60", "visual": "CTA", "audio": "Remember to like and follow!", "notes": "Emphasize CTA"}
            ],
            "copywriting": {
                "title": f"Viral title for {topic} - 90% don't know!",
                "hooks": ["Secrets you don't know!", "Save this!", "Last one is amazing"],
                "call_to_action": "Like and follow, more next time!",
                "tags": [f"#{topic}", "#newmedia", "#tips"]
            }
        }

    def get_mock_transcript(self):
        """Get mock transcript"""
        return {
            "full_transcript": "Hello everyone, today I'll share a very useful tip. First, we need to prepare these materials. Step one, do this. Step two, do that. Got it? Remember to like and follow!",
            "lines": [
                {"time": "00:00", "text": "Hello everyone"},
                {"time": "00:03", "text": "today I'll share a very useful tip"},
                {"time": "00:08", "text": "First, we need to prepare these materials"},
                {"time": "00:12", "text": "Step one, do this"},
                {"time": "00:18", "text": "Step two, do that"},
                {"time": "00:25", "text": "Got it?"},
                {"time": "00:28", "text": "Remember to like and follow!"}
            ]
        }


def print_banner():
    """Print banner"""
    print("\n" + "="*60)
    print("   MediaPilot - Offline Demo")
    print("="*60)
    print("\n[INFO] This is a pure offline demo with mock data")
    print("[INFO] No internet needed, no dependencies needed!\n")


def print_menu():
    """Print menu"""
    print("Please choose a feature:")
    print("  [1] Search industry trending topics")
    print("  [2] Find competitor accounts")
    print("  [3] Get viral video transcript")
    print("  [4] Generate shot list script")
    print("  [5] Full demo - show all features")
    print("  [0] Exit")
    print()


def display_trending(data):
    """Display trending"""
    print("\n" + "-"*60)
    print("Trending Topics")
    print("-"*60)
    for i, item in enumerate(data[:5], 1):
        print(f"\n{i}. {item['title']}")
        print(f"   Heat: {item['heat_index']:,} | Platform: {item['platform']} | Trend: {item['trend']}")
        print(f"   Summary: {item['summary']}")


def display_competitors(data):
    """Display competitors"""
    print("\n" + "-"*60)
    print("Competitor Accounts")
    print("-"*60)
    print()
    print("ID           Nickname        Platform     Followers   Avg Likes")
    print("-"*65)
    for item in data:
        print("%-12s %-15s %-12s %10d %12.1f" % (
            item['account_id'],
            item['nickname'],
            item['platform'],
            item['followers'],
            item['avg_likes']
        ))


def display_transcript(data):
    """Display transcript"""
    print("\n" + "-"*60)
    print("Video Transcript")
    print("-"*60)
    print(f"\nFull text: {data['full_transcript']}\n")
    print("Timeline:")
    for line in data['lines']:
        print(f"  [{line['time']}] {line['text']}")


def display_script(data):
    """Display script"""
    print("\n" + "-"*60)
    print("Shot List Script")
    print("-"*60)
    for shot in data['script']:
        print(f"\n[Scene {shot['scene']}] ({shot['duration']})")
        print(f"  Visual: {shot['visual']}")
        print(f"  Audio: {shot['audio']}")
        if shot.get('notes'):
            print(f"  Notes: {shot['notes']}")

    copy = data['copywriting']
    print(f"\n" + "-"*60)
    print("Copywriting Suggestions")
    print("-"*60)
    print(f"\nTitle: {copy['title']}")
    print("\nHooks:")
    for hook in copy['hooks']:
        print(f"  - {hook}")
    print(f"\nCTA: {copy['call_to_action']}")
    print(f"\nTags: {' '.join(copy['tags'])}")


def main():
    """Main function"""
    print_banner()

    data_gen = MockDataGenerator()

    while True:
        print_menu()
        choice = input("Enter your choice (0-5): ").strip()

        if choice == "0":
            print("\nThank you for using MediaPilot! Goodbye!\n")
            break

        elif choice == "1":
            keyword = input("\nEnter industry keyword (e.g. Beauty): ").strip() or "Beauty"
            print(f"\nSearching trending for '{keyword}' (last 7 days)...")
            result = data_gen.search_trending(keyword)
            display_trending(result)
            print()

        elif choice == "2":
            niche = input("\nEnter niche (e.g. Skincare): ").strip() or "Skincare"
            print(f"\nSearching competitors in '{niche}'...")
            result = data_gen.search_competitors(niche)
            display_competitors(result)
            print()

        elif choice == "3":
            print("\nGetting viral video transcript (mock)...")
            result = data_gen.get_mock_transcript()
            display_transcript(result)
            print()

        elif choice == "4":
            topic = input("\nEnter topic (e.g. How to make videos): ").strip() or "How to make videos"
            print(f"\nGenerating script for '{topic}'...")
            result = data_gen.generate_script(topic)
            display_script(result)
            print()

        elif choice == "5":
            print("\n" + "="*60)
            print("   Full Demo")
            print("="*60)

            # Demo all features
            keyword = "Beauty"
            print(f"\n[1/4] Searching trending for '{keyword}'...")
            trending = data_gen.search_trending(keyword)
            display_trending(trending)

            niche = "Skincare"
            print(f"\n[2/4] Searching competitors in '{niche}'...")
            competitors = data_gen.search_competitors(niche)
            display_competitors(competitors)

            print(f"\n[3/4] Getting video transcript...")
            transcript = data_gen.get_mock_transcript()
            display_transcript(transcript)

            topic = "How to do short videos"
            print(f"\n[4/4] Generating script for '{topic}'...")
            script = data_gen.generate_script(topic)
            display_script(script)

            print("\n" + "="*60)
            print("   Demo Complete!")
            print("="*60)
            print()

        else:
            print("\nInvalid choice, please try again!\n")

        input("Press Enter to continue...")
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram interrupted. Goodbye!")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        try:
            input("Press Enter to exit...")
        except:
            pass

