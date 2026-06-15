#!/usr/bin/env python3

# 测试 trending search API
import requests

# 测试 trending search API
url = 'http://127.0.0.1:8000/api/v1/trending/search'
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJ0ZXN0dXNlciIsImV4cCI6MTc3NTE4jY4Mn0.KPnd722InKgDsX4VhwaZNCkQs5wTesjhfJVq3eS20Pg'
headers = {'Authorization': f'Bearer {token}'}
data = {
    'keyword': 'AI',
    'platforms': ['douyin', 'weibo'],
    'days': 7
}

print('Request URL:', url)
print('Headers:', headers)
print('Request Data:', data)

try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    result = response.json()
    print('Response Status:', result.get('detail', {}).get('message', 'N/A'))
    print('Response Data:', result.get('data', 'N/A').keys())
except requests.exceptions.Timeout:
    print('Timeout')
except Exception as e:
    print('Error:', e)
    print('Error Type:', type(e))