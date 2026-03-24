
"""
MediaPilot - 纯离线演示版
只使用Python标准库，无需安装任何依赖！
"""
import sys
import os
import random
import json
from datetime import datetime, timedelta

# 添加项目路径
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)


class MockDataGenerator:
    """模拟数据生成器"""

    def __init__(self):
        self.platforms = {
            "douyin": "抖音",
            "xiaohongshu": "小红书",
            "weibo": "微博"
        }

    def search_trending(self, keyword, days=7):
        """搜索热点"""
        topics = [
            f"{keyword}行业新趋势",
            f"{keyword}爆款内容分析",
            f"{keyword}怎么做",
            f"{keyword}避坑指南",
            f"{keyword}入门教程",
            f"{keyword}运营技巧",
            f"{keyword}数据增长",
            f"{keyword}流量密码"
        ]
        results = []
        for i, title in enumerate(topics):
            results.append({
                "title": title,
                "heat_index": random.randint(10000, 999999),
                "platform": random.choice(list(self.platforms.values())),
                "trend": random.choice(["上升", "平稳", "下降"]),
                "summary": f"这是关于{title}的热点摘要..."
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
                "platform": random.choice(list(self.platforms.values())),
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
                {"scene": 1, "duration": "0:00-0:05", "visual": "开头吸引眼球", "audio": "大家好，今天给大家分享一个超实用的技巧！", "notes": "要有冲击力"},
                {"scene": 2, "duration": "0:05-0:15", "visual": f"展示主题: {topic}", "audio": f"今天我们来聊一聊{topic}", "notes": ""},
                {"scene": 3, "duration": "0:15-0:30", "visual": "详细讲解", "audio": "具体怎么做呢？首先...", "notes": "配合手势"},
                {"scene": 4, "duration": "0:30-0:45", "visual": "总结升华", "audio": "以上就是今天的全部内容", "notes": ""},
                {"scene": 5, "duration": "0:45-0:60", "visual": "引导关注", "audio": "记得点赞关注，下期更精彩！", "notes": "强调CTA"}
            ],
            "copywriting": {
                "title": f"{topic}爆款标题 - 90%的人都不知道！",
                "hooks": ["你还不知道的秘密！", "建议收藏！", "最后一条绝了"],
                "call_to_action": "点赞关注，下期更精彩！",
                "tags": [f"#{topic}", "#新媒体", "#干货"]
            }
        }

    def get_mock_transcript(self):
        """获取模拟逐字稿"""
        return {
            "full_transcript": "大家好，今天给大家分享一个非常有用的技巧。首先，我们需要准备以下材料。第一步，我们先这样做。第二步，再那样做。大家学会了吗？记得点赞关注哦！",
            "lines": [
                {"time": "00:00", "text": "大家好"},
                {"time": "00:03", "text": "今天给大家分享一个非常有用的技巧"},
                {"time": "00:08", "text": "首先，我们需要准备以下材料"},
                {"time": "00:12", "text": "第一步，我们先这样做"},
                {"time": "00:18", "text": "第二步，再那样做"},
                {"time": "00:25", "text": "大家学会了吗"},
                {"time": "00:28", "text": "记得点赞关注哦"}
            ]
        }


def print_banner():
    """打印横幅"""
    print("\n" + "="*60)
    print("   MediaPilot - 媒体领航员 (纯离线演示版)")
    print("="*60)
    print("\n【说明】这是纯离线演示版，所有数据都是模拟的")
    print("【注意】不需要网络，不需要安装任何依赖！\n")


def print_menu():
    """打印菜单"""
    print("请选择功能:")
    print("  [1] 🔍 搜索行业热点")
    print("  [2] 🎯 查找对标账号")
    print("  [3] 🎬 获取爆款视频逐字稿")
    print("  [4] ✍️  生成分镜头脚本")
    print("  [5] 📋 查看所有功能演示")
    print("  [0] 退出")
    print()


def display_trending(data):
    """显示热点"""
    print("\n" + "-"*60)
    print("🔥 热点话题排行")
    print("-"*60)
    for i, item in enumerate(data[:5], 1):
        print(f"\n{i}. {item['title']}")
        print(f"   热度: {item['heat_index']:,} | 平台: {item['platform']} | 趋势: {item['trend']}")
        print(f"   摘要: {item['summary']}")


def display_competitors(data):
    """显示对标账号"""
    print("\n" + "-"*60)
    print("🎯 对标账号列表")
    print("-"*60)
    print(f"\n{'ID':&lt;12} {'昵称':&lt;15} {'平台':&lt;8} {'粉丝数':&gt;10} {'平均点赞':&gt;10}")
    print("-"*65)
    for item in data:
        print(f"{item['account_id']:&lt;12} {item['nickname']:&lt;15} {item['platform']:&lt;8} {item['followers']:&gt;10,} {item['avg_likes']:&gt;10,.1f}")


def display_transcript(data):
    """显示逐字稿"""
    print("\n" + "-"*60)
    print("📝 视频逐字稿")
    print("-"*60)
    print(f"\n完整文稿: {data['full_transcript']}\n")
    print("时间轴:")
    for line in data['lines']:
        print(f"  [{line['time']}] {line['text']}")


def display_script(data):
    """显示分镜头脚本"""
    print("\n" + "-"*60)
    print("🎬 分镜头脚本")
    print("-"*60)
    for shot in data['script']:
        print(f"\n【场景 {shot['scene']}】 ({shot['duration']})")
        print(f"  画面: {shot['visual']}")
        print(f"  台词: {shot['audio']}")
        if shot.get('notes'):
            print(f"  备注: {shot['notes']}")

    copy = data['copywriting']
    print(f"\n" + "-"*60)
    print("📋 文案建议")
    print("-"*60)
    print(f"\n标题: {copy['title']}")
    print("\n钩子:")
    for hook in copy['hooks']:
        print(f"  - {hook}")
    print(f"\n引导语: {copy['call_to_action']}")
    print(f"\n标签: {' '.join(copy['tags'])}")


def main():
    """主函数"""
    print_banner()

    data_gen = MockDataGenerator()

    while True:
        print_menu()
        choice = input("请输入选项 (0-5): ").strip()

        if choice == "0":
            print("\n感谢使用 MediaPilot！再见！\n")
            break

        elif choice == "1":
            keyword = input("\n请输入行业关键词 (例如: 美妆): ").strip() or "美妆"
            print(f"\n正在搜索「{keyword}」最近一周热点...")
            result = data_gen.search_trending(keyword)
            display_trending(result)
            print()

        elif choice == "2":
            niche = input("\n请输入赛道/领域 (例如: 护肤): ").strip() or "护肤"
            print(f"\n正在搜索「{niche}」赛道的对标账号...")
            result = data_gen.search_competitors(niche)
            display_competitors(result)
            print()

        elif choice == "3":
            print("\n正在获取爆款视频逐字稿 (模拟)...")
            result = data_gen.get_mock_transcript()
            display_transcript(result)
            print()

        elif choice == "4":
            topic = input("\n请输入选题 (例如: 如何护肤): ").strip() or "如何护肤"
            print(f"\n正在为「{topic}」生成分镜头脚本...")
            result = data_gen.generate_script(topic)
            display_script(result)
            print()

        elif choice == "5":
            print("\n" + "="*60)
            print("   完整功能演示")
            print("="*60)

            # 演示所有功能
            keyword = "美妆"
            print(f"\n【1/4】搜索「{keyword}」热点...")
            trending = data_gen.search_trending(keyword)
            display_trending(trending)

            niche = "护肤"
            print(f"\n【2/4】搜索「{niche}」对标账号...")
            competitors = data_gen.search_competitors(niche)
            display_competitors(competitors)

            print(f"\n【3/4】获取视频逐字稿...")
            transcript = data_gen.get_mock_transcript()
            display_transcript(transcript)

            topic = "如何做短视频"
            print(f"\n【4/4】为「{topic}」生成分镜头脚本...")
            script = data_gen.generate_script(topic)
            display_script(script)

            print("\n" + "="*60)
            print("   演示完成！")
            print("="*60)
            print()

        else:
            print("\n无效选项，请重新输入！\n")

        input("按回车键继续...")
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已中断。再见！")
    except Exception as e:
        print(f"\n\n出错了: {e}")
        input("按回车键退出...")

