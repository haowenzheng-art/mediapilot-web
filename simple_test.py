
"""
这是一个超简单的测试 - 只验证Python基本功能
"""

print("="*50)
print("  超简单测试")
print("="*50)
print()

print("测试1: print() 函数")
print("  ✓ 正常")
print()

print("测试2: 标准库导入")
import random
print("  ✓ random 导入成功")
import json
print("  ✓ json 导入成功")
print()

print("测试3: 生成随机数")
num = random.randint(1, 100)
print(f"  ✓ 生成随机数: {num}")
print()

print("测试4: 模拟数据")
topics = ["美妆新趋势", "爆款内容分析", "运营技巧"]
for i, t in enumerate(topics, 1):
    heat = random.randint(10000, 999999)
    print(f"  {i}. {t} (热度: {heat:,})")
print()

print("="*50)
print("  所有测试通过！")
print("="*50)
print()
print("你的Python完全正常！")
print()
print("接下来可以运行:")
print("  python demo_offline.py")
print()
print("或者双击:")
print("  启动离线演示版.bat")
print()

try:
    input("按回车键退出...")
except:
    pass

