
"""
测试火山方舟API连接
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("  测试火山方舟API连接")
print("="*60)
print()

from backend.core.ai_service import ai_manager

# 配置API
print("正在配置AI服务...")
ai_manager.configure_service(
    provider="ark",
    api_key="1a73929c-d549-43e8-b03f-0d6e3e979771",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    model="doubao-seed-2.0-pro-260215"
)
print("  ✓ 配置完成")
print()

# 检查服务是否可用
service = ai_manager.get_current_service()
print(f"服务类型: {type(service).__name__}")
print(f"服务可用: {service.is_available() if service else False}")
print()

# 测试生成
print("正在测试API调用...")
print("  发送: 你好，请简单介绍一下自己")
print()

try:
    result = ai_manager.generate("你好，请简单介绍一下自己", max_tokens=500)
    print("="*60)
    print("  回复:")
    print("="*60)
    print(result)
    print("="*60)
    print()
    if result:
        print("  ✓ API调用成功！")
    else:
        print("  ✗ API返回空结果")
except Exception as e:
    print(f"  ✗ 发生错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
print("  测试完成")
print("="*60)
print()

try:
    input("按回车键退出...")
except:
    pass
