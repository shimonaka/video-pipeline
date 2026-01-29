# 🎬 Video Pipeline - 台本から動画を自動生成

台本（JSON）を入力すると、音声合成・リップシンク・動画レンダリングを経て、キャラクターが話す動画を自動生成するパイプラインです。

## 📁 ディレクトリ構成

```
video-pipeline/
├── scripts/                 # Pythonスクリプト
│   ├── gemini_tts.py       # 音声合成（Gemini TTS API）
│   ├── generate_lipsync.py # リップシンク生成（Rhubarb）
│   ├── integrate_data.py   # データ統合
│   └── run_pipeline.py     # 統合パイプライン
├── schemas/
│   └── examples/
│       └── sample-script.json  # サンプル台本
└── remotion-project/        # Remotion動画生成
    ├── src/
    │   ├── components/     # 再利用可能コンポーネント
    │   ├── types/          # TypeScript型定義
    │   ├── MultiSceneVideo.tsx
    │   └── Root.tsx
    └── public/             # アセット配置先
        ├── audio/          # 生成音声
        ├── lipsync/        # リップシンクJSON
        └── character/      # キャラクター画像
```

## 🚀 クイックスタート

### 1. 環境準備

#### Google API Key の設定
```powershell
# Google AI Studio で無料のAPIキーを取得
# https://aistudio.google.com/ → 「Get API key」→「Create API key」

setx GOOGLE_API_KEY "your-api-key-here"
# ターミナルを再起動
```

#### Rhubarb Lip Sync のインストール
```powershell
# 1. ダウンロード
# https://github.com/DanielSWolf/rhubarb-lip-sync/releases
# → Rhubarb-Lip-Sync-X.X.X-Windows.zip

# 2. 解凍して配置（例: C:\tools\rhubarb\）

# 3. 環境変数設定
setx RHUBARB_PATH "C:\tools\rhubarb\rhubarb.exe"
# ターミナルを再起動
```

#### Pythonパッケージのインストール
```powershell
pip install google-genai
```

#### Remotionプロジェクトのセットアップ
```powershell
cd Miyabi/video-pipeline/remotion-project
npm install
```

### 2. サンプル動画生成

```powershell
cd Miyabi/video-pipeline/scripts

# フルパイプライン実行（Remotionセットアップ前は --skip-render）
python run_pipeline.py full ../schemas/examples/sample-script.json -o ../output/ --skip-render

# Remotionセットアップ後
python run_pipeline.py full ../schemas/examples/sample-script.json -o ../output/
```

## 📝 台本フォーマット

```json
{
  "title": "動画タイトル",
  "speakers": {
    "narrator": { "name": "ナレーター", "voice": "Kore" }
  },
  "scenes": [
    {
      "id": "scene_001",
      "speaker": "narrator",
      "text": "セリフ内容"
    }
  ],
  "video": {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "background": "lightBlue"
  }
}
```

## 🎤 利用可能なボイス

Gemini TTSで使用可能なボイスプリセット:
- **Kore** (日本語推奨)
- Aoede, Charon, Fenrir, Puck, Zephyr, Orbit, Nova, Lyra, Helios

## 📋 個別コマンド

```powershell
# 音声生成のみ
python gemini_tts.py dialogue script.json -o output/ --combine

# リップシンク生成のみ
python generate_lipsync.py --batch output/audio/ -o output/lipsync/

# データ統合のみ
python integrate_data.py script.json output/audio/ output/lipsync/ -o output/pipeline-data.json

# Remotionプレビュー
cd ../remotion-project
npm start
```

## 💡 Tips

- **無料枠**: Gemini TTS APIは1日50リクエストまで無料
- **日本語対応**: Rhubarbは`--recognizer phonetic`モードで日本語に対応
- **口形状画像**: 6種類（A-F）を`public/character/mouth-{A-F}.png`に配置

## 📚 参考

このプロジェクトは以下のブログシリーズを参考に構築されました:
- [AI×動画制作28日間の検証記録](https://zenn.dev/akira_cloudjob/articles/20260101-series-overview)
