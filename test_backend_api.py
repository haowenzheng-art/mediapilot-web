"""
测试后端API的完整脚本生成流程
"""
import json
import httpx

API_BASE_URL = "http://localhost:8000"

headers = {
    "Content-Type": "application/json"
}

data = {
    "topic": "AI工具测评",
    "platform": "xiaohongshu",
    "duration": 60,
    "style": "干货分享"
}

print("测试后端API脚本生成...")
print(f"URL: {API_BASE_URL}/api/v1/content/generate")
print(f"请求参数: {json.dumps(data, ensure_ascii=False, indent=2)}")
print("-" * 50)

try:
    response = httpx.post(
        f"{API_BASE_URL}/api/v1/content/generate",
        headers=headers,
        json=data,
        timeout=120  # 给足2分钟时间
    )

    print(f"状态码: {response.status_code}")
    print("-" * 50)

    if response.status_code == 200:
        result = response.json()
        print("响应内容:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 检查是否是mock数据
        if "script" in result.get("data", {}):
            script_data = result["data"]["script"]
            if len(script_data) <= 3 and "开场画面" in str(script_data):
                print("\n⚠️ 警告：这看起来像是mock数据！")
                print("原因：脚本只有3个场景，且包含'开场画面'等通用描述")
            else:
                print(f"\n✓ 这是真实的AI生成数据（{len(script_data)}个场景）")
        else:
            print("\n⚠️ 警告：响应中没有script字段")
    else:
        print(f"请求失败: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()