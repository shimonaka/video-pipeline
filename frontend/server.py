"""
ビデオパイプライン フロントエンドサーバー

使用方法:
  python server.py
  → http://localhost:8000 でアクセス
"""

import atexit
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

# パイプラインスクリプトのパスを追加
SCRIPT_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import run_pipeline

# 作業ディレクトリ
WORK_DIR = Path(__file__).parent / "work"
UPLOADS_DIR = WORK_DIR / "uploads"
OUTPUT_DIR = WORK_DIR / "output"

# VOICEVOX Engine
VOICEVOX_ENGINE_DIR = Path(__file__).parent.parent / "tools" / "voicevox_engine"
VOICEVOX_ENGINE_EXE = VOICEVOX_ENGINE_DIR / "run.exe"
VOICEVOX_URL = "http://localhost:50021"

# グローバル変数でVOICEVOXプロセスを管理
voicevox_process = None

def is_voicevox_running() -> bool:
    """VOICEVOXが起動しているかチェック"""
    try:
        req = urllib.request.Request(f"{VOICEVOX_URL}/version", method="GET")
        with urllib.request.urlopen(req, timeout=2) as res:
            return res.status == 200
    except:
        return False

def start_voicevox_engine() -> bool:
    """VOICEVOX Engineを起動"""
    global voicevox_process
    
    if not VOICEVOX_ENGINE_EXE.exists():
        print(f"⚠️  VOICEVOX Engine が見つかりません: {VOICEVOX_ENGINE_EXE}")
        return False
    
    if is_voicevox_running():
        print("✅ VOICEVOX Engine は既に起動しています")
        return True
    
    print("🚀 VOICEVOX Engine を起動中...", flush=True)
    
    try:
        # バックグラウンドで起動
        voicevox_process = subprocess.Popen(
            [str(VOICEVOX_ENGINE_EXE), "--host", "127.0.0.1", "--port", "50021"],
            cwd=str(VOICEVOX_ENGINE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        # 起動を待機（最大30秒）
        for i in range(30):
            time.sleep(1)
            if is_voicevox_running():
                print("✅ VOICEVOX Engine 起動完了", flush=True)
                return True
            print(f"   起動待機中... ({i+1}/30)", flush=True)
        
        print("❌ VOICEVOX Engine 起動タイムアウト")
        return False
        
    except Exception as e:
        print(f"❌ VOICEVOX Engine 起動エラー: {e}")
        return False

def stop_voicevox_engine():
    """VOICEVOX Engineを停止"""
    global voicevox_process
    
    if voicevox_process:
        print("🛑 VOICEVOX Engine を停止中...")
        try:
            voicevox_process.terminate()
            voicevox_process.wait(timeout=5)
        except:
            voicevox_process.kill()
        voicevox_process = None
        print("✅ VOICEVOX Engine 停止完了")

# 終了時にVOICEVOXを停止
atexit.register(stop_voicevox_engine)

# ディレクトリ作成
WORK_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="ビデオパイプライン")

# 静的ファイル
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")


def parse_script_text(text: str) -> dict:
    """
    テキスト台本をJSON形式に変換
    
    ルール:
    - 空行で区切る → 別シーン
    - `---` → スライド切り替え
    - 連続する行 → 同じシーンのテキスト
    """
    lines = text.strip().split('\n')
    scenes = []
    current_scene_lines = []
    current_slide_index = 0  # 現在のスライドインデックス
    scene_count = 0
    
    for line in lines:
        stripped = line.strip()
        
        # スライド切り替えマーカー
        if stripped == '---':
            # 現在のシーンを確定
            if current_scene_lines:
                scene_count += 1
                scenes.append({
                    "id": f"scene_{scene_count:03d}",
                    "speaker": "narrator",
                    "text": ' '.join(current_scene_lines),
                    "slideIndex": current_slide_index
                })
                current_scene_lines = []
            # 次のスライドへ
            current_slide_index += 1
            continue
        
        # 空行 → シーン区切り
        if not stripped:
            if current_scene_lines:
                scene_count += 1
                scenes.append({
                    "id": f"scene_{scene_count:03d}",
                    "speaker": "narrator",
                    "text": ' '.join(current_scene_lines),
                    "slideIndex": current_slide_index
                })
                current_scene_lines = []
            continue
        
        # テキスト行
        current_scene_lines.append(stripped)
    
    # 最後のシーン
    if current_scene_lines:
        scene_count += 1
        scenes.append({
            "id": f"scene_{scene_count:03d}",
            "speaker": "narrator",
            "text": ' '.join(current_scene_lines),
            "slideIndex": current_slide_index
        })
    
    return {
        "title": "生成動画",
        "version": "1.0",
        "speakers": {
            "narrator": {"name": "ナレーター", "voice": "Kore"}
        },
        "scenes": scenes,
        "video": {
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "background": "lightBlue"
        }
    }


@app.get("/", response_class=HTMLResponse)
async def root():
    """メインページ"""
    html_path = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.post("/api/parse-script")
async def parse_script(script: str = Form(...)):
    """台本テキストをJSONに変換（プレビュー用）"""
    try:
        script_json = parse_script_text(script)
        return {"success": True, "script": script_json}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/generate")
async def generate_video(
    script: str = Form(...),
    engine: str = Form("voicevox"),
    speaker: str = Form("3"),  # VOICEVOX speaker ID
    voice: str = Form("Kore"),  # Gemini voice
    slides: List[UploadFile] = File(default=[]),
    slideOrder: str = Form(default="")  # カンマ区切りの順番
):
    """動画を生成"""
    job_id = str(uuid.uuid4())[:8]
    job_dir = OUTPUT_DIR / job_id
    job_dir.mkdir(exist_ok=True)
    
    try:
        # 1. 台本をパース
        script_json = parse_script_text(script)
        script_json["speakers"]["narrator"]["voice"] = voice
        script_json["speakers"]["narrator"]["voice"] = voice
        
        # キャラクター表示設定 & VOICEVOX ID設定
        if speaker == "none":
            if "video" not in script_json:
                script_json["video"] = {}
            script_json["video"]["characterVisible"] = False
            # 音声生成のためにデフォルトIDを使用（ずんだもん=3）
            script_json["speakers"]["narrator"]["voicevox_id"] = 3
        elif speaker == "custom-rin":
            if "video" not in script_json:
                script_json["video"] = {}
            script_json["video"]["characterVisible"] = True
            
            # カスタムキャラクター設定
            # Remotion側でのパス（publicからの相対パス）
            # script_json["video"]["characterBase"] = "character/rin.png" # ベース画像を指定すると口パク画像と重なってスタンド化するため無効化
            script_json["video"]["characterMouthDir"] = "character"
            
            # デフォルト音声（女性音声）
            script_json["speakers"]["narrator"]["voicevox_id"] = 8  # 春日部つむぎ
            
            # アセットのコピー（video-pipeline/character -> remotion-project/public/character）
            # キャラクター定義ディレクトリ
            char_src_dir = Path(__file__).parent.parent / "character"
            remotion_char_dir = SCRIPT_DIR.parent / "remotion-project" / "public" / "character"
            
            # ディレクトリ作成
            remotion_char_dir.mkdir(parents=True, exist_ok=True)
            
            # rin.pngをコピー
            rin_src = char_src_dir / "rin.png"
            if rin_src.exists():
                shutil.copy(rin_src, remotion_char_dir / "rin.png")
            else:
                print(f"Warning: {rin_src} not found")
                
            # 口の画像をコピー (A-F)
            for mouth in ["A", "B", "C", "D", "E", "F"]:
                mouth_file = f"mouth-{mouth}.png"
                mouth_src = char_src_dir / mouth_file
                if mouth_src.exists():
                    shutil.copy(mouth_src, remotion_char_dir / mouth_file)
        else:
            if "video" not in script_json:
                script_json["video"] = {}
            script_json["video"]["characterVisible"] = True
            script_json["speakers"]["narrator"]["voicevox_id"] = int(speaker)
        
        # 2. スライド画像を保存（順番を適用）
        slide_paths = []
        
        # 順番を復元
        if slideOrder:
            order_list = slideOrder.split(",")
            ordered_slides = []
            for idx in order_list:
                try:
                    i = int(idx)
                    if 0 <= i < len(slides):
                        ordered_slides.append(slides[i])
                except ValueError:
                    pass
            slides = ordered_slides
        
        for i, slide in enumerate(slides):
            if slide.filename:
                ext = Path(slide.filename).suffix or ".png"
                slide_path = job_dir / f"slide_{i:02d}{ext}"
                with open(slide_path, "wb") as f:
                    content = await slide.read()
                    f.write(content)
                slide_paths.append(f"slides/slide_{i:02d}{ext}")
        
        # 3. シーンにスライドパスを設定
        for scene in script_json["scenes"]:
            slide_idx = scene.get("slideIndex", 0)
            if slide_idx < len(slide_paths):
                scene["background"] = slide_paths[slide_idx]
        
        # 4. 台本を保存
        script_path = job_dir / "script.json"
        with open(script_path, "w", encoding="utf-8") as f:
            json.dump(script_json, f, ensure_ascii=False, indent=2)
        
        # 5. パイプライン実行（関数直接呼び出し）
        # 環境変数設定
        os.environ["PYTHONIOENCODING"] = "utf-8"
        rhubarb_path = SCRIPT_DIR.parent / "tools" / "rhubarb" / "rhubarb.exe"
        if rhubarb_path.exists():
            os.environ["RHUBARB_PATH"] = str(rhubarb_path)
            
        print(f"DEBUG: Running pipeline directly. Engine={engine}")
        
        try:
            # run_full_pipelineを実行
            run_pipeline.run_full_pipeline(
                str(script_path),
                str(job_dir),
                video_output=None,
                skip_render=True,
                tts_engine=engine
            )
            success = True
        except Exception as e:
            import traceback
            error_msg = f"パイプライン実行エラー: {str(e)}\n{traceback.format_exc()}"
            print(f"ERROR: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        
        # 6. Remotionにデータをコピー
        remotion_public = SCRIPT_DIR.parent / "remotion-project" / "public"
        
        # スライドをコピー
        slides_dir = remotion_public / "slides"
        if slides_dir.exists():
            shutil.rmtree(slides_dir)
        slides_dir.mkdir(exist_ok=True)
        
        for slide_file in job_dir.glob("slide_*"):
            shutil.copy(slide_file, slides_dir / slide_file.name)
        
        # audio, lipsync, pipeline-dataをコピー
        for subdir in ["audio", "lipsync"]:
            src = job_dir / subdir
            dst = remotion_public / subdir
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
        
        shutil.copy(job_dir / "pipeline-data.json", remotion_public / "pipeline-data.json")
        
        # 7. Remotionレンダリング
        remotion_dir = SCRIPT_DIR.parent / "remotion-project"
        video_output = job_dir / "video.mp4"
        
        npx_cmd = "npx"
        if os.name == "nt":
            npx_cmd = "npx.cmd"
            
        print(f"DEBUG: Rendering with {npx_cmd}")
        
        result = subprocess.run(
            [
                npx_cmd, "remotion", "render",
                "src/index.ts",
                "MultiSceneVideo",
                str(video_output)
            ],
            cwd=str(remotion_dir),
            capture_output=True,
            text=True,
            timeout=600,
            shell=True 
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"レンダリングエラー: {result.stderr[:500]}"
            }
        
        return {
            "success": True,
            "videoUrl": f"/output/{job_id}/video.mp4",
            "jobId": job_id,
            "scenes": len(script_json["scenes"])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/voices")
async def get_voices():
    """利用可能なボイス一覧"""
    return {
        "voices": [
            {"id": "Kore", "name": "Kore（日本語推奨）"},
            {"id": "Aoede", "name": "Aoede"},
            {"id": "Charon", "name": "Charon"},
            {"id": "Fenrir", "name": "Fenrir"},
            {"id": "Puck", "name": "Puck"},
            {"id": "Zephyr", "name": "Zephyr"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("ビデオパイプライン サーバー")
    print("=" * 50)
    print()
    
    # VOICEVOX Engine 起動
    if VOICEVOX_ENGINE_EXE.exists():
        start_voicevox_engine()
    else:
        print("⚠️  VOICEVOX Engine が見つかりません")
        print(f"   パス: {VOICEVOX_ENGINE_EXE}")
        print("   Geminiエンジンを使用してください")
    
    print()
    print("🌐 http://localhost:8000 でアクセス")
    print()
    print("Ctrl+C で終了")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
