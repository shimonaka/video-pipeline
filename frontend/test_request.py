
import requests
import json
import time

url = "http://localhost:8000/api/generate"

data = {
    "script": "テスト\n\nテスト2",
    "engine": "voicevox",
    "speaker": "3",
    "voice": "Kore",
    "slideOrder": ""
}

print(f"POST {url}")
try:
    response = requests.post(url, data=data, timeout=600)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
