#!/bin/bash

# Cloud Shell用デプロイスクリプト
echo "=== SlackBot-AIScheduler Cloud Shell デプロイ ==="

# 1. プロジェクト設定
echo "1. プロジェクト設定..."
gcloud config set project slackbot-aischeduler

# 2. ファイル展開
echo "2. ファイル展開..."
tar -xzf slack-bot-prototype.tar.gz

# 3. 認証設定
echo "3. Docker認証設定..."
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# 4. Dockerビルド
echo "4. Dockerイメージビルド（x86_64）..."
docker build -t asia-northeast1-docker.pkg.dev/slackbot-aischeduler/slackbot-aischeduler/slack-bot-ai-scheduler:1.0.3 .

# 5. イメージプッシュ
echo "5. イメージをArtifact Registryにプッシュ..."
docker push asia-northeast1-docker.pkg.dev/slackbot-aischeduler/slackbot-aischeduler/slack-bot-ai-scheduler:1.0.3

# 6. Cloud Runデプロイ
echo "6. Cloud Runにデプロイ..."
gcloud run deploy slack-bot-ai-scheduler \
  --image asia-northeast1-docker.pkg.dev/slackbot-aischeduler/slackbot-aischeduler/slack-bot-ai-scheduler:1.0.3 \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars="SLACK_BOT_TOKEN=dummy,SLACK_SIGNING_SECRET=dummy,GEMINI_API_KEY=dummy,GOOGLE_CLOUD_PROJECT=slackbot-aischeduler"

echo "✅ デプロイ完了！"
echo ""
echo "次の手順:"
echo "1. Cloud Runコンソールで環境変数を実際の値に更新"
echo "2. Slack Appの設定でWebhook URLを設定"
echo "3. Service Accountキーを設定"