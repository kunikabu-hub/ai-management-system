# Google Drive MCP セットアップ手順

## 📋 準備完了

✅ OAuth認証情報: `~/.config/claude-code/gdrive/credentials.json`
✅ Pythonスクリプト: `get_google_drive_token.py`
✅ Claude設定ファイル: `~/Library/Application Support/Claude/claude_desktop_config.json`

## 🚀 実行手順

### ステップ1: 必要なライブラリをインストール

```bash
cd ~/ai-management-system
pip3 install -r requirements.txt
```

### ステップ2: 認証スクリプトを実行

```bash
python3 get_google_drive_token.py
```

### ステップ3: 何が起こるか

1. ブラウザが自動的に開きます
2. Googleアカウントでログイン
3. アプリケーションへのアクセスを承認
4. ターミナルにリフレッシュトークンが表示されます

### ステップ4: リフレッシュトークンを設定に追加

スクリプトが表示したリフレッシュトークンをコピーして、以下のコマンドで設定ファイルを編集：

```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

または

```bash
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

`GOOGLE_REFRESH_TOKEN`行を追加：

```json
{
  "mcpServers": {
    "gdrive": {
      "command": "npx",
      "args": ["-y", "mcp-google-drive"],
      "env": {
        "GOOGLE_CLIENT_ID": "743931359241-gqv70k9t0tf346ebgi29sv5latpqlrrr.apps.googleusercontent.com",
        "GOOGLE_CLIENT_SECRET": "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",
        "GOOGLE_REDIRECT_URI": "http://localhost",
        "GOOGLE_REFRESH_TOKEN": "ここにリフレッシュトークンを貼り付け"
      }
    }
  }
}
```

### ステップ5: Claude Codeを再起動

設定を反映させるため、Claude Codeを完全に終了して再起動してください。

## ⚠️ トラブルシューティング

### ブラウザが開かない場合

スクリプトがURLを表示するので、手動でブラウザにコピー＆ペーストしてください。

### "redirect_uri_mismatch" エラー

Google Cloud Consoleで承認済みのリダイレクトURIに以下を追加：
- `http://localhost:8080`
- `http://localhost`

手順:
1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. プロジェクト "hallowed-hold-487203-f0" を選択
3. 「APIとサービス」→「認証情報」
4. OAuth 2.0 クライアントIDをクリック
5. 「承認済みのリダイレクトURI」に上記を追加
6. 保存

### pip install がエラーになる場合

```bash
# 仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 get_google_drive_token.py
```

## 📚 次のステップ

認証が完了したら、Claude CodeでGoogle Driveの操作ができるようになります：

- ファイル一覧の取得
- Google Docs/Sheets/Slidesの読み取り
- ファイルのアップロード
- フォルダの作成・管理

## 🔗 関連リンク

- [Google Cloud Console](https://console.cloud.google.com/)
- [mcp-google-drive GitHub](https://github.com/minhlong244/mcp-google-drive)
