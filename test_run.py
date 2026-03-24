
print("测试开始...")
print("Python版本:", __import__('sys').version)
print("当前目录:", __import__('os').getcwd())
print()
print("✓ 基础功能正常！")
print()
print("现在测试 random 模块...")
import random
print("  随机数:", random.randint(1, 100))
print()
print("✓ 全部测试通过！")
print()
input("按回车键退出...")

