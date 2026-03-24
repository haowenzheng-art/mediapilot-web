
"""
MediaPilot 环境测试脚本
运行这个脚本来检查你的Python环境是否就绪
"""
import sys
import os

print("=" * 50)
print("  MediaPilot 环境检查")
print("=" * 50)
print()

# 1. 检查Python版本
print("[1/6] 检查Python版本...")
print(f"  Python路径: {sys.executable}")
print(f"  Python版本: {sys.version}")
if sys.version_info &gt;= (3, 8):
    print("  ✓ Python版本符合要求")
else:
    print("  ✗ Python版本过低，建议3.8+")
print()

# 2. 检查项目路径
print("[2/6] 检查项目路径...")
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"  项目目录: {project_dir}")
os.chdir(project_dir)
print(f"  当前工作目录: {os.getcwd()}")
print("  ✓ 路径检查完成")
print()

# 3. 添加到sys.path
print("[3/6] 设置模块路径...")
sys.path.insert(0, project_dir)
print("  ✓ 模块路径已添加")
print()

# 4. 检查基础依赖
print("[4/6] 检查基础依赖...")

required_packages = [
    ("fastapi", "FastAPI", "后端API框架"),
    ("uvicorn", "Uvicorn", "ASGI服务器"),
    ("pydantic", "Pydantic", "数据验证"),
    ("requests", "Requests", "HTTP请求"),
]

for package, name, desc in required_packages:
    try:
        __import__(package)
        print(f"  ✓ {name} 已安装 ({desc})")
    except ImportError:
        print(f"  ✗ {name} 未安装 ({desc})")

print()

# 5. 检查桌面端依赖
print("[5/6] 检查桌面端依赖...")
try:
    import PyQt5
    print("  ✓ PyQt5 已安装 (桌面GUI)")
except ImportError:
    print("  ✗ PyQt5 未安装 (桌面GUI)")

try:
    import openpyxl
    print("  ✓ openpyxl 已安装 (Excel处理)")
except ImportError:
    print("  ✗ openpyxl 未安装 (Excel处理)")

print()

# 6. 检查可选AI依赖
print("[6/6] 检查AI依赖（可选）...")

ai_packages = [
    ("anthropic", "Anthropic SDK"),
    ("openai", "OpenAI SDK"),
]

for package, name in ai_packages:
    try:
        __import__(package)
        print(f"  ✓ {name} 已安装")
    except ImportError:
        print(f"  - {name} 未安装 (可选)")

print()
print("=" * 50)
print("  检查完成！")
print("=" * 50)
print()
print("如果缺少依赖，可以运行:")
print("  pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple")
print()
print("然后:")
print("  1. 运行: 用Anaconda运行.bat")
print("  或者")
print("  2. 先运行: 启动后端.bat")
print("     再运行: 启动桌面端.bat")
print()
input("按回车键退出...")

