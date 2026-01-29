
import requests
import json
import time

def test_no_character():
    url = "http://localhost:8000/api/generate"
    
    # speaker="none" でリクエスト
    data = {
        "script": "これはテストです。\n\nキャラクターは表示されません。",
        "engine": "voicevox",
        "speaker": "none",
        "voice": "Kore"
    }
    
    print("Testing with speaker='none'...")
    try:
        response = requests.post(url, data=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                job_id = result.get("jobId")
                print(f"Job ID: {job_id}")
                
                # pipeline-data.json を確認
                pipeline_url = f"http://localhost:8000/output/{job_id}/pipeline-data.json"
                pipeline_res = requests.get(pipeline_url)
                
                if pipeline_res.status_code == 200:
                    pipeline_data = pipeline_res.json()
                    visible = pipeline_data["videoConfig"].get("characterVisible")
                    print(f"videoConfig.characterVisible: {visible}")
                    
                    if visible is False:
                        print("✅ Success: characterVisible is False")
                    else:
                        print(f"❌ Failure: characterVisible is {visible}")
                else:
                    print("❌ Failed to fetch pipeline-data.json")
            else:
                print(f"❌ API Error: {result.get('error')}")
        else:
            print(f"❌ Server Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Server not running?")

if __name__ == "__main__":
    test_no_character()
