"""
リップシンク生成スクリプト - Rhubarb Lip Syncのラッパー

使用方法:
  # 単一音声ファイルからリップシンク生成
  python generate_lipsync.py input.wav -o output.json

  # パイプラインデータディレクトリの全音声を処理
  python generate_lipsync.py --batch audio_dir/ -o lipsync_dir/

必要なツール:
  Rhubarb Lip Sync (https://github.com/DanielSWolf/rhubarb-lip-sync/releases)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


# Rhubarbのパス設定
# 環境変数 RHUBARB_PATH が設定されていればそれを使用
# なければ一般的なインストールパスを試行
RHUBARB_PATHS = [
    os.environ.get("RHUBARB_PATH", ""),
    "rhubarb",  # PATHに追加されている場合
    r"C:\tools\rhubarb\rhubarb.exe",
    r"C:\development\tools\rhubarb\rhubarb.exe",
    r"C:\Program Files\rhubarb\rhubarb.exe",
]


def find_rhubarb() -> Optional[str]:
    """Rhubarbの実行ファイルを探す"""
    # その都度環境変数をチェックするためにリストを再構築
    current_paths = [os.environ.get("RHUBARB_PATH", "")] + RHUBARB_PATHS
    
    for path in current_paths:
        if not path:
            continue
        
        # フルパスの場合
        if os.path.isfile(path):
            return path
        
        # PATHから検索
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return path
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
    
    return None


def check_rhubarb():
    """Rhubarbが利用可能かチェック"""
    rhubarb = find_rhubarb()
    if rhubarb is None:
        error_msg = "Rhubarb Lip Sync が見つかりません。環境変数 RHUBARB_PATH を設定してください。"
        print("=" * 60)
        print(f"エラー: {error_msg}")
        print("=" * 60)
        raise RuntimeError(error_msg)
    
    return rhubarb


def generate_lipsync(
    audio_path: str,
    output_path: Optional[str] = None,
    rhubarb_path: Optional[str] = None
) -> dict:
    """
    音声ファイルからリップシンクJSONを生成
    
    Args:
        audio_path: 入力音声ファイル（.wav）
        output_path: 出力JSONパス（Noneの場合は音声と同名）
        rhubarb_path: Rhubarb実行ファイルのパス
    
    Returns:
        生成されたリップシンクデータ
    """
    if rhubarb_path is None:
        rhubarb_path = check_rhubarb()
    
    audio_file = Path(audio_path)
    if not audio_file.exists():
        print(f"エラー: 音声ファイルが見つかりません: {audio_path}")
        sys.exit(1)
    
    # 出力パス決定
    if output_path is None:
        output_path = str(audio_file.with_suffix(".json"))
    
    print(f"🎤 リップシンク生成中: {audio_file.name}")
    
    # Rhubarb実行
    # --recognizer phonetic: 日本語対応（言語非依存の音声解析）
    # -f json: JSON形式で出力
    cmd = [
        rhubarb_path,
        "--recognizer", "phonetic",
        "-f", "json",
        "-o", output_path,
        str(audio_path)
    ]
    
    print(f"DEBUG: Rhubarb command: {cmd}")
    print(f"DEBUG: Rhubarb path exists: {os.path.exists(cmd[0])}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2分タイムアウト
        )
        
        if result.returncode != 0:
            print(f"エラー: Rhubarb実行失敗")
            print(f"stderr: {result.stderr}")
            raise RuntimeError(f"Rhubarb実行失敗: {result.stderr}")
        
    except subprocess.TimeoutExpired:
        print("エラー: リップシンク生成がタイムアウトしました")
        raise RuntimeError("リップシンク生成がタイムアウトしました")
    except Exception as e:
        print(f"エラー: Rhubarb実行中に問題が発生: {e}")
        raise RuntimeError(f"Rhubarb実行中に問題が発生: {e}")
    
    # 結果読み込み
    with open(output_path, "r", encoding="utf-8") as f:
        lipsync_data = json.load(f)
    
    # 統計表示
    cues = lipsync_data.get("mouthCues", [])
    duration = lipsync_data.get("metadata", {}).get("duration", 0)
    print(f"✅ 完了: {len(cues)} キュー, {duration:.1f}秒")
    print(f"   出力: {output_path}")
    
    return lipsync_data


def batch_generate(
    audio_dir: str,
    output_dir: Optional[str] = None,
    rhubarb_path: Optional[str] = None
) -> list:
    """
    ディレクトリ内の全音声ファイルを処理
    
    Args:
        audio_dir: 音声ファイルがあるディレクトリ
        output_dir: 出力ディレクトリ（Noneの場合は音声と同じ場所）
        rhubarb_path: Rhubarb実行ファイルのパス
    
    Returns:
        生成されたリップシンクデータのリスト
    """
    if rhubarb_path is None:
        rhubarb_path = check_rhubarb()
    
    audio_path = Path(audio_dir)
    if not audio_path.is_dir():
        print(f"エラー: ディレクトリが見つかりません: {audio_dir}")
        sys.exit(1)
    
    # 出力ディレクトリ
    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
    else:
        out_path = audio_path
    
    # WAVファイルを検索
    wav_files = sorted(audio_path.glob("*.wav"))
    if not wav_files:
        print(f"警告: WAVファイルが見つかりません: {audio_dir}")
        return []
    
    print(f"📂 {len(wav_files)} 個の音声ファイルを処理します")
    print()
    
    results = []
    for wav_file in wav_files:
        output_file = out_path / wav_file.with_suffix(".json").name
        data = generate_lipsync(str(wav_file), str(output_file), rhubarb_path)
        results.append({
            "audio": wav_file.name,
            "lipsync": output_file.name,
            "data": data
        })
        print()
    
    print(f"✅ 全{len(results)}ファイルの処理が完了しました")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="リップシンク生成 - Rhubarb Lip Sync ラッパー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 単一ファイル
  python generate_lipsync.py audio.wav -o lipsync.json

  # バッチ処理
  python generate_lipsync.py --batch audio_dir/ -o lipsync_dir/

  # Rhubarbの場所を指定
  python generate_lipsync.py audio.wav --rhubarb C:\\tools\\rhubarb\\rhubarb.exe
        """
    )
    
    parser.add_argument("input", help="入力音声ファイル または ディレクトリ（--batch時）")
    parser.add_argument("-o", "--output", help="出力ファイル または ディレクトリ")
    parser.add_argument("--batch", action="store_true", help="ディレクトリ内の全WAVを処理")
    parser.add_argument("--rhubarb", help="Rhubarb実行ファイルのパス")
    
    args = parser.parse_args()
    
    if args.batch:
        batch_generate(args.input, args.output, args.rhubarb)
    else:
        generate_lipsync(args.input, args.output, args.rhubarb)


if __name__ == "__main__":
    main()
