
"""
快速测试 - 验证离线演示版是否能正常工作
"""
import sys
import os

print("="*50)
print("  MediaPilot - 环境快速测试")
print("="*50)
print()

# 1. 测试Python
print("[1/3] 测试Python...")
print(f"  Python版本: {sys.version}")
print("  ✓ Python正常")
print()

# 2. 测试标准库
print("[2/3] 测试标准库...")
import random
import json
from datetime import datetime
print("  ✓ random 正常")
print("  ✓ json 正常")
print("  ✓ datetime 正常")
print("  所有标准库正常！")
print()

# 3. 测试导入离线演示模块
print("[3/3] 测试离线演示模块...")
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from demo_offline import MockDataGenerator
    print("  ✓ 导入成功")

    # 测试生成数据
    data_gen = MockDataGenerator()

    print("\n  测试生成热点数据...")
    trending = data_gen.search_trending("美妆")
    print(f"  ✓ 生成了 {len(trending)} 条热点")

    print("  测试生成对标账号...")
    competitors = data_gen.search_competitors("护肤")
    print(f"  ✓ 生成了 {len(competitors)} 个账号")

    print("  测试生成分镜头脚本...")
    script = data_gen.generate_script("如何做短视频")
    print(f"  ✓ 生成了 {len(script['script'])} 个场景")

    print()
    print("="*50)
    print("  所有测试通过！")
    print("="*50)
    print()
    print("现在你可以运行:")
    print("  1. 双击 '启动离线演示版.bat'")
    print("  或者")
    print("  2. 运行: python demo_offline.py")
    print()

except Exception as e:
    print(f"  ✗ 出错: {e}")
    import traceback
    traceback.print_exc()

print()
input("按回车键退出...")

