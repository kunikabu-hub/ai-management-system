# Google Drive MCP OAuth2セットアップガイド

## 現在の設定状況

- **認証情報**: `~/.config/claude-code/gdrive/credentials.json`
- **Claude設定**: `~/Library/Application Support/Claude/claude_desktop_config.json`

## OAuth2リフレッシュトークンの取得方法

### 手順1: OAuth Playgroundを使用

1. [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)にアクセス
2. 右上の設定アイコン⚙️をクリック
3. "Use your own OAuth credentials"にチェック
4. 以下を入力：
   - **OAuth Client ID**: `743931359241-gqv70k9t0tf346ebgi29sv5latpqlrrr.apps.googleusercontent.com`
   - **OAuth Client secret**: `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`
5. 左側のScope一覧から以下を選択：
   - `https://www.googleapis.com/auth/drive.readonly` (読み取り専用)
   - または `https://www.googleapis.com/auth/drive` (フルアクセス)
6. "Authorize APIs"をクリック
7. Googleアカウントでログイン・承認
8. "Exchange authorization code for tokens"をクリック
9. 表示される **Refresh token** をコピー

### 手順2: 設定ファイルの更新

リフレッシュトークンを取得したら、以下のコマンドで設定を更新：

```bash
# 設定ファイルを編集
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

以下のように`GOOGLE_REFRESH_TOKEN`を追加：

```json
{
  "mcpServers": {
    "gdrive": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-google-drive"
      ],
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

### 手順3: Claude Codeを再起動

設定を更新したら、Claude Codeを再起動して変更を反映させてください。

## 利用可能な機能

接続後、以下のようなGoogle Drive操作が可能になります：

- ファイル・フォルダの一覧取得
- ファイルの読み取り（Google Docs, Sheets, Slides対応）
- ファイルのアップロード・作成
- ファイルの削除・移動
- 共有設定の管理

## トラブルシューティング

### 認証エラーが出る場合
- リフレッシュトークンが正しいか確認
- Google Cloud Consoleでプロジェクトが有効化されているか確認
- 必要なAPIが有効化されているか確認（Google Drive API）

### 接続できない場合
- Claude Codeを完全に再起動
- 設定ファイルのJSON形式が正しいか確認（カンマ、括弧など）

## 参考リンク

- [Google OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
- [Google Cloud Console](https://console.cloud.google.com/)
- [mcp-google-drive GitHub](https://github.com/minhlong244/mcp-google-drive)
