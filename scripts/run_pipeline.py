"""
統合パイプラインスクリプト - 台本から動画を1コマンドで生成

使用方法:
  # フルパイプライン実行
  python run_pipeline.py full script.json -o output/

  # 個別ステップ
  python run_pipeline.py tts script.json -o output/      # 音声生成のみ
  python run_pipeline.py lipsync output/ -o output/      # リップシンクのみ
  python run_pipeline.py render output/ -o video.mp4    # レンダリングのみ
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


# 同じディレクトリのモジュールをインポート
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# TTSモジュールのインポート（遅延）
_gemini_available = False
_voicevox_available = False

try:
    from gemini_tts import generate_dialogue as gemini_generate, check_api_key
    _gemini_available = True
except ImportError:
    pass

try:
    from voicevox_tts import generate_dialogue as voicevox_generate, check_voicevox
    _voicevox_available = True
except ImportError:
    pass

try:
    from generate_lipsync import batch_generate, check_rhubarb
    from integrate_data import integrate_pipeline_data
except ImportError as e:
    print(f"Module import error: {e}")
    print("Ensure generate_lipsync.py, integrate_data.py are in the same directory")
    print("Ensure generate_lipsync.py, integrate_data.py are in the same directory")
    raise ImportError(e)


# Remotionプロジェクトのパス
REMOTION_PROJECT = SCRIPT_DIR.parent / "remotion-project"
REMOTION_PUBLIC = REMOTION_PROJECT / "public"


def run_tts(script_path: str, output_dir: str, engine: str = "auto") -> str:
    """
    Step 1: 音声生成
    
    Args:
        script_path: 台本ファイルパス
        output_dir: 出力ディレクトリ
        engine: TTSエンジン ("gemini", "voicevox", "auto")
    
    Returns:
        出力ディレクトリパス
    """
    # エンジン自動選択
    if engine == "auto":
        # VOICEVOXを優先（レート制限なし）
        if _voicevox_available:
            try:
                if check_voicevox():
                    engine = "voicevox"
                else:
                    engine = "gemini"
            except:
                engine = "gemini"
        elif _gemini_available:
            engine = "gemini"
        else:
            print("エラー: 利用可能なTTSエンジンがありません")
            raise RuntimeError("利用可能なTTSエンジンがありません")
    
    print("=" * 60)
    print(f"Step 1: 音声生成 ({engine.upper()})")
    print("=" * 60)
    print()
    
    output_path = Path(output_dir)
    audio_dir = output_path / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    if engine == "voicevox":
        if not _voicevox_available:
            print("エラー: VOICEVOXモジュールが見つかりません")
            raise RuntimeError("VOICEVOXモジュールが見つかりません")
        if not check_voicevox():
            raise RuntimeError("VOICEVOXが起動していません")
        voicevox_generate(script_path, str(audio_dir), combine=True)
    else:
        if not _gemini_available:
            print("エラー: Geminiモジュールが見つかりません")
            raise RuntimeError("Geminiモジュールが見つかりません")
        check_api_key()
        gemini_generate(script_path, str(audio_dir), combine=True)
    
    print()
    return str(audio_dir)


def run_lipsync(audio_dir: str, output_dir: str) -> str:
    """
    Step 2: リップシンク生成
    
    Returns:
        出力ディレクトリパス
    """
    print("=" * 60)
    print("Step 2: リップシンク生成 (Rhubarb)")
    print("=" * 60)
    print()
    
    # Rhubarbチェック
    check_rhubarb()
    
    output_path = Path(output_dir)
    lipsync_dir = output_path / "lipsync"
    lipsync_dir.mkdir(parents=True, exist_ok=True)
    
    # リップシンク生成
    batch_generate(audio_dir, str(lipsync_dir))
    
    print()
    return str(lipsync_dir)


def run_integrate(
    script_path: str,
    audio_dir: str,
    lipsync_dir: str,
    output_dir: str
) -> str:
    """
    Step 3: データ統合
    
    Returns:
        pipeline-data.jsonのパス
    """
    print("=" * 60)
    print("Step 3: データ統合")
    print("=" * 60)
    print()
    
    output_path = Path(output_dir)
    pipeline_json = output_path / "pipeline-data.json"
    
    integrate_pipeline_data(
        script_path,
        audio_dir,
        lipsync_dir,
        str(pipeline_json)
    )
    
    print()
    return str(pipeline_json)


def copy_assets_to_remotion(output_dir: str) -> bool:
    """
    Step 4a: アセットをRemotionのpublicディレクトリにコピー
    
    Returns:
        成功したかどうか
    """
    print("=" * 60)
    print("Step 4a: アセットをRemotionにコピー")
    print("=" * 60)
    print()
    
    output_path = Path(output_dir)
    
    if not REMOTION_PUBLIC.exists():
        print(f"警告: Remotion publicディレクトリが見つかりません: {REMOTION_PUBLIC}")
        print("Remotionプロジェクトのセットアップが必要です")
        return False
    
    # pipeline-data.jsonをコピー
    src_pipeline = output_path / "pipeline-data.json"
    if src_pipeline.exists():
        shutil.copy(src_pipeline, REMOTION_PUBLIC / "pipeline-data.json")
        print(f"✅ pipeline-data.json")
    
    # audioディレクトリをコピー
    src_audio = output_path / "audio"
    dst_audio = REMOTION_PUBLIC / "audio"
    if src_audio.exists():
        if dst_audio.exists():
            shutil.rmtree(dst_audio)
        shutil.copytree(src_audio, dst_audio)
        wav_count = len(list(dst_audio.glob("*.wav")))
        print(f"✅ audio/ ({wav_count}ファイル)")
    
    # lipsyncディレクトリをコピー
    src_lipsync = output_path / "lipsync"
    dst_lipsync = REMOTION_PUBLIC / "lipsync"
    if src_lipsync.exists():
        if dst_lipsync.exists():
            shutil.rmtree(dst_lipsync)
        shutil.copytree(src_lipsync, dst_lipsync)
        json_count = len(list(dst_lipsync.glob("*.json")))
        print(f"✅ lipsync/ ({json_count}ファイル)")
    
    print()
    return True


def run_render(output_dir: str, video_output: Optional[str] = None) -> str:
    """
    Step 4b: Remotionでレンダリング
    
    Returns:
        出力動画パス
    """
    print("=" * 60)
    print("Step 4b: Remotionレンダリング")
    print("=" * 60)
    print()
    
    if not REMOTION_PROJECT.exists():
        print("=" * 60)
        print("エラー: Remotionプロジェクトがセットアップされていません")
        print("=" * 60)
        print()
        print("📝 セットアップ方法:")
        print(f"  cd {REMOTION_PROJECT.parent}")
        print("  npx degit remotion-dev/template-helloworld remotion-project")
        print("  cd remotion-project")
        print("  npm install")
        print()
        print("その後、必要なコンポーネントを追加してください")
        print("=" * 60)
        return ""
    
    # アセットコピー
    output_path = Path(output_dir)
    if not copy_assets_to_remotion(output_dir):
        return ""
    
    # 出力パス決定
    if video_output is None:
        video_output = str(output_path / "output.mp4")
    
    print(f"🎬 レンダリング中: MultiSceneVideo")
    print(f"   出力先: {video_output}")
    print()
    
    # Remotionレンダリング実行
    cmd = [
        "npx", "remotion", "render",
        "src/index.ts",
        "MultiSceneVideo",
        video_output
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(REMOTION_PROJECT),
            capture_output=True,
            text=True,
            timeout=600  # 10分タイムアウト
        )
        
        if result.returncode != 0:
            print(f"エラー: Remotionレンダリング失敗")
            print(f"stderr: {result.stderr}")
            return ""
        
        print(result.stdout)
        print(f"✅ レンダリング完了: {video_output}")
        
    except subprocess.TimeoutExpired:
        print("エラー: レンダリングがタイムアウトしました")
        return ""
    except FileNotFoundError:
        print("エラー: npx が見つかりません。Node.jsがインストールされているか確認してください")
        return ""
    
    print()
    return video_output


def run_full_pipeline(
    script_path: str,
    output_dir: str,
    video_output: Optional[str] = None,
    skip_render: bool = False,
    tts_engine: str = "auto"
) -> str:
    """
    フルパイプライン実行
    
    Args:
        script_path: 台本JSONのパス
        output_dir: 出力ディレクトリ
        video_output: 動画出力パス
        skip_render: レンダリングをスキップ
        tts_engine: TTSエンジン ("gemini", "voicevox", "auto")
    
    Returns:
        出力動画パス（またはpipeline-data.jsonパス）
    """
    print("*" * 60)
    print("台本から動画を自動生成 - フルパイプライン")
    print("*" * 60)
    print()
    print(f"Script: {script_path}")
    print(f"Output: {output_dir}")
    print(f"TTS Engine: {tts_engine}")
    print()
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Step 1: 音声生成
    audio_dir = run_tts(script_path, output_dir, tts_engine)
    
    # Step 2: リップシンク生成
    lipsync_dir = run_lipsync(audio_dir, output_dir)
    
    # Step 3: データ統合
    pipeline_json = run_integrate(script_path, audio_dir, lipsync_dir, output_dir)
    
    # Step 4: レンダリング（オプション）
    if skip_render:
        print("=" * 60)
        print("レンダリングをスキップしました")
        print(f"pipeline-data.json: {pipeline_json}")
        print("=" * 60)
        return pipeline_json
    
    video_path = run_render(output_dir, video_output)
    
    if video_path:
        print("*" * 60)
        print("✅ パイプライン完了!")
        print(f"   動画: {video_path}")
        print("*" * 60)
    
    return video_path


def main():
    parser = argparse.ArgumentParser(
        description="統合パイプライン - 台本から動画を自動生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # フルパイプライン
  python run_pipeline.py full script.json -o output/

  # レンダリングなし（Remotionセットアップ前）
  python run_pipeline.py full script.json -o output/ --skip-render

  # 個別ステップ
  python run_pipeline.py tts script.json -o output/
  python run_pipeline.py lipsync output/audio/ -o output/
  python run_pipeline.py render output/ -o video.mp4
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # full コマンド
    full_parser = subparsers.add_parser("full", help="フルパイプライン実行")
    full_parser.add_argument("script", help="台本JSONファイル")
    full_parser.add_argument("-o", "--output", default="./output", help="出力ディレクトリ")
    full_parser.add_argument("--video", help="動画出力パス")
    full_parser.add_argument("--skip-render", action="store_true", help="レンダリングをスキップ")
    full_parser.add_argument("--engine", choices=["auto", "gemini", "voicevox"], default="auto", help="TTSエンジン")
    
    # tts コマンド
    tts_parser = subparsers.add_parser("tts", help="音声生成のみ")
    tts_parser.add_argument("script", help="台本JSONファイル")
    tts_parser.add_argument("-o", "--output", default="./output", help="出力ディレクトリ")
    tts_parser.add_argument("--engine", choices=["auto", "gemini", "voicevox"], default="auto", help="TTSエンジン")
    
    # lipsync コマンド
    lipsync_parser = subparsers.add_parser("lipsync", help="リップシンク生成のみ")
    lipsync_parser.add_argument("audio_dir", help="音声ディレクトリ")
    lipsync_parser.add_argument("-o", "--output", default="./output", help="出力ディレクトリ")
    
    # render コマンド
    render_parser = subparsers.add_parser("render", help="Remotionレンダリングのみ")
    render_parser.add_argument("pipeline_dir", help="パイプラインデータディレクトリ")
    render_parser.add_argument("-o", "--output", help="動画出力パス")
    
    args = parser.parse_args()
    
    if args.command == "full":
        run_full_pipeline(args.script, args.output, args.video, args.skip_render, args.engine)
    elif args.command == "tts":
        run_tts(args.script, args.output, args.engine)
    elif args.command == "lipsync":
        run_lipsync(args.audio_dir, args.output)
    elif args.command == "render":
        run_render(args.pipeline_dir, args.output)


if __name__ == "__main__":
    main()
