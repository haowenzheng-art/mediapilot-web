import httpx
import json

response = httpx.post(
    'http://localhost:8000/api/v1/video/fetch',
    json={
        'video_url': 'https://www.bilibili.com/video/BV1B6421F7on',
        'platform': 'bilibili'
    },
    timeout=60
)

result = response.json()
print('Thumbnail URL:', result['data']['thumbnail_url'])
print('Title:', result['data']['title'])