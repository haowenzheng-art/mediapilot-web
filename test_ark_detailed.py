
"""
详细测试火山方舟API
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("  详细测试火山方舟API")
print("="*60)
print()

import requests

# 配置
api_key = "1a73929c-d549-43e8-b03f-0d6e3e979771"
base_url = "https://ark.cn-beijing.volces.com/api/v3"
model = "ep-m-20260311150444-fn2zc"
prompt = "你好，请简单介绍一下自己"

print(f"API Key: {api_key[:20]}...")
print(f"Base URL: {base_url}")
print(f"Model: {model}")
print(f"Prompt: {prompt}")
print()

# 构建URL
if base_url.endswith("/responses"):
    url = base_url
else:
    url = f"{base_url}/responses"

print(f"请求URL: {url}")
print()

# 构建请求头
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 构建请求体
data = {
    "model": model,
    "input": [{
        "role": "user",
        "content": [{"type": "input_text", "text": prompt}]
    }]
}

print("发送请求...")
try:
    response = requests.post(url, headers=headers, json=data, timeout=30)
    print(f"状态码: {response.status_code}")
    print()

    if response.status_code == 200:
        result = response.json()
        print("="*60)
        print("  完整响应:")
        print("="*60)
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()

        # 尝试提取回复
        print("="*60)
        print("  提取回复:")
        print("="*60)

        if "output" in result:
            print("✓ 找到 'output' 字段")
            for content in result.get("output", []):
                print(f"  - 内容类型: {content.get('type')}")
                if content.get("type") == "message":
                    print("  ✓ 找到 'message' 类型")
                    if "content" in content:
                        print("  ✓ 找到 'content' 字段")
                        for msg_content in content.get("content", []):
                            print(f"    - 消息类型: {msg_content.get('type')}")
                            if msg_content.get("type") == "output_text":
                                text = msg_content.get("text", "")
                                print(f"    ✓ 找到回复文本:")
                                print(f"      {text[:100]}...")
        else:
            print("✗ 没有找到 'output' 字段")
    else:
        print(f"请求失败!")
        print(f"响应内容: {response.text}")

except Exception as e:
    print(f"发生异常: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)

try:
    input("按回车键退出...")
except:
    pass

