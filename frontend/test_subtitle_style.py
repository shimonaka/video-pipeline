
import requests
import json
import time

def test_subtitle_style():
    url = "http://localhost:8000/api/generate"
    
    # 強調表示を含む台本
    data = {
        "script": "これは*テスト*です。\n\nテロップの*デザイン*が変わりました。",
        "engine": "voicevox",
        "speaker": "3", # ずんだもん (Green)
        "voice": "Kore"
    }
    
    print("Testing with highlighted script...")
    try:
        response = requests.post(url, data=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                job_id = result.get("jobId")
                print(f"Job ID: {job_id}")
                print(f"Video URL: {result.get('videoUrl')}")
                print("✅ API Request Successful")
            else:
                print(f"❌ API Error: {result.get('error')}")
        else:
            print(f"❌ Server Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running?")

if __name__ == "__main__":
    test_subtitle_style()
