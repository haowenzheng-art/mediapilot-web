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

print('=== 视频信息获取结果 ===')
print(json.dumps(response.json(), ensure_ascii=False, indent=2))