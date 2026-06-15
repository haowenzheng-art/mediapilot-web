import httpx
import json

response = httpx.post(
    'http://localhost:8000/api/v1/video/fetch',
    json={
        'video_url': 'https://www.bilibili.com/video/BV1xx411c7mD',
        'platform': 'bilibili'
    },
    timeout=60
)

result = response.json()
print('=== 后端返回的数据结构 ===')
print(json.dumps(result.get('data', {}), ensure_ascii=False, indent=2))