"""
测试ark-code-latest生成脚本的完整流程
模拟后端ai_service.py的逻辑
"""
import json
import httpx
import os
import re
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

# 模拟content.py中generate_content_script的prompt
topic = "AI工具测评"
platform = "xiaohongshu"
duration = 60
style = "干货分享"

prompt = f"""你是一个专业的新媒体内容创作专家。请为以下主题创作短视频分镜头脚本。

主题: {topic}
平台: {platform}
目标时长: {duration}秒
风格: {style}

请直接返回JSON格式，不要使用markdown代码块包装，不要其他文字:
{{
    "script": [
        {{
            "scene": 1,
            "duration": "0:00-0:05",
            "visual": "画面描述",
            "audio": "台词",
            "notes": "注意事项"
        }}
    ],
    "copywriting": {{
        "title": "爆款标题",
        "hooks": ["钩子1", "钩子2", "钩子3"],
        "call_to_action": "引导语",
        "tags": ["#标签1", "#标签2"]
    }}
}}"""

data = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "max_tokens": 3000,
    "temperature": 0.6
}

print(f"模型: {MODEL}")
print(f"主题: {topic}")
print("-" * 50)
print("发送请求...")
print("-" * 50)

try:
    response = httpx.post(url, headers=headers, json=data, timeout=60)
    print(f"状态码: {response.status_code}")
    print("-" * 50)

    if response.status_code == 200:
        response_json = response.json()
        content = response_json["choices"][0]["message"]["content"]

        print(f"AI原始返回内容:")
        print(content)
        print("-" * 50)

        # 模拟ai_service.py的解析逻辑
        print("\n开始解析JSON...")

        # 先尝试提取 markdown 代码块
        json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            print("✓ 找到markdown代码块")
            json_str = json_match.group(1).strip()
            print(f"提取的JSON字符串（前200字符）: {json_str[:200]}...")
            try:
                parsed = json.loads(json_str)
                print("✓ JSON解析成功！")
                print(f"解析后的结构: {list(parsed.keys())}")
                print(json.dumps(parsed, ensure_ascii=False, indent=2))
            except json.JSONDecodeError as e:
                print(f"✗ JSON解析失败: {e}")
                print(f"完整JSON字符串: {json_str}")
        else:
            print("✓ 没有找到markdown代码块，直接解析")
            # 如果没有 markdown 代码块，回退到原来的方式
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group()
                print(f"提取的JSON字符串（前200字符）: {json_str[:200]}...")
                try:
                    parsed = json.loads(json_str)
                    print("✓ JSON解析成功！")
                    print(f"解析后的结构: {list(parsed.keys())}")
                except json.JSONDecodeError as e:
                    print(f"✗ JSON解析失败: {e}")
                    print(f"完整JSON字符串: {json_str}")
            else:
                print("✗ 没有找到JSON格式的数据")

    else:
        print(f"API请求失败: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()