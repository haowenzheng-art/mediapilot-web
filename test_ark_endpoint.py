
"""
测试火山方舟接入点ID
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("  Test Ark Endpoint")
print("="*60)
print()

from backend.core.ai_service import ai_manager

# 配置API - 使用你的接入点ID
print("Configuring AI service...")
print(f"  Endpoint ID: ep-m-20260311150444-fn2zc")
ai_manager.configure_service(
    provider="ark",
    api_key="1a73929c-d549-43e8-b03f-0d6e3e979771",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    model="ep-m-20260311150444-fn2zc"
)
print("  OK: Configured")
print()

# 检查服务是否可用
service = ai_manager.get_current_service()
print(f"Service type: {type(service).__name__}")
print(f"Service available: {service.is_available() if service else False}")
print()

# 测试生成
print("Testing API call...")
print("  Sending: Hello, please introduce yourself briefly")
print()

try:
    result = ai_manager.generate("Hello, please introduce yourself briefly", max_tokens=500)
    print("="*60)
    print("  Response:")
    print("="*60)
    print(result)
    print("="*60)
    print()
    if result:
        print("  OK: API call successful!")
    else:
        print("  ERROR: API returned empty result")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
print("  Test Complete")
print("="*60)
print()

try:
    input("Press Enter to exit...")
except:
    pass

