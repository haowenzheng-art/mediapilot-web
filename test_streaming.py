
"""
测试流式输出逻辑
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*60)
print("  测试流式输出逻辑")
print("="*60)
print()

# 模拟配置
config = {
    "provider": "openai",
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

# 测试OpenAI兼容API的流式输出
print("测试OpenAI兼容API流式输出...")
print()

try:
    from openai import OpenAI

    api_key = config["api_key"]
    base_url = config["base_url"]
    model = config["model"]

    client = OpenAI(api_key=api_key, base_url=base_url)

    prompt = "你好，请简单介绍一下自己，用3句话"

    print(f"Prompt: {prompt}")
    print()
    print("开始流式接收...")
    print("-" * 60)

    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.7,
        stream=True
    )

    full_response = ""
    for chunk in stream:
        if chunk.choices and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)
                full_response += delta.content

    print()
    print("-" * 60)
    print()
    print("✓ 流式输出成功!")
    print(f"完整回复: {full_response[:100]}...")
    print()

except ImportError:
    print("✗ openai库未安装")
except Exception as e:
    print(f"✗ 发生错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
print("测试完成!")
print("="*60)
print()

try:
    input("按回车键退出...")
except:
    pass

