# AI Management System セットアップガイド

他のPCでこのプロジェクトを再構築するための完全なセットアップ手順です。

**最終更新**: 2026-02-13

---

## 📋 目次

1. [前提条件](#前提条件)
2. [リポジトリのクローン](#リポジトリのクローン)
3. [環境変数の設定](#環境変数の設定)
4. [依存関係のインストール](#依存関係のインストール)
5. [MCP連携の設定](#mcp連携の設定)
6. [Google Drive OAuth認証](#google-drive-oauth認証)
7. [動作確認](#動作確認)
8. [トラブルシューティング](#トラブルシューティング)

---

## 🔧 前提条件

以下がインストールされていることを確認してください：

### 必須ソフトウェア

- **Python 3.9以上**
  ```bash
  python3 --version
  ```

- **Git**
  ```bash
  git --version
  ```

- **Node.js & npm**（Notion MCP用）
  ```bash
  node --version
  npm --version
  ```

- **Claude Code CLI**
  - https://docs.anthropic.com/claude/docs/claude-code からインストール

### オプション（推奨）

- **Homebrew**（macOS）
  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  ```

- **ngrok**（Circleback Webhook用）
  ```bash
  brew install ngrok
  ```

---

## 📥 リポジトリのクローン

### 1. GitHubからクローン

```bash
# プロジェクトディレクトリに移動
cd ~/Documents

# リポジトリをクローン（Private）
git clone https://github.com/kunikabu-hub/ai-management-system.git

# ディレクトリに移動
cd ai-management-system
```

### 2. ディレクトリ構造の確認

```bash
ls -la
```

以下のような構造になっているはずです：

```
ai-management-system/
├── .claude/              # Claude Code設定
├── .gitignore            # Git除外設定
├── 00_context/           # コンテキスト・メモリ
├── 01_strategy/          # 戦略ドキュメント
├── output/               # 成果物
├── tools/                # 連携ツール
├── CLAUDE.md             # AI指示書
├── SETUP.md              # このファイル
├── requirements.txt      # Python依存関係
└── README.md             # プロジェクト概要
```

---

## 🔑 環境変数の設定

### 1. .envファイルの作成

プロジェクトルートに `.env` ファイルを作成します：

```bash
touch .env
```

### 2. 必要なAPIキーを取得・設定

以下のテンプレートを `.env` ファイルにコピーして、各APIキーを設定してください：

```bash
# ========================================
# API Keys for AI Management System
# ========================================

# xAI Grok API
# 取得先: https://console.x.ai/
GROK_API_KEY=xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Gemini API
# 取得先: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Notion Integration Token
# 取得先: https://www.notion.so/my-integrations
NOTION_TOKEN=ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# GitHub Personal Access Token
# 取得先: https://github.com/settings/tokens
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Figma Personal Access Token
# 取得先: https://www.figma.com/developers/api#access-tokens
FIGMA_TOKEN=figd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI API Key (ChatGPT)
# 取得先: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Circleback Webhook Signing Secret
# 取得先: https://app.circleback.ai/ → Settings → Webhook
CIRCLEBACK_WEBHOOK_SECRET=
```

### 3. 各APIキーの取得手順

#### 🔷 Grok API
1. https://console.x.ai/ にアクセス
2. ログイン → "API Keys" → "Create API Key"
3. キーをコピーして `.env` に貼り付け

#### 🔷 Gemini API
1. https://aistudio.google.com/app/apikey にアクセス
2. "Create API Key" をクリック
3. キーをコピーして `.env` に貼り付け

#### 🔷 Notion Integration Token
1. https://www.notion.so/my-integrations にアクセス
2. "New integration" → 名前を入力（例: AI Management System）
3. "Submit" → Internal Integration Tokenをコピー
4. `.env` に貼り付け
5. **重要**: Notionデータベースと接続する（後述）

#### 🔷 GitHub Personal Access Token
1. https://github.com/settings/tokens にアクセス
2. "Generate new token (classic)" をクリック
3. スコープを選択:
   - `repo` (Full control of private repositories)
   - `read:user`
4. トークンをコピーして `.env` に貼り付け

#### 🔷 Figma Personal Access Token
1. https://www.figma.com/developers/api#access-tokens にアクセス
2. 右上のアカウント → "Settings" → "Personal Access Tokens"
3. "Generate new token" → トークンをコピー
4. `.env` に貼り付け

#### 🔷 OpenAI API Key
1. https://platform.openai.com/api-keys にアクセス
2. "Create new secret key" → 名前を入力
3. キーをコピーして `.env` に貼り付け
4. **注意**: 課金設定が必要

#### 🔷 Circleback Webhook Secret
1. https://app.circleback.ai/ にログイン
2. Settings → Webhook（または Automations → Webhook）
3. Signing Secretをコピーして `.env` に貼り付け

---

## 📦 依存関係のインストール

### 1. Python依存関係のインストール

```bash
pip3 install -r requirements.txt
```

以下がインストールされます：
- `google-auth-oauthlib` - Google Drive OAuth
- `google-api-python-client` - Google APIs
- `requests` - HTTP通信
- `playwright` - Web自動化
- `flask` - Webhook受信サーバー
- `python-dotenv` - 環境変数管理

### 2. Playwrightブラウザのインストール

```bash
playwright install chromium
```

### 3. Notion MCPサーバーのインストール

```bash
npx -y @notionhq/notion-mcp-server
```

---

## 🔌 MCP連携の設定

### 1. .mcp.jsonファイルの作成

プロジェクトルートに `.mcp.json` ファイルを作成します：

```bash
touch .mcp.json
```

### 2. MCP設定を記述

`.mcp.json` に以下を記述：

```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "NOTION_TOKEN": "ntn_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

**重要**: `NOTION_TOKEN` を実際の値に置き換えてください。

### 3. Claude Codeの再起動

MCPサーバーを読み込むため、Claude Codeを再起動します：

```bash
# エイリアスがある場合
ccr

# またはClaude Codeを手動で再起動
```

---

## 🔐 Google Drive OAuth認証

### 1. Google Cloud Platformでプロジェクトを作成

1. https://console.cloud.google.com/ にアクセス
2. 新しいプロジェクトを作成（例: "AI Management System"）
3. プロジェクトを選択

### 2. Google Drive APIを有効化

1. 左メニュー → "APIとサービス" → "ライブラリ"
2. "Google Drive API" を検索 → "有効にする"
3. 同様に "Google Calendar API" も有効化

### 3. OAuth認証情報の作成

1. "APIとサービス" → "認証情報"
2. "認証情報を作成" → "OAuth クライアントID"
3. アプリケーションの種類: **デスクトップアプリ**
4. 名前: "AI Management System"
5. "作成" → JSONファイルをダウンロード

### 4. 認証情報を配置

```bash
mkdir -p ~/.config/claude-code/gdrive
mv ~/Downloads/client_secret_*.json ~/.config/claude-code/gdrive/credentials.json
```

### 5. OAuth認証を実行

```bash
cd tools
python3 get_google_drive_token.py
```

ブラウザが開き、Googleアカウントでログインを求められます。
許可すると、`token.json` が自動生成されます。

### 6. 動作確認

```bash
./show_drive_files.sh 10
```

Google Driveのファイル一覧が表示されればOKです。

---

## ✅ 動作確認

### 1. 各APIのテスト

#### Grok API
```bash
cd tools
python3 -c "from grok_api import call_grok; print(call_grok('Hello'))"
```

#### Gemini API
```bash
python3 -c "from gemini_api import call_gemini; print(call_gemini('Hello'))"
```

#### OpenAI API
```bash
python3 -c "from openai_helper import call_openai; print(call_openai('Hello'))"
```

#### GitHub API
```bash
python3 -c "from github_helper import get_user_info; print(get_user_info())"
```

#### Figma API
```bash
python3 -c "from figma_helper import get_user_info; print(get_user_info())"
```

### 2. Notion連携のテスト

Claude Codeで以下を実行：

```
記事ネタ帳データベースの内容を表示してください
```

データベースの内容が表示されればOKです。

### 3. Circleback Webhookのテスト

```bash
cd tools
./start_webhook_server.sh
```

サーバーが起動したら、別ターミナルで：

```bash
curl http://localhost:5000/health
```

`{"status": "healthy"}` が返ってくればOKです。

---

## 🚨 トラブルシューティング

### ❌ 問題: `pip3 install`でエラーが出る

**原因**: Pythonのバージョンが古い、または権限の問題

**解決方法**:
```bash
# Pythonバージョンを確認
python3 --version

# 3.9未満の場合はアップグレード
brew install python@3.11

# 権限エラーの場合
pip3 install --user -r requirements.txt
```

---

### ❌ 問題: Notion MCPサーバーで401エラー

**原因**: NOTION_TOKENが間違っている、またはデータベースと未接続

**解決方法**:
1. `.mcp.json` のトークンを確認
2. Notionでデータベースと連携:
   - Notionデータベースを開く
   - 右上の「…」→ "Add connections"
   - 作成したIntegrationを選択

3. Claude Codeを再起動:
   ```bash
   ccr
   ```

---

### ❌ 問題: Google Drive認証でエラー

**原因**: `credentials.json` の配置場所が間違っている

**解決方法**:
```bash
# 正しい場所に配置されているか確認
ls -la ~/.config/claude-code/gdrive/

# 再度認証を実行
cd tools
python3 get_google_drive_token.py
```

---

### ❌ 問題: Webhook Serverが起動しない

**原因**: ポート5000が既に使用されている

**解決方法**:
```bash
# 使用中のプロセスを確認
lsof -i :5000

# プロセスを停止
kill -9 <PID>

# または別のポートを使用（circleback_webhook.py を編集）
```

---

### ❌ 問題: APIキーが認識されない

**原因**: `.env` ファイルが読み込まれていない

**解決方法**:
```bash
# .envファイルの確認
cat .env

# 環境変数が読み込まれているか確認
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('NOTION_TOKEN'))"
```

---

### ❌ 問題: Claude Codeでスキルが認識されない

**原因**: `.claude/commands/` が正しく配置されていない

**解決方法**:
```bash
# スキルファイルの確認
ls -la .claude/commands/

# Claude Codeを再起動
ccr
```

---

## 🔄 定期メンテナンス

### 依存関係のアップデート

```bash
# 最新版を確認
pip3 list --outdated

# 一括アップデート
pip3 install --upgrade -r requirements.txt
```

### APIトークンの更新

APIトークンには有効期限がある場合があります。定期的に確認してください：

- **Google Drive**: token.jsonは自動更新されます
- **GitHub**: トークンの有効期限を確認
- **Notion**: 通常は無期限ですが、Integrationを削除すると無効化されます

---

## 📚 参考ドキュメント

- **Claude Code公式ドキュメント**: https://docs.anthropic.com/claude/docs/claude-code
- **Notion API**: https://developers.notion.com/
- **Google Drive API**: https://developers.google.com/drive
- **Circleback Webhook**: https://circleback.ai/docs/webhook-integration

---

## 🆘 サポート

問題が解決しない場合は、以下を確認してください：

1. **ログの確認**: エラーメッセージを詳しく読む
2. **Githubリポジトリ**: https://github.com/kunikabu-hub/ai-management-system
3. **関連ドキュメント**: `troubleshooting.md` を参照

---

## ✅ セットアップ完了チェックリスト

セットアップが正しく完了したか、以下を確認してください：

- [ ] リポジトリをクローン
- [ ] `.env` ファイルを作成し、全APIキーを設定
- [ ] `pip3 install -r requirements.txt` を実行
- [ ] Playwrightブラウザをインストール
- [ ] `.mcp.json` を作成してNotion連携を設定
- [ ] Google Drive OAuth認証を完了
- [ ] 各APIの動作確認が成功
- [ ] Claude Codeでスキルが使える
- [ ] Webhook Serverが起動する

すべてにチェックが入れば、セットアップ完了です！🎉

---

**作成日**: 2026-02-13
**最終更新**: 2026-02-13
