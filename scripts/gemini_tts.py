"""
Gemini TTS - 台本から音声を自動生成するスクリプト

使用方法:
  # 単一テキストから音声生成
  python gemini_tts.py text "こんにちは" -o output.wav

  # 台本JSONから一括生成
  python gemini_tts.py dialogue script.json -o output_dir/ --combine

  # 既存音声ファイルを結合
  python gemini_tts.py combine metadata.json -o combined.wav

必要なパッケージ:
  pip install google-genai
"""

import argparse
import json
import os
import struct
import sys
import wave
from pathlib import Path
from typing import Optional


# 利用可能なボイスプリセット
AVAILABLE_VOICES = [
    "Aoede", "Charon", "Fenrir", "Kore", "Puck",
    "Zephyr", "Orbit", "Nova", "Lyra", "Helios"
]

# デフォルト設定
DEFAULT_VOICE = "Kore"  # 日本語に適したボイス
DEFAULT_PAUSE_SAME = 0.3  # 同一話者間のポーズ（秒）
DEFAULT_PAUSE_DIFFERENT = 0.6  # 話者交代時のポーズ（秒）
SAMPLE_RATE = 24000  # Gemini TTSの出力サンプルレート


def check_api_key() -> str:
    """環境変数からAPIキーを取得"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("=" * 60)
        print("エラー: GOOGLE_API_KEY 環境変数が設定されていません")
        print("=" * 60)
        print()
        print("📝 APIキーの取得方法:")
        print("1. https://aistudio.google.com/ にアクセス")
        print("2. 左メニューの「Get API key」をクリック")
        print("3. 「Create API key」でAPIキーを発行")
        print()
        print("💻 環境変数の設定方法 (Windows):")
        print('   setx GOOGLE_API_KEY "your-api-key-here"')
        print("   ※設定後、ターミナル/エディタを再起動してください")
        print("=" * 60)
        sys.exit(1)
    return api_key


def generate_single_audio(
    text: str,
    voice: str = DEFAULT_VOICE,
    output_path: Optional[str] = None,
    style_instructions: Optional[str] = None,
    max_retries: int = 3
) -> bytes:
    """
    単一テキストから音声を生成
    
    Args:
        text: 読み上げるテキスト
        voice: ボイスプリセット名
        output_path: 出力ファイルパス（Noneの場合は保存しない）
        style_instructions: スタイル指示（例: "ゆっくり丁寧に読む"）
        max_retries: 最大リトライ回数
    
    Returns:
        生成された音声データ（RAW PCM）
    """
    import time
    
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("=" * 60)
        print("エラー: google-genai パッケージがインストールされていません")
        print("=" * 60)
        print()
        print("以下のコマンドでインストールしてください:")
        print("  pip install google-genai")
        print("=" * 60)
        sys.exit(1)
    
    api_key = check_api_key()
    client = genai.Client(api_key=api_key)
    
    # プロンプト構築
    prompt = f"Read aloud the following text in Japanese: {text}"
    if style_instructions:
        prompt = f"{style_instructions}. {prompt}"
    
    # リトライループ
    for attempt in range(max_retries):
        try:
            # 音声生成
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice
                            )
                        )
                    )
                )
            )
            
            # 音声データ取得
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            
            # ファイル保存
            if output_path:
                save_wav(audio_data, output_path)
                print(f"✅ 保存: {output_path}")
            
            return audio_data
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "RetryInfo" in error_msg:
                wait_time = 25 * (attempt + 1)  # 25, 50, 75秒
                print(f"⏳ レート制限。{wait_time}秒待機中... (リトライ {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"エラー: {e}")
                raise
    
    print("エラー: 最大リトライ回数を超えました")
    sys.exit(1)


def save_wav(audio_data: bytes, output_path: str):
    """RAW PCMデータをWAVファイルとして保存"""
    with wave.open(output_path, "wb") as wav_file:
        wav_file.setnchannels(1)  # モノラル
        wav_file.setsampwidth(2)  # 16bit
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(audio_data)


def create_silence(duration_seconds: float) -> bytes:
    """指定秒数の無音データを生成"""
    num_samples = int(SAMPLE_RATE * duration_seconds)
    return b'\x00\x00' * num_samples


def generate_dialogue(
    script_path: str,
    output_dir: str,
    combine: bool = False,
    pause_same: float = DEFAULT_PAUSE_SAME,
    pause_different: float = DEFAULT_PAUSE_DIFFERENT
) -> dict:
    """
    台本JSONから音声を一括生成
    
    Args:
        script_path: 台本JSONのパス
        output_dir: 出力ディレクトリ
        combine: 結合済みファイルも生成するか
        pause_same: 同一話者間のポーズ（秒）
        pause_different: 話者交代時のポーズ（秒）
    
    Returns:
        メタデータ（各ファイル情報）
    """
    # 台本読み込み
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)
    
    # 出力ディレクトリ作成
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # シーン配列の取得（dialogueとscenes両方に対応）
    scenes = script.get("scenes", script.get("dialogue", []))
    
    # 話者設定の取得
    speakers = script.get("speakers", {})
    default_voice = DEFAULT_VOICE
    
    metadata = {
        "title": script.get("title", "Untitled"),
        "files": [],
        "pause_same": pause_same,
        "pause_different": pause_different
    }
    
    prev_speaker = None
    
    for i, scene in enumerate(scenes, start=1):
        speaker_id = scene.get("speaker", "narrator")
        text = scene.get("text", "")
        
        # ボイス決定
        speaker_config = speakers.get(speaker_id, {})
        voice = speaker_config.get("voice", default_voice)
        
        # ファイル名
        filename = f"{i:02d}_{speaker_id}.wav"
        filepath = output_path / filename
        
        print(f"🎙 シーン {i}: {text[:30]}...")
        
        # 音声生成
        audio_data = generate_single_audio(text, voice, str(filepath))
        
        # メタデータ記録
        file_info = {
            "index": i,
            "filename": filename,
            "speaker": speaker_id,
            "voice": voice,
            "text": text,
            "duration": len(audio_data) / (SAMPLE_RATE * 2)  # 秒
        }
        metadata["files"].append(file_info)
        
        prev_speaker = speaker_id
    
    # メタデータ保存
    metadata_path = output_path / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"📋 メタデータ保存: {metadata_path}")
    
    # 結合
    if combine:
        combined_path = output_path / "combined.wav"
        combine_audio_files(str(metadata_path), str(combined_path))
    
    return metadata


def combine_audio_files(metadata_path: str, output_path: Optional[str] = None) -> str:
    """
    メタデータに基づいて音声ファイルを結合
    
    Args:
        metadata_path: metadata.jsonのパス
        output_path: 出力ファイルパス（Noneの場合は同ディレクトリにcombined.wav）
    
    Returns:
        出力ファイルパス
    """
    metadata_file = Path(metadata_path)
    base_dir = metadata_file.parent
    
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    pause_same = metadata.get("pause_same", DEFAULT_PAUSE_SAME)
    pause_different = metadata.get("pause_different", DEFAULT_PAUSE_DIFFERENT)
    
    combined_audio = b""
    prev_speaker = None
    
    for file_info in metadata["files"]:
        # ポーズ挿入
        if prev_speaker is not None:
            if file_info["speaker"] == prev_speaker:
                pause = pause_same
            else:
                pause = pause_different
            combined_audio += create_silence(pause)
        
        # 音声データ読み込み
        filepath = base_dir / file_info["filename"]
        with wave.open(str(filepath), "rb") as wav_file:
            combined_audio += wav_file.readframes(wav_file.getnframes())
        
        prev_speaker = file_info["speaker"]
    
    # 出力パス決定
    if output_path is None:
        output_path = str(base_dir / "combined.wav")
    
    # 保存
    save_wav(combined_audio, output_path)
    print(f"✅ 結合完了: {output_path}")
    
    # 結合後の長さを計算
    duration = len(combined_audio) / (SAMPLE_RATE * 2)
    print(f"📊 合計時間: {duration:.1f}秒")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Gemini TTS - 台本から音声を自動生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 単一テキストから音声生成
  python gemini_tts.py text "こんにちは" -o output.wav

  # 台本JSONから一括生成（結合あり）
  python gemini_tts.py dialogue script.json -o output_dir/ --combine

  # 既存音声ファイルを結合
  python gemini_tts.py combine metadata.json -o combined.wav
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # text コマンド
    text_parser = subparsers.add_parser("text", help="単一テキストから音声生成")
    text_parser.add_argument("text", help="読み上げるテキスト")
    text_parser.add_argument("-o", "--output", default="output.wav", help="出力ファイルパス")
    text_parser.add_argument("--voice", default=DEFAULT_VOICE, choices=AVAILABLE_VOICES, help="ボイスプリセット")
    text_parser.add_argument("--style", help="スタイル指示（例: 'ゆっくり丁寧に'）")
    
    # dialogue コマンド
    dialogue_parser = subparsers.add_parser("dialogue", help="台本JSONから一括生成")
    dialogue_parser.add_argument("script", help="台本JSONファイルパス")
    dialogue_parser.add_argument("-o", "--output", default="./output", help="出力ディレクトリ")
    dialogue_parser.add_argument("--combine", action="store_true", help="結合済みファイルも生成")
    dialogue_parser.add_argument("--pause-same", type=float, default=DEFAULT_PAUSE_SAME, help="同一話者間のポーズ（秒）")
    dialogue_parser.add_argument("--pause-different", type=float, default=DEFAULT_PAUSE_DIFFERENT, help="話者交代時のポーズ（秒）")
    
    # combine コマンド
    combine_parser = subparsers.add_parser("combine", help="既存音声ファイルを結合")
    combine_parser.add_argument("metadata", help="metadata.jsonのパス")
    combine_parser.add_argument("-o", "--output", help="出力ファイルパス")
    
    args = parser.parse_args()
    
    if args.command == "text":
        generate_single_audio(args.text, args.voice, args.output, args.style)
    elif args.command == "dialogue":
        generate_dialogue(args.script, args.output, args.combine, args.pause_same, args.pause_different)
    elif args.command == "combine":
        combine_audio_files(args.metadata, args.output)


if __name__ == "__main__":
    main()
