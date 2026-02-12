#!/bin/bash
# Circleback Webhook Server起動スクリプト

echo "🚀 Circleback Webhook Serverを起動します..."
echo ""

# プロジェクトディレクトリに移動
cd "$(dirname "$0")"

# Python3の確認
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3がインストールされていません"
    exit 1
fi

# Flaskがインストールされているか確認
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️ Flaskがインストールされていません"
    echo "📦 インストール中..."
    pip3 install -r ../requirements.txt
fi

# .envファイルの確認
if [ ! -f ../.env ]; then
    echo "⚠️ .envファイルが見つかりません"
    echo "📝 テンプレートを作成します..."
    echo "CIRCLEBACK_WEBHOOK_SECRET=your_webhook_secret_here" >> ../.env
    echo "✅ .envファイルを作成しました。CIRCLEBACK_WEBHOOK_SECRETを設定してください。"
fi

# Webhook Serverを起動
echo ""
echo "📡 Webhook URL: http://localhost:5000/webhook/circleback"
echo "💚 Health Check: http://localhost:5000/health"
echo ""
echo "🛑 停止するには Ctrl+C を押してください"
echo ""

python3 circleback_webhook.py
