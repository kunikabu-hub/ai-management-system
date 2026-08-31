# 1日実装プラン - システム拡張

**実施日**: 2026-02-12（水）
**作業時間**: 9:00〜21:00（12時間、休憩含む）
**目標**: MCP連携6つ + API2つ + スキル6つ = 全機能実装

---

## 📋 1日のタイムライン

### 午前（9:00〜12:00）- 3時間：認証情報取得とMCP設定

#### 9:00-9:30（30分）- 準備・確認
- [ ] 設計書の再確認
- [ ] 必要なツールのインストール確認
  - Node.js、npm、Python3、pip
- [ ] 作業ディレクトリの整理

#### 9:30-10:00（30分）- Notion Integration
- [ ] https://www.notion.so/my-integrations で Integration作成
- [ ] 「記事ネタ帳」データベース作成
- [ ] Integration Token取得
- [ ] MCP設定ファイル編集
- [ ] 動作確認

#### 10:00-10:30（30分）- Google Sheets
- [ ] Google Cloud Console でプロジェクト作成
- [ ] Google Sheets API有効化
- [ ] サービスアカウント作成
- [ ] 「経理管理」スプレッドシート作成
- [ ] サービスアカウント共有
- [ ] MCP設定ファイル編集
- [ ] 動作確認

#### 10:30-11:00（30分）- Slack
- [ ] https://api.slack.com/apps でSlack App作成
- [ ] 権限設定（chat:write、channels:read）
- [ ] ワークスペースにインストール
- [ ] Bot Token取得
- [ ] チャンネル招待（#ai-notifications）
- [ ] MCP設定ファイル編集
- [ ] 動作確認

#### 11:00-11:30（30分）- API設定（Gemini、Grok）
- [ ] Gemini API Key取得（https://makersuite.google.com/app/apikey）
- [ ] Grok API申請開始（https://developer.x.com/）
  - **注意**: 承認に時間がかかる可能性。代替案として既存のTwitter APIを使用
- [ ] 環境変数設定（~/.bashrc or ~/.zshrc）
- [ ] 動作確認

#### 11:30-12:00（30分）- GitHub、Figma、Playwright
- [ ] GitHub Personal Access Token取得
- [ ] Figma Personal Access Token取得
- [ ] Playwright インストール（`npm install -g playwright`）
- [ ] MCP設定ファイル編集
- [ ] 動作確認

---

### 昼休憩（12:00〜13:00）- 1時間

---

### 午後前半（13:00〜17:00）- 4時間：スキル実装

#### 13:00-14:00（60分）- /meta-trend-daily スキル
- [ ] `.claude/commands/meta-trend-daily.md` 作成
- [ ] 実装内容：
  - Web検索でトレンド収集
  - カテゴリ分類
  - Notion保存
  - Slack通知
  - ファイル保存
- [ ] 動作確認
- [ ] cron設定（毎日9:00実行）

#### 14:00-14:45（45分）- /digest スキル
- [ ] `.claude/commands/digest.md` 作成
- [ ] 実装内容：
  - トピック関連情報収集
  - 分析・要約
  - レポート生成
  - ファイル保存
- [ ] 動作確認

#### 14:45-15:30（45分）- /gemini-write スキル
- [ ] `.claude/commands/gemini-write.md` 作成
- [ ] 実装内容：
  - 関連資料収集
  - Gemini APIで記事生成
  - ファイル保存
- [ ] 動作確認

#### 15:30-16:00（30分）- /title-gen スキル
- [ ] `.claude/commands/title-gen.md` 作成
- [ ] 実装内容：
  - 記事要約から3パターンのタイトル生成
  - SEOスコア計算
- [ ] 動作確認

#### 16:00-16:30（30分）- /cover-image-prompt スキル
- [ ] `.claude/commands/cover-image-prompt.md` 作成
- [ ] 実装内容：
  - 記事タイトルから画像プロンプト生成（3パターン）
- [ ] 動作確認

#### 16:30-17:00（30分）- /media-mix-weekly スキル
- [ ] `.claude/commands/media-mix-weekly.md` 作成
- [ ] 実装内容：
  - X投稿パフォーマンス分析
  - Google Sheets記録
  - Slack通知
  - レポート生成
- [ ] cron設定（毎週月曜9:00実行）

---

### 休憩（17:00〜17:30）- 30分

---

### 午後後半（17:30〜21:00）- 3.5時間：統合テスト・最適化・ドキュメント

#### 17:30-18:30（60分）- 統合テスト
- [ ] 全スキルの動作確認
- [ ] MCP連携の動作確認
- [ ] エラーハンドリングの確認
- [ ] ログ出力の確認

#### 18:30-19:30（60分）- 実戦テスト
- [ ] `/meta-trend-daily` を実際に実行してトレンド収集
- [ ] `/gemini-write` で記事作成
- [ ] `/title-gen` でタイトル生成
- [ ] `/cover-image-prompt` でプロンプト生成
- [ ] 結果をNotionに保存
- [ ] Slackに通知

#### 19:30-20:30（60分）- ドキュメント整備
- [ ] 各スキルのREADME作成
- [ ] トラブルシューティングガイド作成
- [ ] 運用マニュアル作成
- [ ] CLAUDE.mdの更新

#### 20:30-21:00（30分）- 最終確認・振り返り
- [ ] チェックリストの確認
- [ ] 動作確認
- [ ] 次のステップの確認
- [ ] 振り返り・メモ

---

## 🎯 実装のコツ

### 効率化のポイント

1. **並列作業**
   - 認証情報の取得は待ち時間が発生するため、先に全部申請
   - 承認待ちの間に他の作業を進める

2. **テンプレート活用**
   - 既存スキル（daily-schedule、trend-check、write-draft）をコピーして改変
   - 実装時間を50%削減

3. **段階的確認**
   - 1つ実装したら必ず動作確認
   - 後から一括デバッグは時間がかかる

4. **最小実装**
   - 最初は最小限の機能で実装
   - 動作確認後に機能追加

5. **エラーハンドリングは後回し**
   - 基本機能を優先
   - エラーハンドリングは統合テスト時に追加

---

## 📝 チェックリスト

### 認証情報取得（午前）

#### Notion
- [ ] Integration作成
- [ ] データベース作成（記事ネタ帳）
- [ ] Integration Token取得
- [ ] データベースID取得
- [ ] Connection追加

#### Google Sheets
- [ ] GCPプロジェクト作成
- [ ] API有効化
- [ ] サービスアカウント作成
- [ ] キー（JSON）ダウンロード
- [ ] スプレッドシート作成
- [ ] 共有設定

#### Slack
- [ ] Slack App作成
- [ ] 権限設定
- [ ] インストール
- [ ] Bot Token取得
- [ ] チャンネル招待

#### GitHub
- [ ] Personal Access Token作成
- [ ] リポジトリ確認

#### Figma
- [ ] Personal Access Token作成
- [ ] ファイルKey確認

#### Playwright
- [ ] インストール
- [ ] ブラウザインストール

#### Gemini API
- [ ] API Key取得

#### Grok API
- [ ] Developer Account申請
  - **代替**: 既存Twitter API使用

### MCP設定（午前）

- [ ] ~/.claude/mcp.json 編集
- [ ] 環境変数設定（~/.bashrc or ~/.zshrc）
- [ ] source ~/.bashrc（または ~/.zshrc）
- [ ] 各MCP動作確認

### スキル実装（午後前半）

- [ ] /meta-trend-daily
- [ ] /digest
- [ ] /gemini-write
- [ ] /title-gen
- [ ] /cover-image-prompt
- [ ] /media-mix-weekly

### cron設定

- [ ] meta-trend-daily（毎日9:00）
- [ ] media-mix-weekly（毎週月曜9:00）

### テスト（午後後半）

- [ ] 全スキル動作確認
- [ ] MCP連携確認
- [ ] 実戦テスト
- [ ] エラーハンドリング

### ドキュメント

- [ ] README更新
- [ ] トラブルシューティング
- [ ] 運用マニュアル
- [ ] CLAUDE.md更新

---

## 🚀 実装の優先順位（時間が足りない場合）

### 最優先（必ず実装）

1. **Notion MCP** - 記事ネタ帳の連携
2. **/meta-trend-daily** - トレンド自動収集
3. **/gemini-write** - 記事執筆の効率化
4. **Gemini API** - 記事生成

### 次に優先

5. **Slack MCP** - 通知
6. **/title-gen** - タイトル生成
7. **Google Sheets MCP** - データ記録

### 余裕があれば

8. **/digest** - トピック分析
9. **/cover-image-prompt** - 画像プロンプト
10. **/media-mix-weekly** - X投稿分析
11. **GitHub MCP** - Issue管理
12. **Figma MCP** - デザインレビュー
13. **Playwright MCP** - Web自動化
14. **Grok API** - X/Twitter連携

---

## 💡 トラブルシューティング

### よくある問題と対処法

#### 問題1: Notion Integration Tokenが無効

**対処法**:
```bash
# 1. Tokenが正しくコピーされているか確認
echo $NOTION_API_KEY

# 2. Integration がデータベースにConnectionされているか確認
# Notionのデータベース > "..." > "Connections" で確認
```

#### 問題2: Google Sheets APIが動作しない

**対処法**:
```bash
# 1. API が有効化されているか確認
# GCP Console > "APIとサービス" > "有効なAPI" で確認

# 2. サービスアカウントキーのパスが正しいか確認
echo $GOOGLE_APPLICATION_CREDENTIALS

# 3. スプレッドシートが共有されているか確認
# スプレッドシート > "共有" でサービスアカウントのメールを確認
```

#### 問題3: Slackに投稿できない

**対処法**:
```bash
# 1. Bot Tokenが正しいか確認
echo $SLACK_BOT_TOKEN

# 2. チャンネルIDが正しいか確認
echo $SLACK_CHANNEL_ID

# 3. Bot がチャンネルに招待されているか確認
# Slack > チャンネル > "Integrations" で確認
```

#### 問題4: Gemini APIがエラー

**対処法**:
```bash
# 1. API Keyが正しいか確認
echo $GEMINI_API_KEY

# 2. 利用枠を確認
# https://makersuite.google.com/ でクォータを確認

# 3. モデル名が正しいか確認
# 'gemini-pro' または 'gemini-pro-vision'
```

#### 問題5: cronが実行されない

**対処法**:
```bash
# 1. cronの設定を確認
crontab -l

# 2. cronのログを確認
tail -f /var/log/cron

# 3. 絶対パスを使用しているか確認
# NG: claude run meta-trend-daily
# OK: /usr/local/bin/claude run meta-trend-daily
```

---

## 🎬 実装開始コマンド

### 1. 環境確認

```bash
# Node.js確認
node --version  # v18以上

# Python確認
python3 --version  # 3.9以上

# pip確認
pip3 --version
```

### 2. 必要なパッケージインストール

```bash
# Playwright
npm install -g playwright
npx playwright install

# Python パッケージ（必要に応じて）
pip3 install google-generativeai tweepy google-auth google-auth-oauthlib google-auth-httplib2
```

### 3. ディレクトリ確認

```bash
# 作業ディレクトリに移動
cd /Users/attadesign/ai-management-system

# ディレクトリ構造確認
ls -la
```

### 4. 認証情報の保存場所

```bash
# ~/.claude/mcp.json
# ~/.bashrc または ~/.zshrc
# ~/.config/claude-code/ 配下
```

---

## 📊 進捗管理

### 時間管理

| 時刻 | タスク | ステータス |
|------|--------|-----------|
| 09:00 | 準備・確認 | ⬜ |
| 09:30 | Notion | ⬜ |
| 10:00 | Google Sheets | ⬜ |
| 10:30 | Slack | ⬜ |
| 11:00 | API設定 | ⬜ |
| 11:30 | GitHub/Figma/Playwright | ⬜ |
| 12:00 | 昼休憩 | ⬜ |
| 13:00 | /meta-trend-daily | ⬜ |
| 14:00 | /digest | ⬜ |
| 14:45 | /gemini-write | ⬜ |
| 15:30 | /title-gen | ⬜ |
| 16:00 | /cover-image-prompt | ⬜ |
| 16:30 | /media-mix-weekly | ⬜ |
| 17:00 | 休憩 | ⬜ |
| 17:30 | 統合テスト | ⬜ |
| 18:30 | 実戦テスト | ⬜ |
| 19:30 | ドキュメント | ⬜ |
| 20:30 | 最終確認 | ⬜ |
| 21:00 | 完了！ | ⬜ |

### 完了チェック

実装完了の定義：
- [ ] 全6つのMCPが動作する
- [ ] 全6つのスキルが動作する
- [ ] トレンド収集が自動実行される（cron）
- [ ] 記事執筆がGemini APIで可能
- [ ] Notionにデータが保存される
- [ ] Slackに通知が届く
- [ ] ドキュメントが整備されている

---

## 🎉 完了後の確認事項

### 動作確認コマンド

```bash
# 1. トレンド収集
/meta-trend-daily

# 2. 記事執筆
/gemini-write パーソナライズ絵本の未来

# 3. タイトル生成
/title-gen output/articles/2026-02-12_パーソナライズ絵本市場のトレンド2026.md

# 4. トピック分析
/digest AI絵本サービス

# 5. 画像プロンプト
/cover-image-prompt "パーソナライズ絵本市場のトレンド2026"

# 6. X投稿分析（翌週月曜日）
/media-mix-weekly
```

### 自動実行の確認

```bash
# cronの確認
crontab -l

# 期待される出力:
# 0 9 * * * cd /path/to/ai-management-system && /usr/local/bin/claude run meta-trend-daily
# 0 9 * * 1 cd /path/to/ai-management-system && /usr/local/bin/claude run media-mix-weekly
```

### Notionの確認

1. 記事ネタ帳データベースを開く
2. トレンド情報が保存されているか確認
3. カテゴリ、ステータス、タグが正しく設定されているか確認

### Slackの確認

1. #ai-notifications チャンネルを開く
2. トレンド分析の通知が届いているか確認

---

## 🚀 次のステップ（翌日以降）

### 運用開始

1. **毎日の確認**（5分）
   - Notionの記事ネタ帳を確認
   - Slackの通知を確認
   - 気になるトレンドを深掘り

2. **週次の確認**（30分）
   - X投稿パフォーマンスレポートを確認
   - 改善点を特定
   - 次週の投稿戦略を立てる

3. **記事執筆**（随時）
   - Notionのネタ帳から記事テーマを選択
   - `/gemini-write` で下書き作成
   - `/title-gen` でタイトル生成
   - `/cover-image-prompt` で画像プロンプト生成
   - レビュー・編集後、公開

### 改善・最適化

1. **1週間後**
   - トレンド収集の精度をチェック
   - 不要なトレンドをフィルタリング
   - Notionのタグを整理

2. **1ヶ月後**
   - Gemini APIの利用料金を確認
   - Grok APIの利用状況を確認
   - ROIを評価

3. **3ヶ月後**
   - システム全体の見直し
   - 新機能の追加検討

---

**作成者**: Claude (AI経営パートナー)
**作成日**: 2026-02-12
**想定作業時間**: 12時間（9:00〜21:00）

---

## 💪 準備はいいですか？

それでは、9:00から実装を開始しましょう！

**最初のタスク**: Notion Integrationの作成
→ https://www.notion.so/my-integrations
