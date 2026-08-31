# Google Drive MCP トラブルシューティング

## 再起動後に接続できない場合

### 1. 設定ファイルの確認

```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

以下の項目がすべて含まれているか確認：
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_REDIRECT_URI
- GOOGLE_REFRESH_TOKEN

### 2. MCP サーバーの手動テスト

```bash
export GOOGLE_CLIENT_ID="743931359241-gqv70k9t0tf346ebgi29sv5latpqlrrr.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="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"
export GOOGLE_REDIRECT_URI="http://localhost"
export GOOGLE_REFRESH_TOKEN="1//0eX1qVEP9OT9ICgYIARAAGA4SNwF-L9IrKwjPKAPGazxvYuCftdrYPOyxR0WU8VN7S8Vfvjw7HYyHtYhq-3kN-6SqO9SpRhTuNs8"

npx -y mcp-google-drive
```

エラーメッセージが表示される場合は、その内容をメモしてください。

### 3. Google Drive API の有効化確認

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. プロジェクト "hallowed-hold-487203-f0" を選択
3. 「APIとサービス」→「有効なAPIとサービス」
4. **Google Drive API** が有効になっているか確認
5. 無効の場合は「APIとサービスを有効化」から有効にする

### 4. トークンの再取得

トークンが無効になっている可能性があります：

```bash
cd ~/ai-management-system
python3 get_google_drive_token.py
```

新しいリフレッシュトークンを取得し、設定ファイルを更新してください。

### 5. ログの確認

Claude Codeのログを確認して、MCP接続エラーがないかチェック：

```bash
# Claude Codeを起動する際に詳細ログを有効化
DEBUG=* npx @anthropic-ai/claude-code
```

### 6. 代替の設定方法

もし `mcp-google-drive` で問題が続く場合、別のパッケージを試す：

```json
{
  "mcpServers": {
    "gdrive": {
      "command": "npx",
      "args": [
        "-y",
        "@botrun/mcp-google-drive"
      ],
      "env": {
        "GOOGLE_CREDENTIALS_PATH": "/Users/attadesign/.config/claude-code/gdrive/credentials.json",
        "GOOGLE_TOKEN_PATH": "/Users/attadesign/.config/claude-code/gdrive/token.json"
      }
    }
  }
}
```

## よくあるエラーと解決方法

### "Authentication failed"
→ リフレッシュトークンを再取得

### "Permission denied"
→ OAuth認証時に必要な権限を承認していない
→ `get_google_drive_token.py` を再実行し、すべての権限を承認

### "API not enabled"
→ Google Cloud ConsoleでGoogle Drive APIを有効化

### "Invalid client"
→ Client IDとClient Secretが正しいか確認
→ 設定ファイルに余分なスペースや改行がないか確認

## 問題が解決しない場合

以下の情報を確認してください：

1. 設定ファイルの内容
2. MCPサーバーのエラーログ
3. Google Cloud Consoleのプロジェクト設定
4. 使用しているClaude Codeのバージョン

```bash
npx @anthropic-ai/claude-code --version
```
