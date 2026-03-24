
"""
测试配置加载逻辑
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
import json

# 模拟load_config
def load_config():
    config_path = Path.home() / ".mediapilot_config.json"
    print(f"配置文件路径: {config_path}")
    print(f"配置文件存在: {config_path.exists()}")

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                print(f"已加载配置: {config}")
                return config
        except Exception as e:
            print(f"加载配置失败: {e}")

    default_config = {
        "provider": "ark",
        "api_key": "1a73929c-d549-43e8-b03f-0d6e3e979771",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "ep-m-20260311150444-fn2zc"
    }
    print(f"使用默认配置: {default_config}")
    return default_config

# 测试
print("="*60)
print("  测试配置加载")
print("="*60)
config = load_config()
print()
print("配置内容:")
for k, v in config.items():
    print(f"  {k}: {v}")

print()
print("="*60)
print("  测试AI服务初始化")
print("="*60)

from backend.core.ai_service import ai_manager

try:
    ai_manager.configure_service(
        provider=config["provider"],
        api_key=config["api_key"],
        base_url=config["base_url"],
        model=config["model"]
    )
    print("AI服务配置成功！")

    service = ai_manager.get_current_service()
    print(f"服务类型: {type(service).__name__}")
    print(f"服务可用: {service.is_available()}")

    print()
    print("测试发送消息...")
    result = ai_manager.generate("Hello, 请用中文回复", max_tokens=200)
    print(f"回复: {result}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)

