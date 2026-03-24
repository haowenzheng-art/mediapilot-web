
"""
测试火山方舟API - 只提取回复
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("  测试火山方舟API")
print("="*60)
print()

import requests

# 配置
api_key = "1a73929c-d549-43e8-b03f-0d6e3e979771"
base_url = "https://ark.cn-beijing.volces.com/api/v3"
model = "ep-m-20260311150444-fn2zc"
prompt = "你好，请简单介绍一下自己"

# 构建URL
if base_url.endswith("/responses"):
    url = base_url
else:
    url = f"{base_url}/responses"

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

        # 尝试提取回复 - 多种方式
        reply = ""

        # 方式1: 原有的方式
        if "output" in result:
            for content in result.get("output", []):
                if content.get("type") == "message":
                    for msg_content in content.get("content", []):
                        if msg_content.get("type") == "output_text":
                            reply = msg_content.get("text", "")
                            if reply:
                                break

        # 如果方式1没找到，试试其他可能的字段
        if not reply:
            print("方式1未找到，尝试其他方式...")
            # 打印所有键看看结构
            print(f"响应顶层键: {list(result.keys())}")

        if reply:
            print("="*60)
            print("  AI回复:")
            print("="*60)
            # 避免编码问题，用repr看原始内容
            print(repr(reply))
            print()
            print("="*60)
            print("  成功!")
        else:
            print("未能提取到回复")
            print("完整响应键:", list(result.keys()))

    else:
        print(f"请求失败!")
        print(f"响应: {response.text}")

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

