"""
データ統合スクリプト - 音声とリップシンクをRemotion用に統合

使用方法:
  # 台本JSONと生成済みアセットからpipeline-data.jsonを生成
  python integrate_data.py script.json audio_dir/ lipsync_dir/ -o pipeline-data.json
"""

import argparse
import json
import os
import wave
from pathlib import Path
from typing import Optional



# 動画設定のデフォルト値
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
DEFAULT_FPS = 30


def get_audio_duration(audio_path: str) -> float:
    """WAVファイルの長さ（秒）を取得"""
    with wave.open(audio_path, "rb") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        return frames / rate


def integrate_pipeline_data(
    script_path: str,
    audio_dir: str,
    lipsync_dir: str,
    output_path: Optional[str] = None,
    fps: int = DEFAULT_FPS
) -> dict:
    """
    台本と生成済みアセットを統合してpipeline-data.jsonを生成
    
    Args:
        script_path: 台本JSONのパス
        audio_dir: 音声ファイルディレクトリ
        lipsync_dir: リップシンクJSONディレクトリ
        output_path: 出力パス
        fps: フレームレート
    
    Returns:
        生成されたパイプラインデータ
    """
    # 台本読み込み
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)
    
    audio_path = Path(audio_dir)
    lipsync_path = Path(lipsync_dir)
    
    # シーン配列の取得
    scenes = script.get("scenes", script.get("dialogue", []))
    speakers = script.get("speakers", {})
    
    # 動画設定
    video_config = script.get("video", {})
    width = video_config.get("width", DEFAULT_WIDTH)
    height = video_config.get("height", DEFAULT_HEIGHT)
    
    # パイプラインデータ構築
    pipeline_data = {
        "title": script.get("title", "Untitled"),
        "version": "1.0",
        "videoConfig": {
            "width": width,
            "height": height,
            "fps": fps,
            "background": video_config.get("background", "lightBlue"),
            "characterVisible": video_config.get("characterVisible", True)
        },
        "scenes": []
    }
    
    current_frame = 0
    
    for i, scene in enumerate(scenes, start=1):
        scene_id = scene.get("id", f"scene_{i:03d}")
        speaker_id = scene.get("speaker", "narrator")
        text = scene.get("text", "")
        
        # 音声ファイル
        audio_filename = f"{i:02d}_{speaker_id}.wav"
        audio_file = audio_path / audio_filename
        
        if not audio_file.exists():
            print(f"警告: 音声ファイルが見つかりません: {audio_filename}")
            continue
        
        # リップシンクファイル
        lipsync_filename = f"{i:02d}_{speaker_id}.json"
        lipsync_file = lipsync_path / lipsync_filename
        
        if not lipsync_file.exists():
            print(f"警告: リップシンクファイルが見つかりません: {lipsync_filename}")
            continue
        
        # 音声の長さを取得
        duration_seconds = get_audio_duration(str(audio_file))
        duration_frames = int(duration_seconds * fps)
        
        # シーンデータ構築
        scene_data = {
            "sceneId": scene_id,
            "speaker": speaker_id,
            "text": text,
            "audio": {
                "file": f"audio/{audio_filename}",
                "duration": duration_seconds,
                "startFrame": current_frame,
                "endFrame": current_frame + duration_frames
            },
            "lipsync": {
                "file": f"lipsync/{lipsync_filename}"
            }
        }
        
        # 背景指定があれば追加
        if "background" in scene:
            scene_data["background"] = scene["background"]
        
        pipeline_data["scenes"].append(scene_data)
        current_frame += duration_frames
        
        print(f"✅ シーン {i}: {duration_seconds:.1f}秒 ({duration_frames}フレーム)")
    
    # 合計フレーム数
    pipeline_data["totalFrames"] = current_frame
    total_seconds = current_frame / fps
    
    print()
    print(f"📊 合計: {len(pipeline_data['scenes'])}シーン, {total_seconds:.1f}秒 ({current_frame}フレーム)")
    
    # 保存
    if output_path is None:
        output_path = "pipeline-data.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pipeline_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 保存: {output_path}")
    
    return pipeline_data


def main():
    parser = argparse.ArgumentParser(
        description="パイプラインデータ統合 - Remotion用データ生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python integrate_data.py script.json audio/ lipsync/ -o pipeline-data.json
        """
    )
    
    parser.add_argument("script", help="台本JSONファイル")
    parser.add_argument("audio_dir", help="音声ファイルディレクトリ")
    parser.add_argument("lipsync_dir", help="リップシンクJSONディレクトリ")
    parser.add_argument("-o", "--output", help="出力ファイルパス")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS, help="フレームレート")
    
    args = parser.parse_args()
    
    integrate_pipeline_data(
        args.script,
        args.audio_dir,
        args.lipsync_dir,
        args.output,
        args.fps
    )


if __name__ == "__main__":
    main()
