#!/bin/bash
# 自分史インタビューAPI起動スクリプト

set -e

echo "🚀 自分史インタビューAPI起動中..."

# OpenAI APIキーのチェック
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ エラー: OPENAI_API_KEY 環境変数が設定されていません"
    echo ""
    echo "以下のコマンドで設定してください:"
    echo "  export OPENAI_API_KEY='your-api-key-here'"
    echo ""
    exit 1
fi

# セッションディレクトリの作成
mkdir -p ./sessions

# Python仮想環境のチェック（オプション）
if [ ! -d "venv" ]; then
    echo "📦 Python仮想環境が見つかりません。作成しますか？ (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r ../requirements.txt
    fi
else
    source venv/bin/activate
fi

# 依存関係のチェック
echo "📦 依存関係をチェック中..."
pip install -q fastapi uvicorn openai pydantic 2>/dev/null || true

echo "✅ 準備完了"
echo ""
echo "APIサーバーを起動します..."
echo "  URL: http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo ""
echo "停止するには Ctrl+C を押してください"
echo ""

# サーバー起動
python memoir_editor_api.py
