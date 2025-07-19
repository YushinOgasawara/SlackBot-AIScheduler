# SlackBot-AIScheduler プロトタイプ

SlackでメンションされたスレッドをLLMで解析し、Google Calendarに自動でスケジュールを登録するシステムのプロトタイプです。

## 🚀 クイックスタート

### 1. 環境設定
```bash
# 環境変数ファイルを作成
cp .env.example .env

# 必要な環境変数を設定
vim .env
```

### 2. Google Cloud設定
```bash
# サービスアカウントキーファイルを配置（実際のファイルに置き換えてください）
cp path/to/your/service-account.json ./service-account.json

# または、環境変数でサービスアカウント情報を設定することも可能
```

### 3. Dockerでの起動
```bash
# ビルド & 起動
docker-compose up --build

# バックグラウンドで起動
docker-compose up -d --build
```

### 4. 動作確認
```bash
# ヘルスチェック
curl http://localhost:8080/health

# 基本エンドポイント
curl http://localhost:8080/
```

## 📁 プロジェクト構造

```
prototype/
├── src/
│   ├── main.py                      # FastAPIメインアプリケーション
│   ├── handlers/
│   │   ├── slack_handler.py         # Slack API処理
│   │   ├── schedule_analyzer.py     # LLMによるスケジュール解析
│   │   └── calendar_handler.py      # Google Calendar API処理
│   ├── models/
│   │   └── schedule_models.py       # データモデル定義
│   ├── config/
│   │   └── settings.py              # 設定管理
│   └── utils/
│       ├── logger.py                # ログ処理
│       └── slack_verification.py    # Slack署名検証
├── tests/                           # テストファイル
├── requirements.txt                 # Python依存関係
├── Dockerfile                       # Docker設定
├── docker-compose.yml               # Docker Compose設定
├── .env.example                     # 環境変数の例
└── README.md                        # このファイル
```

## 🔧 開発用コマンド

### 本番環境と同様の起動
```bash
# Python環境での起動
python src/main.py

# uvicornでの起動
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

### ログの確認
```bash
# リアルタイムログ
docker-compose logs -f

# 特定のサービスのログ
docker-compose logs slack-bot-ai-scheduler
```

## 🔐 必要な設定

### Slack App設定
1. Slack Appを作成
2. Bot Token Scopesを設定:
   - `app_mentions:read`
   - `channels:history`
   - `chat:write`
   - `users:read`
   - `users:read.email`

### Google Cloud設定
1. Google Cloud Projectを作成
2. Calendar APIを有効化
3. サービスアカウントを作成
4. キーファイルをダウンロード

## 📋 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `SLACK_BOT_TOKEN` | Slack Bot Token | ✅ |
| `SLACK_SIGNING_SECRET` | Slack Signing Secret | ✅ |
| `GEMINI_API_KEY` | Gemini API Key | ✅ |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud Project ID | ✅ |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | サービスアカウントファイルパス | ✅ |
| `LOG_LEVEL` | ログレベル | ⚪ |
| `SCHEDULE_CONFIDENCE_THRESHOLD` | スケジュール信頼度閾値 | ⚪ |

## 🧪 テスト

```bash
# テスト実行（実装後）
pytest tests/

# カバレッジ付きテスト
pytest --cov=src tests/
```

## 📚 API エンドポイント

- `GET /` - 基本情報
- `GET /health` - ヘルスチェック
- `POST /slack/events` - Slack Events API

## 🔄 処理フロー

1. **Slack Events API** からのWebhook受信
2. **署名検証** でセキュリティチェック
3. **即座にACK応答** (3秒以内)
4. **バックグラウンド処理**:
   - スレッド内容取得
   - Gemini 2.5 Flashで解析
   - カレンダー空き時間確認
   - イベント作成
   - Slack通知

## 🚨 注意事項

- このプロトタイプはテスト用です
- 本番環境での使用前に十分なテストを実施してください
- セキュリティ設定を適切に行ってください
- API制限に注意してください
- `service-account.json`ファイルは実際のGoogle Cloudプロジェクトから取得する必要があります
- 初回起動前に必要な認証情報をすべて設定してください

## 📝 今後の改善点

- [ ] エラーハンドリングの強化
- [ ] テストケースの追加
- [ ] ログの改善
- [ ] パフォーマンスの最適化
- [ ] 設定の柔軟性向上