# システム拡張 詳細設計書

**作成日**: 2026-02-12
**バージョン**: 1.0
**プロジェクト**: AI Management System 機能拡張
**想定期間**: 2026年2月〜2026年5月（約3ヶ月）

---

## 📋 目次

1. [概要](#概要)
2. [MCP連携追加](#mcp連携追加)
3. [追加API](#追加api)
4. [新規スキル](#新規スキル)
5. [実装の優先順位](#実装の優先順位)
6. [スケジュール案](#スケジュール案)
7. [リスクと対策](#リスクと対策)

---

## 概要

### プロジェクト目標

AI Management Systemの機能を大幅に拡張し、以下を実現する：

1. **MCP連携**: Notion、Google Sheets、Slack、GitHub、Figma、Playwrightとの連携により、ワークフロー自動化を強化
2. **追加API**: Grok API（X/Twitter）、Gemini API（記事執筆）により、多様な情報源とAIモデルを活用
3. **新規スキル**: 6つの新規スキルにより、トレンド分析・記事執筆・SNS運用を自動化

### 期待される効果

- **業務効率化**: 手作業タスクの80%削減
- **情報収集の自動化**: 毎日のトレンドチェックを自動化
- **記事執筆の効率化**: Gemini APIによる高品質な記事生成
- **SNS運用の最適化**: X投稿パフォーマンス分析による改善サイクル

---

## MCP連携追加

MCP（Model Context Protocol）は、AIアシスタントが外部ツールと連携するためのプロトコルです。以下の6つのMCPサーバーを追加します。

### 1. Notion MCP

#### 概要
- **目的**: 記事ネタ帳データベースの読み書き
- **ユースケース**:
  - トレンド情報をNotionデータベースに自動保存
  - 記事執筆時にネタ帳から情報を取得
  - 記事公開ステータスの更新

#### 設定手順

**1. Notion Integration の作成**

```bash
# 1. Notion Developers (https://www.notion.so/my-integrations) にアクセス
# 2. "New integration" をクリック
# 3. Integration名: "AI Management System"
# 4. 以下の権限を付与:
#    - Read content
#    - Update content
#    - Insert content
# 5. Integration Token をコピー
```

**2. データベースの準備**

Notionで「記事ネタ帳」データベースを作成し、以下のプロパティを設定：

| プロパティ名 | タイプ | 説明 |
|------------|--------|------|
| タイトル | Title | 記事タイトル |
| カテゴリ | Select | B2C / B2B / 技術・トレンド |
| ステータス | Select | アイデア / 執筆中 / 完了 / 公開済み |
| 優先度 | Select | 高 / 中 / 低 |
| 作成日 | Date | 作成日 |
| 公開予定日 | Date | 公開予定日 |
| タグ | Multi-select | #パーソナライズ絵本 #AI #B2B など |
| 要約 | Text | 記事の要約 |
| 参考資料 | URL | 参考リンク |

**3. データベースとIntegrationの接続**

```bash
# 1. 作成したデータベースを開く
# 2. 右上の "..." メニューをクリック
# 3. "Add connections" を選択
# 4. "AI Management System" Integrationを選択
```

**4. MCP設定ファイルの編集**

`~/.claude/mcp.json` に以下を追加：

```json
{
  "mcpServers": {
    "notion": {
      "command": "npx",
      "args": [
        "-y",
        "@notionhq/client"
      ],
      "env": {
        "NOTION_API_KEY": "secret_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "NOTION_DATABASE_ID": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
      }
    }
  }
}
```

**必要な認証情報**:
- `NOTION_API_KEY`: Notion Integration Token
- `NOTION_DATABASE_ID`: 記事ネタ帳データベースのID（URLの最後の32文字）

#### 実装の詳細

**使用するツール**:
- `notion_create_page`: 新しいページ（記事ネタ）を作成
- `notion_query_database`: データベースを検索
- `notion_update_page`: ページを更新（ステータス変更など）

**実装例**:
```python
# 疑似コード
def save_trend_to_notion(title, category, summary, tags):
    notion.create_page(
        database_id=NOTION_DATABASE_ID,
        properties={
            "タイトル": {"title": [{"text": {"content": title}}]},
            "カテゴリ": {"select": {"name": category}},
            "ステータス": {"select": {"name": "アイデア"}},
            "優先度": {"select": {"name": "中"}},
            "要約": {"rich_text": [{"text": {"content": summary}}]},
            "タグ": {"multi_select": [{"name": tag} for tag in tags]}
        }
    )
```

---

### 2. Google Sheets MCP

#### 概要
- **目的**: 経理スプレッドシートの読み書き
- **ユースケース**:
  - 売上データの自動記録
  - 経費データの集計
  - 月次レポートの自動生成

#### 設定手順

**1. Google Cloud Project の作成**

```bash
# 1. Google Cloud Console (https://console.cloud.google.com/) にアクセス
# 2. 新しいプロジェクトを作成: "AI Management System"
# 3. Google Sheets API を有効化
# 4. 認証情報 > サービスアカウントを作成
#    - サービスアカウント名: "ai-mgmt-sheets"
#    - 役割: Editor
# 5. キーを作成（JSON形式）してダウンロード
```

**2. スプレッドシートの準備**

Google Sheetsで「経理管理」スプレッドシートを作成し、以下のシートを設定：

**売上シート**:
| 日付 | 項目 | 金額 | カテゴリ | メモ |
|------|------|------|----------|------|
| 2026-02-12 | B2C売上 | 50,000 | 絵本販売 | 鈴木自工 |

**経費シート**:
| 日付 | 項目 | 金額 | カテゴリ | メモ |
|------|------|------|----------|------|
| 2026-02-12 | AI利用料 | 5,000 | システム | OpenAI API |

**3. サービスアカウントの共有**

```bash
# 1. スプレッドシートを開く
# 2. "共有" ボタンをクリック
# 3. サービスアカウントのメールアドレス（xxx@xxx.iam.gserviceaccount.com）を追加
# 4. 権限: 編集者
```

**4. MCP設定ファイルの編集**

`~/.claude/mcp.json` に以下を追加：

```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "node",
      "args": [
        "/path/to/google-sheets-mcp-server.js"
      ],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/service-account-key.json",
        "SPREADSHEET_ID": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
      }
    }
  }
}
```

**必要な認証情報**:
- `GOOGLE_APPLICATION_CREDENTIALS`: サービスアカウントキー（JSON）のパス
- `SPREADSHEET_ID`: スプレッドシートのID（URLの一部）

#### 実装の詳細

**使用するツール**:
- `sheets_read`: シートからデータを読み込む
- `sheets_write`: シートにデータを書き込む
- `sheets_append`: シートに行を追加

**実装例**:
```python
# 疑似コード
def record_sales(date, item, amount, category, memo):
    sheets.append(
        spreadsheet_id=SPREADSHEET_ID,
        range="売上!A:E",
        values=[[date, item, amount, category, memo]]
    )
```

---

### 3. Slack MCP

#### 概要
- **目的**: Slackチャンネルへのメッセージ送受信
- **ユースケース**:
  - トレンド分析結果の自動通知
  - 記事公開の通知
  - エラー・アラートの送信

#### 設定手順

**1. Slack App の作成**

```bash
# 1. Slack API (https://api.slack.com/apps) にアクセス
# 2. "Create New App" をクリック
# 3. "From scratch" を選択
# 4. App Name: "AI Management System"
# 5. Workspace: 使用するワークスペースを選択
```

**2. 権限の設定**

```bash
# 1. "OAuth & Permissions" に移動
# 2. 以下のBot Token Scopesを追加:
#    - chat:write (メッセージ送信)
#    - chat:write.public (パブリックチャンネルに投稿)
#    - channels:read (チャンネル一覧取得)
#    - channels:history (チャンネル履歴読み込み)
# 3. "Install to Workspace" をクリック
# 4. Bot User OAuth Token をコピー
```

**3. チャンネルへの招待**

```bash
# 1. Slackで通知先チャンネル（例: #ai-notifications）を開く
# 2. チャンネル設定 > "Integrations" > "Add apps"
# 3. "AI Management System" を追加
```

**4. MCP設定ファイルの編集**

`~/.claude/mcp.json` に以下を追加：

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": [
        "-y",
        "@slack/bolt"
      ],
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-XXXXXXXXXXXX-XXXXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXX",
        "SLACK_CHANNEL_ID": "C0XXXXXXXXX"
      }
    }
  }
}
```

**必要な認証情報**:
- `SLACK_BOT_TOKEN`: Bot User OAuth Token
- `SLACK_CHANNEL_ID`: 通知先チャンネルのID

#### 実装の詳細

**使用するツール**:
- `slack_post_message`: メッセージを投稿
- `slack_get_channel_history`: チャンネル履歴を取得

**実装例**:
```python
# 疑似コード
def notify_trend_analysis(summary):
    slack.post_message(
        channel=SLACK_CHANNEL_ID,
        text=f"📊 本日のトレンド分析が完了しました\n\n{summary}",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*📊 本日のトレンド分析*\n\n{summary}"}
            },
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "詳細を見る"}, "url": "https://..."}
                ]
            }
        ]
    )
```

---

### 4. GitHub MCP

#### 概要
- **目的**: GitHub Issueの作成・管理
- **ユースケース**:
  - バグ報告の自動Issue化
  - タスク管理（TODO → Issue）
  - プロジェクト進捗の追跡

#### 設定手順

**1. GitHub Personal Access Token の作成**

```bash
# 1. GitHub (https://github.com/settings/tokens) にアクセス
# 2. "Generate new token (classic)" をクリック
# 3. Note: "AI Management System"
# 4. 以下のスコープを選択:
#    - repo (すべて)
#    - workflow
# 5. "Generate token" をクリック
# 6. トークンをコピー（一度しか表示されない）
```

**2. リポジトリの準備**

GitHub で「ai-management-system」リポジトリを作成（プライベート推奨）

**3. MCP設定ファイルの編集**

`~/.claude/mcp.json` に以下を追加：

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@octokit/rest"
      ],
      "env": {
        "GITHUB_TOKEN": "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "GITHUB_OWNER": "your-github-username",
        "GITHUB_REPO": "ai-management-system"
      }
    }
  }
}
```

**必要な認証情報**:
- `GITHUB_TOKEN`: Personal Access Token
- `GITHUB_OWNER`: GitHubユーザー名
- `GITHUB_REPO`: リポジトリ名

#### 実装の詳細

**使用するツール**:
- `github_create_issue`: Issueを作成
- `github_list_issues`: Issue一覧を取得
- `github_update_issue`: Issueを更新（クローズなど）

**実装例**:
```python
# 疑似コード
def create_task_issue(title, body, labels):
    github.create_issue(
        owner=GITHUB_OWNER,
        repo=GITHUB_REPO,
        title=title,
        body=body,
        labels=labels
    )
```

---

### 5. Figma MCP

#### 概要
- **目的**: Figmaデザインファイルのレビュー
- **ユースケース**:
  - デザインレビューコメントの自動収集
  - デザイン変更の追跡
  - スクリーンショットの取得

#### 設定手順

**1. Figma Personal Access Token の作成**

```bash
# 1. Figma (https://www.figma.com/settings) にアクセス
# 2. "Personal Access Tokens" セクションに移動
# 3. "Create new token" をクリック
# 4. Token name: "AI Management System"
# 5. トークンをコピー
```

**2. Figmaファイルの準備**

Figmaで「えほんインク デザイン」ファイルを作成し、共有設定を確認

**3. MCP設定ファイルの編集**

`~/.claude/mcp.json` に以下を追加：

```json
{
  "mcpServers": {
    "figma": {
      "command": "node",
      "args": [
        "/path/to/figma-mcp-server.js"
      ],
      "env": {
        "FIGMA_ACCESS_TOKEN": "figd_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "FIGMA_FILE_KEY": "XXXXXXXXXXXXXXXXXXXXXXXX"
      }
    }
  }
}
```

**必要な認証情報**:
- `FIGMA_ACCESS_TOKEN`: Personal Access Token
- `FIGMA_FILE_KEY`: FigmaファイルのKey（URLの一部）

#### 実装の詳細

**使用するツール**:
- `figma_get_file`: ファイル情報を取得
- `figma_get_comments`: コメントを取得
- `figma_export_image`: 画像をエクスポート

**実装例**:
```python
# 疑似コード
def review_design(file_key):
    comments = figma.get_comments(file_key)
    for comment in comments:
        print(f"{comment.user}: {comment.message}")
```

---

### 6. Playwright MCP

#### 概要
- **目的**: Web自動化（スクレイピング、テスト）
- **ユースケース**:
  - 競合サイトのスクレイピング
  - Web UIのスクリーンショット取得
  - E2Eテストの自動化

#### 設定手順

**1. Playwrightのインストール**

```bash
npm install -g playwright
npx playwright install
```

**2. MCP設定ファイルの編集**

`~/.claude/mcp.json` に以下を追加：

```json
{
  "mcpServers": {
    "playwright": {
      "command": "node",
      "args": [
        "/path/to/playwright-mcp-server.js"
      ]
    }
  }
}
```

**必要な認証情報**: なし

#### 実装の詳細

**使用するツール**:
- `playwright_navigate`: ページに移動
- `playwright_screenshot`: スクリーンショット取得
- `playwright_extract_text`: テキスト抽出

**実装例**:
```python
# 疑似コード
def scrape_competitor_site(url):
    playwright.navigate(url)
    text = playwright.extract_text("article")
    screenshot = playwright.screenshot()
    return text, screenshot
```

---

## 追加API

### 1. Grok API（X/Twitter）

#### 概要
- **目的**: X（旧Twitter）の情報収集・投稿
- **ユースケース**:
  - トレンドツイートの収集
  - 自動投稿
  - エンゲージメント分析

#### 設定手順

**1. X Developer Account の作成**

```bash
# 1. X Developer Portal (https://developer.x.com/) にアクセス
# 2. "Sign up" で開発者アカウントを作成
# 3. 使用目的を説明（個人/商用利用）
# 4. アプリを作成: "AI Management System"
```

**2. API Keysの取得**

```bash
# 1. アプリの "Keys and tokens" タブに移動
# 2. 以下をコピー:
#    - API Key
#    - API Secret Key
#    - Bearer Token
#    - Access Token
#    - Access Token Secret
```

**3. 環境変数の設定**

`~/.bashrc` または `~/.zshrc` に以下を追加：

```bash
export GROK_API_KEY="your-api-key"
export GROK_API_SECRET="your-api-secret"
export GROK_BEARER_TOKEN="your-bearer-token"
export GROK_ACCESS_TOKEN="your-access-token"
export GROK_ACCESS_SECRET="your-access-secret"
```

**必要な認証情報**:
- `GROK_API_KEY`: API Key
- `GROK_API_SECRET`: API Secret Key
- `GROK_BEARER_TOKEN`: Bearer Token
- `GROK_ACCESS_TOKEN`: Access Token
- `GROK_ACCESS_SECRET`: Access Token Secret

#### 実装の詳細

**使用するライブラリ**: `tweepy` (Python)

```python
import tweepy

# 認証
auth = tweepy.OAuthHandler(GROK_API_KEY, GROK_API_SECRET)
auth.set_access_token(GROK_ACCESS_TOKEN, GROK_ACCESS_SECRET)
api = tweepy.API(auth)

# ツイート投稿
def post_tweet(text):
    api.update_status(text)

# トレンド取得
def get_trends():
    trends = api.get_place_trends(23424856)  # 日本
    return trends[0]['trends']
```

---

### 2. Gemini API

#### 概要
- **目的**: Google Gemini を使った記事執筆
- **ユースケース**:
  - 長文記事の生成
  - 多言語翻訳
  - コード生成

#### 設定手順

**1. Google AI Studio でAPI Keyを取得**

```bash
# 1. Google AI Studio (https://makersuite.google.com/app/apikey) にアクセス
# 2. "Create API key" をクリック
# 3. API Keyをコピー
```

**2. 環境変数の設定**

`~/.bashrc` または `~/.zshrc` に以下を追加：

```bash
export GEMINI_API_KEY="AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

**必要な認証情報**:
- `GEMINI_API_KEY`: Google AI Studio API Key

#### 実装の詳細

**使用するライブラリ**: `google-generativeai` (Python)

```python
import google.generativeai as genai

# 認証
genai.configure(api_key=GEMINI_API_KEY)

# モデル選択
model = genai.GenerativeModel('gemini-pro')

# 記事生成
def generate_article(prompt):
    response = model.generate_content(prompt)
    return response.text
```

---

## 新規スキル

### 1. /meta-trend-daily

#### 概要
- **目的**: 毎日のトレンド情報を自動収集・分類
- **実行タイミング**: 毎日朝9:00（cron）
- **処理時間**: 約10分

#### 機能仕様

**実行内容**:
1. Grok API（X/Twitter）でトレンドツイートを収集
2. WebSearchで関連記事を検索
3. トレンドをカテゴリ別に分類（業界、技術、マーケティング、競合）
4. Notion「記事ネタ帳」データベースに保存
5. Slack通知（サマリー）

**入力**: なし（自動実行）

**出力**:
- Notion: 記事ネタ帳に10-20件のトレンド情報
- Slack: トレンドサマリー通知
- `output/trends/daily/YYYY-MM-DD_meta_trends.md`

#### 実装例

```python
# 疑似コード
def meta_trend_daily():
    # 1. X/Twitterトレンド取得
    x_trends = grok_api.get_trends(location="日本")

    # 2. 各トレンドについてWeb検索
    trend_data = []
    for trend in x_trends[:20]:
        articles = web_search(trend['name'])
        trend_data.append({
            'trend': trend['name'],
            'tweet_volume': trend['tweet_volume'],
            'articles': articles,
            'category': classify_category(trend, articles)
        })

    # 3. Notionに保存
    for data in trend_data:
        if is_relevant(data):  # えほんインクに関連するか判定
            notion.create_page(
                database_id=NOTION_DATABASE_ID,
                properties={
                    'タイトル': data['trend'],
                    'カテゴリ': data['category'],
                    'ステータス': 'アイデア',
                    '要約': summarize(data['articles'])
                }
            )

    # 4. Slack通知
    summary = generate_summary(trend_data)
    slack.post_message(
        channel=SLACK_CHANNEL_ID,
        text=f"📊 本日のトレンド分析完了\n\n{summary}"
    )

    # 5. ファイル保存
    save_to_file(trend_data, f"output/trends/daily/{today}_meta_trends.md")
```

**cron設定**:
```bash
0 9 * * * cd /path/to/ai-management-system && claude run meta-trend-daily
```

---

### 2. /digest

#### 概要
- **目的**: 特定トピックの分析レポート生成
- **実行タイミング**: 手動実行
- **処理時間**: 約5分

#### 機能仕様

**実行内容**:
1. トピックに関連する情報を収集（Web検索、Notion、Google Drive）
2. 情報を分析・要約
3. レポート生成（構成: 概要、主要トピック、データ、考察）
4. `output/digest/` に保存

**入力**: `[トピック]`

**出力**: `output/digest/YYYY-MM-DD_[トピック]_digest.md`

#### 使い方

```bash
/digest パーソナライズ絵本市場
/digest AI画像生成技術
```

#### 実装例

```python
# 疑似コード
def digest(topic):
    # 1. 情報収集
    web_results = web_search(f"{topic} 最新情報 2026")
    notion_results = notion.query_database(filter={'タグ': topic})
    memory_results = read_memory(topic)

    # 2. 情報を統合・分析
    all_info = merge_info(web_results, notion_results, memory_results)
    analysis = analyze_info(all_info)

    # 3. レポート生成
    report = generate_report(
        topic=topic,
        overview=analysis['overview'],
        key_topics=analysis['key_topics'],
        data=analysis['data'],
        insights=analysis['insights']
    )

    # 4. 保存
    save_to_file(report, f"output/digest/{today}_{topic}_digest.md")

    return report
```

---

### 3. /media-mix-weekly

#### 概要
- **目的**: X投稿パフォーマンス分析
- **実行タイミング**: 毎週月曜日朝9:00（cron）
- **処理時間**: 約5分

#### 機能仕様

**実行内容**:
1. Grok APIで過去1週間の投稿データを取得
2. エンゲージメント指標を分析（いいね、RT、リプライ、インプレッション）
3. パフォーマンスレポート生成（ベスト投稿、改善点）
4. Google Sheetsに記録
5. Slack通知

**入力**: なし（自動実行）

**出力**:
- Google Sheets: 週次パフォーマンスデータ
- Slack: レポート通知
- `output/media_mix/YYYY-MM-DD_weekly_report.md`

#### 実装例

```python
# 疑似コード
def media_mix_weekly():
    # 1. 過去1週間の投稿取得
    tweets = grok_api.get_user_timeline(count=100, since=one_week_ago)

    # 2. エンゲージメント分析
    analytics = {
        'total_tweets': len(tweets),
        'total_likes': sum(t['favorite_count'] for t in tweets),
        'total_retweets': sum(t['retweet_count'] for t in tweets),
        'total_replies': sum(t['reply_count'] for t in tweets),
        'total_impressions': sum(t['impression_count'] for t in tweets),
        'engagement_rate': calculate_engagement_rate(tweets),
        'best_tweet': max(tweets, key=lambda t: t['engagement']),
        'worst_tweet': min(tweets, key=lambda t: t['engagement'])
    }

    # 3. レポート生成
    report = generate_weekly_report(analytics)

    # 4. Google Sheetsに記録
    sheets.append(
        spreadsheet_id=SPREADSHEET_ID,
        range="週次レポート!A:H",
        values=[[
            today,
            analytics['total_tweets'],
            analytics['total_likes'],
            analytics['total_retweets'],
            analytics['engagement_rate'],
            analytics['best_tweet']['text'][:50]
        ]]
    )

    # 5. Slack通知
    slack.post_message(
        channel=SLACK_CHANNEL_ID,
        text=f"📈 週次X投稿レポート\n\n{report}"
    )

    # 6. ファイル保存
    save_to_file(report, f"output/media_mix/{today}_weekly_report.md")
```

**cron設定**:
```bash
0 9 * * 1 cd /path/to/ai-management-system && claude run media-mix-weekly
```

---

### 4. /gemini-write

#### 概要
- **目的**: Gemini APIを使った記事執筆
- **実行タイミング**: 手動実行
- **処理時間**: 約3-5分

#### 機能仕様

**実行内容**:
1. テーマを受け取る
2. Google Drive、05_learning/、記憶から関連資料を検索
3. Gemini APIに記事生成を依頼
4. 記事の構成・下書きを生成
5. `output/articles/` に保存

**入力**: `[テーマ]`

**出力**: `output/articles/YYYY-MM-DD_[テーマ]_gemini.md`

#### 使い方

```bash
/gemini-write パーソナライズ絵本の未来
/gemini-write B2Bマーケティングのトレンド
```

#### 実装例

```python
# 疑似コード
def gemini_write(theme):
    # 1. 関連資料収集
    related_docs = search_related_docs(theme)

    # 2. プロンプト構築
    prompt = f"""
    以下のテーマで記事を執筆してください：{theme}

    参考資料:
    {format_docs(related_docs)}

    記事の構成:
    - タイトル候補（3パターン）
    - 導入（200-300文字）
    - 本文（3-5セクション、各500-800文字）
    - まとめ（200-300文字）

    トーン: プロフェッショナル、データ重視
    文字数: 2,500-3,500文字
    """

    # 3. Gemini APIで生成
    article = gemini_api.generate_content(prompt)

    # 4. 保存
    save_to_file(article, f"output/articles/{today}_{theme}_gemini.md")

    return article
```

---

### 5. /title-gen

#### 概要
- **目的**: 記事タイトルの生成
- **実行タイミング**: 手動実行
- **処理時間**: 約30秒

#### 機能仕様

**実行内容**:
1. 記事の要約を受け取る
2. 3パターンのタイトルを生成（真面目、キャッチー、SEO重視）
3. 各タイトルにSEOスコアを付与

**入力**: `[記事要約]` または `[記事ファイルパス]`

**出力**: タイトル候補（3パターン）

#### 使い方

```bash
/title-gen "パーソナライズ絵本市場が年率10%で成長している。AI技術の進化が..."
/title-gen output/articles/2026-02-12_パーソナライズ絵本市場のトレンド2026.md
```

#### 実装例

```python
# 疑似コード
def title_gen(input_text):
    # 1. 記事要約を取得
    if is_file_path(input_text):
        summary = extract_summary_from_file(input_text)
    else:
        summary = input_text

    # 2. タイトル生成プロンプト
    prompt = f"""
    以下の記事要約から、3パターンのタイトルを生成してください：

    要約: {summary}

    パターン1: 真面目・正統派（データ・事実重視）
    パターン2: キャッチー（読者の興味を引く）
    パターン3: SEO重視（検索されやすいキーワードを含む）

    各タイトルは50文字以内。
    """

    # 3. 生成
    titles = claude_api.generate(prompt)

    # 4. SEOスコア計算
    for title in titles:
        title['seo_score'] = calculate_seo_score(title['text'])

    return titles
```

---

### 6. /cover-image-prompt

#### 概要
- **目的**: カバー画像生成用のプロンプト生成
- **実行タイミング**: 手動実行
- **処理時間**: 約30秒

#### 機能仕様

**実行内容**:
1. 記事タイトルまたは要約を受け取る
2. 画像生成AIプロンプトを生成（Midjourney、DALL-E、Stable Diffusion対応）
3. スタイル・構図・色調を提案

**入力**: `[記事タイトル]` または `[記事要約]`

**出力**: 画像生成プロンプト（3パターン）

#### 使い方

```bash
/cover-image-prompt "パーソナライズ絵本市場のトレンド2026"
/cover-image-prompt "AI技術の進化が変える絵本制作の未来"
```

#### 実装例

```python
# 疑似コード
def cover_image_prompt(input_text):
    # 1. プロンプト生成
    prompt = f"""
    以下の記事タイトルに合うカバー画像のプロンプトを生成してください：

    タイトル: {input_text}

    要件:
    - Midjourney、DALL-E、Stable Diffusionで使用可能
    - プロフェッショナルで視覚的に魅力的
    - 記事の内容を的確に表現
    - 16:9または1:1のアスペクト比

    3パターン生成:
    - パターン1: イラスト風
    - パターン2: 写真風
    - パターン3: グラフィック風
    """

    # 2. 生成
    prompts = claude_api.generate(prompt)

    return prompts
```

---

## 実装の優先順位

### フェーズ1（優先度：高）- 2026年2月〜3月（4週間）

**目標**: コア機能の実装と動作確認

#### 週1（2026-02-12〜02-18）
- [x] Notion MCP 設定
- [ ] Google Sheets MCP 設定
- [ ] Grok API（X/Twitter）設定
- [ ] `/meta-trend-daily` スキル実装（基本版）

#### 週2（2026-02-19〜02-25）
- [ ] Slack MCP 設定
- [ ] `/meta-trend-daily` スキルとNotionの連携
- [ ] `/digest` スキル実装
- [ ] cron設定（meta-trend-daily自動実行）

#### 週3（2026-02-26〜03-04）
- [ ] Gemini API 設定
- [ ] `/gemini-write` スキル実装
- [ ] `/title-gen` スキル実装
- [ ] `/cover-image-prompt` スキル実装

#### 週4（2026-03-05〜03-11）
- [ ] `/media-mix-weekly` スキル実装
- [ ] Google Sheetsとの連携
- [ ] cron設定（media-mix-weekly自動実行）
- [ ] フェーズ1の動作確認・バグ修正

**成果物**:
- トレンド自動収集の仕組み（毎日実行）
- 記事執筆の効率化（Gemini API活用）
- X投稿分析の自動化（毎週実行）

---

### フェーズ2（優先度：中）- 2026年3月〜4月（4週間）

**目標**: 高度な機能の実装と統合

#### 週5-6（2026-03-12〜03-25）
- [ ] GitHub MCP 設定
- [ ] Figma MCP 設定
- [ ] タスク管理の自動化（Notion ↔ GitHub連携）
- [ ] デザインレビューの自動化

#### 週7-8（2026-03-26〜04-08）
- [ ] Playwright MCP 設定
- [ ] 競合サイトのスクレイピング自動化
- [ ] Web UIテストの自動化
- [ ] フェーズ2の動作確認・バグ修正

**成果物**:
- タスク管理の自動化
- デザインレビューの効率化
- 競合分析の自動化

---

### フェーズ3（優先度：低）- 2026年4月〜5月（4週間）

**目標**: 最適化と運用改善

#### 週9-10（2026-04-09〜04-22）
- [ ] スキルの最適化（速度、精度）
- [ ] エラーハンドリングの強化
- [ ] ログ・モニタリングの整備
- [ ] ドキュメント整備

#### 週11-12（2026-04-23〜05-06）
- [ ] ユーザーフィードバックの収集
- [ ] 改善実装
- [ ] 最終動作確認
- [ ] プロジェクト完了

**成果物**:
- 安定稼働するシステム
- 完全なドキュメント
- 運用マニュアル

---

## スケジュール案

### ガントチャート

```
タスク                        2月    3月    4月    5月
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【フェーズ1: コア機能】
Notion MCP                   ████
Google Sheets MCP            ████
Grok API                     ████
Slack MCP                    ████
/meta-trend-daily            ████████
/digest                        ████████
Gemini API                       ████
/gemini-write                    ████████
/title-gen                         ████
/cover-image-prompt                ████
/media-mix-weekly                    ████
動作確認・バグ修正                     ████

【フェーズ2: 高度な機能】
GitHub MCP                           ████
Figma MCP                            ████
タスク管理自動化                       ████████
デザインレビュー自動化                   ████████
Playwright MCP                           ████████
スクレイピング自動化                       ████████
動作確認・バグ修正                           ████

【フェーズ3: 最適化】
スキル最適化                                 ████████
エラーハンドリング                             ████████
ログ・モニタリング                               ████████
ドキュメント整備                                 ████████
改善実装                                           ████
最終確認                                           ████
```

---

## リスクと対策

### リスク1: API利用料金の超過

**リスク内容**:
- Grok API、Gemini APIの利用料金が予想を超える可能性

**対策**:
- 各APIの月間予算を設定（Grok: 5,000円、Gemini: 10,000円）
- 利用量のモニタリング（毎週確認）
- 予算超過時のアラート設定
- 無料枠の活用（Gemini: 月60回まで無料）

### リスク2: MCP設定の複雑さ

**リスク内容**:
- 6つのMCP設定が複雑で、設定ミスの可能性

**対策**:
- 1つずつ段階的に設定
- 各MCPの動作確認を徹底
- 設定ドキュメントの整備
- トラブルシューティングガイドの作成

### リスク3: 自動実行の失敗

**リスク内容**:
- cron設定の失敗により、スキルが自動実行されない

**対策**:
- cron実行ログの記録
- 失敗時のSlack通知
- 手動実行のバックアップ手順
- ヘルスチェック（毎朝確認）

### リスク4: データの誤り・漏れ

**リスク内容**:
- トレンド収集、記事執筆で誤った情報を含む可能性

**対策**:
- 人間によるレビュープロセス
- 情報源の信頼性チェック
- 重要な情報は必ず確認
- 免責事項の明記

### リスク5: 開発期間の遅延

**リスク内容**:
- 3ヶ月で完了できない可能性

**対策**:
- 優先順位の明確化（フェーズ1を最優先）
- 週次進捗確認
- 必要に応じてスコープ調整
- バッファ期間の確保（各フェーズ末に1週間）

---

## 次のステップ

### 今すぐ実行すべきこと

1. **Notion Integration の作成**（今日中）
   - https://www.notion.so/my-integrations
   - 「記事ネタ帳」データベースの作成

2. **Google Cloud Project の作成**（今週中）
   - https://console.cloud.google.com/
   - サービスアカウントの作成
   - 「経理管理」スプレッドシートの作成

3. **Grok API（X Developer Account）の申請**（今週中）
   - https://developer.x.com/
   - 承認に数日かかる可能性があるため、早めに申請

4. **Gemini API Keyの取得**（今日中）
   - https://makersuite.google.com/app/apikey
   - すぐに取得可能

### 今週の目標

- [ ] Notion MCP 設定完了
- [ ] Google Sheets MCP 設定完了
- [ ] Grok API 設定完了
- [ ] `/meta-trend-daily` スキル実装開始

---

**作成者**: Claude (AI経営パートナー)
**最終更新**: 2026-02-12
**バージョン**: 1.0
