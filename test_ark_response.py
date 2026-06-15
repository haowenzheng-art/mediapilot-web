"""
测试ark-code-latest的响应格式
"""
import json
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AI_API_KEY")
BASE_URL = os.getenv("AI_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding/v1")
MODEL = os.getenv("AI_MODEL", "ark-code-latest")

url = f"{BASE_URL}/chat/completions"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": "请用JSON格式返回一个简单的示例，包含title和content字段"}
    ],
    "max_tokens": 100,
    "temperature": 0.6
}

print(f"请求URL: {url}")
print(f"模型: {MODEL}")
print(f"请求体: {json.dumps(data, ensure_ascii=False, indent=2)}")
print("-" * 50)

try:
    response = httpx.post(url, headers=headers, json=data, timeout=60)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print("-" * 50)
    print(f"完整响应内容:")
    print(response.text)
    print("-" * 50)

    # 尝试解析响应
    response_json = response.json()
    print(f"解析后的JSON:")
    print(json.dumps(response_json, ensure_ascii=False, indent=2))

except Exception as e:
    print(f"错误: {e}")