
# -*- coding: utf-8 -*-
"""
MediaPilot - 纯离线中文版演示
不需要网络，不需要安装依赖！
"""
import sys
import os
import random

project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)


class MockDataGenerator:
    """模拟数据生成器"""

    def __init__(self):
        self.platforms = ["抖音", "小红书", "微博"]

    def search_trending(self, keyword):
        """搜索热点话题"""
        topics = [
            f"{keyword}行业新趋势",
            f"{keyword}爆款内容分析",
            f"{keyword}怎么做",
            f"{keyword}避坑指南",
            f"{keyword}入门教程"
        ]
        results = []
        for i, title in enumerate(topics):
            results.append({
                "title": title,
                "heat_index": random.randint(10000, 999999),
                "platform": random.choice(self.platforms),
                "trend": random.choice(["上升", "平稳", "下降"])
            })
        return sorted(results, key=lambda x: x["heat_index"], reverse=True)

    def search_competitors(self, niche):
        """搜索对标账号"""
        nicknames = [
            f"{niche}小能手",
            f"{niche}达人",
            f"{niche}研习社",
            f"{niche}学姐",
            f"{niche}学长"
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
        """生成分镜头脚本"""
        return {
            "script": [
                {"scene": 1, "duration": "0:00-0:05", "visual": "开头吸引眼球", "audio": "大家好！今天给大家分享一个超实用的技巧！"},
                {"scene": 2, "duration": "0:05-0:15", "visual": "展示主题", "audio": f"今天我们来聊一聊{topic}"},
                {"scene": 3, "duration": "0:15-0:30", "visual": "详细讲解", "audio": "具体怎么做呢？首先..."},
                {"scene": 4, "duration": "0:30-0:45", "visual": "总结升华", "audio": "以上就是今天的全部内容"},
                {"scene": 5, "duration": "0:45-0:60", "visual": "引导关注", "audio": "记得点赞关注，下期更精彩！"}
            ],
            "copywriting": {
                "title": f"{topic}爆款标题 - 90%的人都不知道！",
                "hooks": ["你还不知道的秘密！", "建议收藏！", "最后一条绝了"],
                "call_to_action": "点赞关注，下期更精彩！",
                "tags": [f"#{topic}", "#新媒体", "#干货"]
            }
        }


print("="*60)
print("   MediaPilot - 媒体领航员 (纯离线演示版)")
print("="*60)
print()
print("[说明] 这是纯离线演示版，所有数据都是模拟的")
print("[注意] 不需要网络，不需要安装任何依赖！")
print()

data_gen = MockDataGenerator()

# 功能1：热点搜索
print("="*60)
print("功能1：搜索行业热点")
print("="*60)
keyword = "美妆"
print(f"\n搜索关键词：「{keyword}」")
trending = data_gen.search_trending(keyword)
print("\n前5名：")
for i, item in enumerate(trending[:5], 1):
    print(f"\n{i}. {item['title']}")
    print(f"   热度：{item['heat_index']:,} | 平台：{item['platform']} | 趋势：{item['trend']}")

# 功能2：对标账号
print("\n" + "="*60)
print("功能2：查找对标账号")
print("="*60)
niche = "护肤"
print(f"\n搜索赛道：「{niche}」")
competitors = data_gen.search_competitors(niche)
print("\n账号列表：")
print("\n账号ID       昵称            平台         粉丝数      平均点赞")
print("-"*65)
for item in competitors:
    print("%-12s %-15s %-12s %10d %12.1f" % (
        item['account_id'],
        item['nickname'],
        item['platform'],
        item['followers'],
        item['avg_likes']
    ))

# 功能3：分镜头脚本
print("\n" + "="*60)
print("功能3：生成分镜头脚本")
print("="*60)
topic = "如何做短视频"
print(f"\n选题：「{topic}」")
script = data_gen.generate_script(topic)
print("\n分镜头脚本：")
for shot in script["script"]:
    print(f"\n【场景 {shot['scene']}】({shot['duration']})")
    print(f"  画面：{shot['visual']}")
    print(f"  台词：{shot['audio']}")

copy = script["copywriting"]
print("\n文案建议：")
print(f"  标题：{copy['title']}")
print(f"  钩子：{'、'.join(copy['hooks'])}")
print(f"  引导语：{copy['call_to_action']}")
print(f"  标签：{' '.join(copy['tags'])}")

print("\n" + "="*60)
print("   演示完成！")
print("="*60)
print()
print("所有功能正常运行！")
print()
print("要运行交互版本：")
print("  python demo_cn.py")
print()

try:
    input("按回车键退出...")
except:
    pass

