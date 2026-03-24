
"""
测试新的ChatThread逻辑
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("  测试ChatThread逻辑")
print("="*60)
print()

# 模拟config
config = {
    "provider": "ark",
    "api_key": "1a73929c-d549-43e8-b03f-0d6e3e979771",
    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
    "model": "ep-m-20260311150444-fn2zc"
}

print("配置:")
for k, v in config.items():
    if k == "api_key":
        print(f"  {k}: {v[:20]}...")
    else:
        print(f"  {k}: {v}")
print()

# 测试逻辑
import requests

api_key = config["api_key"]
base_url = config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
model = config.get("model", "")
provider = config.get("provider", "ark")
user_text = "你好，请简单介绍一下自己"

prompt = f"你是MediaPilot的AI助手，一个专业的新媒体运营助手。请用简洁、专业、友好的语气回答用户的问题。\n\n用户问题：{user_text}"

response = ""

print(f"Provider: {provider}")
print()

if provider == "ark":
    print("使用火山方舟原生API...")
    if base_url.endswith("/responses"):
        url = base_url
    else:
        url = f"{base_url}/responses"

    print(f"URL: {url}")
    print(f"Model: {model}")
    print()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "input": [{
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}]
        }]
    }

    print("发送请求...")
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    print(f"状态码: {resp.status_code}")
    print()

    if resp.status_code == 200:
        result = resp.json()
        print("✓ 请求成功")
        if "output" in result:
            print("✓ 找到 output 字段")
            for content in result.get("output", []):
                if content.get("type") == "message":
                    print("✓ 找到 message")
                    for msg_content in content.get("content", []):
                        if msg_content.get("type") == "output_text":
                            response = msg_content.get("text", "")
                            print("✓ 找到 output_text")
                            if response:
                                print()
                                print("="*60)
                                print("  AI回复:")
                                print("="*60)
                                # 用repr避免编码问题
                                print(repr(response))
                                print("="*60)
                                break

if not response:
    print("✗ 没有获取到回复")

print()
print("测试完成!")

try:
    input("按回车键退出...")
except:
    pass

