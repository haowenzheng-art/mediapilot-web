"""
测试JSON解析问题 - 捕获实际AI响应
"""
import sys
import os
import io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import re
from backend.core.ai_service import ai_manager

# 设置输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("  测试 AI JSON 解析问题")
print("=" * 70)
print()

# 配置 AI 服务
ai_manager.configure(
    provider="openai",
    api_key="1a73929c-d549-43e8-b03f-0d6e3e979771",
    base_url="https://ark.cn-beijing.volces.com/api/coding/v1",
    model="ark-code-latest"
)

# 生成脚本的 prompt
topic = "如何高效学习Python"
platform = "抖音"
duration = 60
style = "幽默"

prompt = f"""你是一个专业的新媒体内容创作专家。请为以下主题创作短视频分镜头脚本。

主题: {topic}
平台: {platform}
目标时长: {duration}秒
风格: {style}

请返回JSON格式，不要其他文字:
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
}}
"""

print("=" * 70)
print("  步骤 1: 获取原始 AI 响应")
print("=" * 70)

try:
    response = ai_manager.generate(prompt, max_tokens=3000)

    print(f"响应长度: {len(response)} 字符")
    print()
    print("=" * 70)
    print("  原始响应内容 (repr):")
    print("=" * 70)
    print(repr(response))
    print()

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("=" * 70)
print("  步骤 2: 测试当前正则表达式提取")
print("=" * 70)

# 当前的提取方式
json_match = re.search(r'\{[\s\S]*\}', response)

if json_match:
    extracted = json_match.group()
    print("找到匹配，长度: " + str(len(extracted)) + " 字符")
    print()
    print("提取的内容:")
    print("=" * 70)
    print(extracted)
    print("=" * 70)
    print()

    print("=" * 70)
    print("  步骤 3: 尝试解析 JSON")
    print("=" * 70)

    try:
        parsed = json.loads(extracted)
        print("SUCCESS: JSON 解析成功!")
        print("键: " + str(list(parsed.keys())))
    except json.JSONDecodeError as e:
        print("FAIL: JSON 解析失败!")
        print("错误信息: " + str(e))
        print(f"行 {e.lineno}, 列 {e.colno}, 位置 {e.pos}")

        # 显示错误位置附近的内容
        if e.pos < len(extracted):
            start = max(0, e.pos - 50)
            end = min(len(extracted), e.pos + 50)
            print()
            print("错误位置附近的内容:")
            print("=" * 70)
            print(extracted[start:end])
            print(" " * (e.pos - start) + "^")
            print("=" * 70)
else:
    print("未找到 JSON 匹配")

print()
print("=" * 70)
print("  步骤 4: 尝试其他提取方式")
print("=" * 70)

# 尝试提取 markdown 代码块
markdown_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
if markdown_match:
    print("结果 1: 找到 ```json ... ``` 代码块")
    content = markdown_match.group(1).strip()
    print("内容长度: " + str(len(content)))
    try:
        parsed = json.loads(content)
        print("  SUCCESS: JSON 解析成功!")
    except:
        print("  FAIL: JSON 解析失败")
else:
    print("结果 1: 未找到 ```json ... ``` 代码块")

# 尝试提取通用代码块
generic_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
if generic_match:
    print("结果 2: 找到 ``` ... ``` 代码块")
    content = generic_match.group(1).strip()
    print("内容长度: " + str(len(content)))
    try:
        parsed = json.loads(content)
        print("  SUCCESS: JSON 解析成功!")
    except:
        print("  FAIL: JSON 解析失败")
else:
    print("结果 2: 未找到 ``` ... ``` 代码块")

# 尝试查找最外层的大括号对
def find_outermost_braces(text):
    """查找最外层的完整 {} 对"""
    stack = []
    start = -1
    for i, char in enumerate(text):
        if char == '{':
            if not stack:
                start = i
            stack.append(i)
        elif char == '}':
            if stack:
                stack.pop()
                if not stack:
                    return text[start:i+1]
    return None

outermost = find_outermost_braces(response)
if outermost:
    print("结果 3: 找到最外层 {} 对，长度: " + str(len(outermost)))
    try:
        parsed = json.loads(outermost)
        print("  SUCCESS: JSON 解析成功!")
    except:
        print("  FAIL: JSON 解析失败")
else:
    print("结果 3: 未找到完整的 {} 对")

print()
print("=" * 70)
print("  结论:")
print("=" * 70)
print("AI 返回的响应格式: ```json ... ```")
print("当前正则表达式 r'\\{[\\s\\S]*\\}' 会匹配从第一个 { 到最后一个 }")
print("这包括 ```json 标记，导致 JSON 解析失败")
print()
print("建议修复方案: 提取 markdown 代码块后再解析")
print("=" * 70)
