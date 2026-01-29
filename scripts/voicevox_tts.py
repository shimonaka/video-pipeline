"""
VOICEVOX TTS - VOICEVOXで音声を生成するスクリプト

使用方法:
  # VOICEVOXを起動した状態で実行
  python voicevox_tts.py text "こんにちは" -o output.wav
  python voicevox_tts.py dialogue script.json -o output_dir/ --combine

VOICEVOXのダウンロード:
  https://voicevox.hiroshiba.jp/

特徴:
  - 完全無料
  - APIキー不要
  - レート制限なし
  - 高品質な日本語音声
"""

import argparse
import json
import os
import struct
import sys
import wave
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, List

# VOICEVOXのデフォルトエンドポイント
VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://localhost:50021")

# デフォルトスピーカーID（ずんだもん: 3、四国めたん: 2、春日部つむぎ: 8）
DEFAULT_SPEAKER = 3  # ずんだもん（ノーマル）

# 利用可能なスピーカー一覧
SPEAKERS = {
    "zundamon": 3,       # ずんだもん
    "metan": 2,          # 四国めたん
    "tsumugi": 8,        # 春日部つむぎ
    "ritsu": 9,          # 九州そら
    "himari": 14,        # もち子さん
    "takehiro": 20,      # 冥鳴ひまり
}


def check_voicevox() -> bool:
    """VOICEVOXが起動しているかチェック"""
    try:
        req = urllib.request.Request(f"{VOICEVOX_URL}/version")
        with urllib.request.urlopen(req, timeout=5) as res:
            version = res.read().decode('utf-8')
            print(f"✅ VOICEVOX 接続成功 (version: {version.strip()})")
            return True
    except Exception as e:
        print("=" * 60)
        print("エラー: VOICEVOXに接続できません")
        print("=" * 60)
        print()
        print("📥 VOICEVOXのダウンロード:")
        print("   https://voicevox.hiroshiba.jp/")
        print()
        print("🚀 起動方法:")
        print("   1. VOICEVOXアプリを起動")
        print("   2. 起動後、このスクリプトを再実行")
        print()
        print(f"   エンドポイント: {VOICEVOX_URL}")
        print("=" * 60)
        return False


def get_speakers() -> List[dict]:
    """利用可能なスピーカー一覧を取得"""
    try:
        req = urllib.request.Request(f"{VOICEVOX_URL}/speakers")
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        print(f"警告: スピーカー一覧の取得に失敗: {e}")
        return []


def generate_audio(
    text: str,
    speaker: int = DEFAULT_SPEAKER,
    output_path: Optional[str] = None
) -> bytes:
    """
    VOICEVOXで音声を生成
    
    Args:
        text: 読み上げるテキスト
        speaker: スピーカーID
        output_path: 出力ファイルパス
    
    Returns:
        WAV音声データ
    """
    # 1. 音声合成クエリを生成
    params = urllib.parse.urlencode({"text": text, "speaker": speaker})
    query_url = f"{VOICEVOX_URL}/audio_query?{params}"
    
    req = urllib.request.Request(query_url, method="POST")
    with urllib.request.urlopen(req, timeout=30) as res:
        query = json.loads(res.read().decode('utf-8'))
    
    # 2. 音声合成を実行
    synthesis_url = f"{VOICEVOX_URL}/synthesis?speaker={speaker}"
    req = urllib.request.Request(
        synthesis_url,
        data=json.dumps(query).encode('utf-8'),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    with urllib.request.urlopen(req, timeout=60) as res:
        audio_data = res.read()
    
    # 保存
    if output_path:
        with open(output_path, "wb") as f:
            f.write(audio_data)
        print(f"✅ 保存: {output_path}")
    
    return audio_data


def generate_single_audio(
    text: str,
    speaker: int = DEFAULT_SPEAKER,
    output_path: Optional[str] = None
) -> bytes:
    """単一テキストから音声生成（gemini_ttsとの互換性）"""
    print(f"🎙 生成中: {text[:30]}...")
    return generate_audio(text, speaker, output_path)


def generate_dialogue(
    script_path: str,
    output_dir: str,
    combine: bool = False,
    default_speaker: int = DEFAULT_SPEAKER
) -> List[str]:
    """
    台本JSONから音声を一括生成
    
    Args:
        script_path: 台本JSONファイルパス
        output_dir: 出力ディレクトリ
        combine: 音声を結合するか
        default_speaker: デフォルトスピーカーID
    
    Returns:
        生成されたファイルパスのリスト
    """
    # 台本読み込み
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # シーン配列を取得
    scenes = script.get("scenes", script.get("dialogue", []))
    speakers_config = script.get("speakers", {})
    
    print(f"📝 {len(scenes)} シーンの音声を生成します")
    print()
    
    generated_files = []
    
    for i, scene in enumerate(scenes, start=1):
        text = scene.get("text", "")
        speaker_id = scene.get("speaker", "narrator")
        
        # スピーカー設定からVOICEVOX IDを取得
        speaker_config = speakers_config.get(speaker_id, {})
        voicevox_id = speaker_config.get("voicevox_id", default_speaker)
        
        # 出力ファイル名
        filename = f"{i:02d}_{speaker_id}.wav"
        output_file = output_path / filename
        
        print(f"🎙 シーン {i}: {text[:30]}...")
        
        try:
            generate_audio(text, voicevox_id, str(output_file))
            generated_files.append(str(output_file))
        except Exception as e:
            print(f"❌ エラー: {e}")
            continue
    
    print()
    print(f"✅ {len(generated_files)} ファイルを生成しました")
    
    # 結合
    if combine and generated_files:
        combined_path = output_path / "combined.wav"
        combine_wav_files(generated_files, str(combined_path))
    
    return generated_files


def combine_wav_files(input_files: List[str], output_path: str):
    """WAVファイルを結合"""
    if not input_files:
        return
    
    # 最初のファイルからパラメータを取得
    with wave.open(input_files[0], "rb") as first:
        params = first.getparams()
    
    with wave.open(output_path, "wb") as output:
        output.setparams(params)
        
        for filepath in input_files:
            with wave.open(filepath, "rb") as f:
                output.writeframes(f.readframes(f.getnframes()))
    
    print(f"✅ 結合完了: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="VOICEVOX TTS - ローカル音声合成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 単一テキスト
  python voicevox_tts.py text "こんにちは" -o output.wav

  # 台本から一括生成
  python voicevox_tts.py dialogue script.json -o output/

  # スピーカー指定
  python voicevox_tts.py text "こんにちは" -o output.wav --speaker 2

スピーカーID:
  2: 四国めたん
  3: ずんだもん（デフォルト）
  8: 春日部つむぎ
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # text コマンド
    text_parser = subparsers.add_parser("text", help="単一テキストから音声生成")
    text_parser.add_argument("text", help="読み上げるテキスト")
    text_parser.add_argument("-o", "--output", default="output.wav", help="出力ファイル")
    text_parser.add_argument("--speaker", type=int, default=DEFAULT_SPEAKER, help="スピーカーID")
    
    # dialogue コマンド
    dialogue_parser = subparsers.add_parser("dialogue", help="台本から一括生成")
    dialogue_parser.add_argument("script", help="台本JSONファイル")
    dialogue_parser.add_argument("-o", "--output", default="./output", help="出力ディレクトリ")
    dialogue_parser.add_argument("--combine", action="store_true", help="音声を結合")
    dialogue_parser.add_argument("--speaker", type=int, default=DEFAULT_SPEAKER, help="デフォルトスピーカーID")
    
    # speakers コマンド
    speakers_parser = subparsers.add_parser("speakers", help="利用可能なスピーカー一覧")
    
    args = parser.parse_args()
    
    # VOICEVOXチェック
    if not check_voicevox():
        sys.exit(1)
    
    if args.command == "text":
        generate_single_audio(args.text, args.speaker, args.output)
    
    elif args.command == "dialogue":
        generate_dialogue(args.script, args.output, args.combine, args.speaker)
    
    elif args.command == "speakers":
        speakers = get_speakers()
        for speaker in speakers:
            print(f"\n{speaker['name']}:")
            for style in speaker.get("styles", []):
                print(f"  ID {style['id']}: {style['name']}")


if __name__ == "__main__":
    main()
