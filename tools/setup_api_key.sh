#!/bin/bash
# OpenAI APIキー設定スクリプト

echo "================================================"
echo "  OpenAI APIキー設定"
echo "================================================"
echo ""
echo "OpenAI APIキーを入力してください:"
echo "（形式: sk-proj-... または sk-...）"
echo ""
read -s -p "APIキー: " OPENAI_API_KEY
echo ""
echo ""

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ APIキーが入力されていません"
    exit 1
fi

# 環境変数を設定
export OPENAI_API_KEY="$OPENAI_API_KEY"

# .zshrcまたは.bashrcに追記（永続化）
SHELL_RC=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    echo ""
    echo "APIキーを $SHELL_RC に保存しますか？ (y/n)"
    read -p "> " save_choice

    if [ "$save_choice" = "y" ]; then
        # 既存のOPENAI_API_KEYを削除
        sed -i.bak '/export OPENAI_API_KEY=/d' "$SHELL_RC"

        # 新しいAPIキーを追記
        echo "" >> "$SHELL_RC"
        echo "# OpenAI API Key (自分史インタビューAPI用)" >> "$SHELL_RC"
        echo "export OPENAI_API_KEY='$OPENAI_API_KEY'" >> "$SHELL_RC"

        echo "✅ APIキーを $SHELL_RC に保存しました"
        echo "   次回ターミナル起動時から自動で読み込まれます"
    fi
fi

echo ""
echo "✅ APIキーを設定しました"
echo ""
echo "次のコマンドで本番サーバーを起動できます:"
echo "  cd tools"
echo "  python3 memoir_editor_api.py"
echo ""
