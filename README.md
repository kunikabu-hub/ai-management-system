# AI Management System

**えほんインク 事業管理システム**

AIを活用した経営サポート、リサーチ、データ分析のための統合管理システム

---

## 📖 概要

このシステムは、**Claude（AI）を経営パートナー兼リサーチャー**として活用し、事業戦略の立案、市場調査、データ分析、ドキュメント管理を効率化するためのプラットフォームです。

### 🎯 主な機能

- **Google Drive連携**: 資料の自動収集・分析
- **事業データ分析**: ミーティングメモ、企画書の要約・構造化
- **戦略立案サポート**: AI壁打ち、ブレインストーミング
- **ドキュメント管理**: 自動整理、テンプレート化
- **プロジェクト追跡**: 進行中のプロジェクト管理

---

## 🏢 対象事業

**えほんインク（H本育株式会社）**

AIを活用したパーソナライズ絵本サービスを核とし、B2C・B2B両面で事業展開。

- **ビジョン**: 「大切な人との心を私たちのサービスでつぐ」
- **コアサービス**: パーソナライズ絵本、AIナラティブDB
- **主要顧客**: 子育て世代、企業（自動車・住宅・保険業界）

詳細: [output/business_analysis.md](output/business_analysis.md)

---

## 🚀 クイックスタート

### 前提条件

- **Python 3.9以上**
- **Git**
- **Google Drive API認証情報**
- **Claude Code CLI**（推奨）

### セットアップ

#### 1. リポジトリのクローン

GitHubからこのリポジトリをクローンします。HTTPS/SSHのいずれかの方法を選択してください。

##### 方法A: HTTPS（推奨・簡単）

```bash
cd ~/Documents
git clone https://github.com/kunikabu-hub/ai-management-system.git
cd ai-management-system
```

**Private リポジトリの場合**: GitHubのユーザー名とPersonal Access Tokenの入力を求められます。

##### 方法B: SSH（より安全・パスワード不要）

SSH接続を使用すると、毎回パスワードを入力する必要がなくなります。

**SSH鍵の設定手順**:

1. **SSH鍵を生成**（既に持っている場合はスキップ）:
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   # Enterを3回押してデフォルト設定で作成
   ```

2. **SSH鍵をGitHubに登録**:
   ```bash
   # 公開鍵をクリップボードにコピー
   cat ~/.ssh/id_ed25519.pub | pbcopy
   ```

   - https://github.com/settings/keys にアクセス
   - "New SSH key" をクリック
   - タイトルを入力（例: "MacBook Pro"）
   - クリップボードの内容を貼り付け
   - "Add SSH key" をクリック

3. **SSH接続をテスト**:
   ```bash
   ssh -T git@github.com
   # "Hi username! You've successfully authenticated..." と表示されればOK
   ```

4. **リポジトリをクローン**:
   ```bash
   cd ~/Documents
   git clone git@github.com:kunikabu-hub/ai-management-system.git
   cd ai-management-system
   ```

##### 既存のHTTPSをSSHに切り替える

既にHTTPSでクローンしている場合、SSHに切り替えることができます：

```bash
cd ~/ai-management-system
git remote set-url origin git@github.com:kunikabu-hub/ai-management-system.git
git remote -v  # 確認
```

#### 2. 依存関係のインストール

```bash
cd ai-management-system
pip install -r requirements.txt
```

#### 3. Google Drive認証の設定

詳細は [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) を参照

```bash
# 1. credentials.jsonを配置
mkdir -p ~/.config/claude-code/gdrive/
cp /path/to/credentials.json ~/.config/claude-code/gdrive/

# 2. OAuth2トークンを取得
python3 tools/get_google_drive_token.py
```

#### 4. 動作確認

```bash
# ファイル一覧を取得
./tools/show_drive_files.sh 10
```

---

## 📁 ディレクトリ構造

```
ai-management-system/
├── README.md                    # このファイル
├── CLAUDE.md                    # Claudeへの永続的指示
├── DAILY.md                     # 日次ログ・メモ
├── requirements.txt             # Python依存関係
│
├── 00_context/                  # コンテキスト情報
│   ├── memories/                # 重要な記憶・メモ
│   └── portfolio/               # ポートフォリオ・実績
│
├── 01_strategy/                 # 戦略・計画
├── 03_projects/                 # プロジェクト管理
├── 04_content/                  # コンテンツ・資料
├── 05_learning/                 # 学習・ナレッジ
│
├── output/                      # 生成された成果物
│   ├── business_analysis.md    # 事業概要分析
│   ├── google_drive_files.json # Driveファイル一覧
│   └── slides/                  # エクスポートされたスライド
│
└── tools/                       # Google Drive連携ツール
    ├── README.md                # ツールの使い方
    ├── get_google_drive_token.py
    ├── show_drive_files.sh
    └── export_google_slides.sh
```

### ディレクトリの用途

| ディレクトリ | 用途 |
|------------|------|
| `00_context/` | 長期的なコンテキスト、重要な意思決定の記録 |
| `01_strategy/` | 事業戦略、マーケティング計画 |
| `03_projects/` | 個別プロジェクトのドキュメント |
| `04_content/` | 企画書、提案資料 |
| `05_learning/` | 業界知識、ベストプラクティス |
| `output/` | AIが生成した分析レポート、成果物 |
| `tools/` | Google Drive連携スクリプト |

詳細: [CLAUDE.md](CLAUDE.md)

---

## 💡 使い方

### Google Driveからファイルを取得

```bash
# ファイル一覧を表示（50件）
./tools/show_drive_files.sh 50

# 結果はoutput/google_drive_files.jsonに保存される
```

### Google Slidesをエクスポート

```bash
# スライドをテキスト形式でエクスポート
./tools/export_google_slides.sh [file_id] [output_name]

# 例:
./tools/export_google_slides.sh 1i1lE78sPSHJUCDxbF2jW6WS_wnExIlIHcs3k5Hycscg presentation
```

### Claudeとの対話

Claude Code CLIを起動して、以下のように質問できます：

```
# 事業分析
「最新のミーティングメモを分析して、重要なアクションアイテムを抽出してください」

# 戦略立案
「ペット絵本事業の市場調査を行い、競合分析をまとめてください」

# 壁打ち
「ナック社との提携案について、メリット・デメリットを整理してください」
```

詳細: [CLAUDE.md](CLAUDE.md) - Claudeの役割と行動指針

---

## 📊 主要プロジェクト

### 現在進行中

| プロジェクト | 概要 | ステータス | 導入予定 |
|------------|------|----------|---------|
| **鈴木自工** | 購入車両のアバター絵本 | 開発中 | 2026年4月1日 |
| **ナック** | 代理店販売契約 | 検討中 | 2026年2月 |
| **かんぽ生命** | AIナラティブDB実証実験 | 進行中 | - |
| **ペット絵本** | プロトタイプ開発 | 企画中 | 2026年Q3 |

### 過去実績

- ガリバー: 車購入者向けパーソナライズ絵本
- 旭化成ホームズ: 企業向けカスタマイズ絵本

詳細: [output/business_analysis.md](output/business_analysis.md)

---

## 🔧 ツール・スクリプト

### Google Drive連携

| スクリプト | 用途 | 使い方 |
|-----------|------|--------|
| `get_google_drive_token.py` | OAuth2トークン取得 | `python3 tools/get_google_drive_token.py` |
| `show_drive_files.sh` | ファイル一覧表示 | `./tools/show_drive_files.sh [件数]` |
| `export_google_slides.sh` | スライドエクスポート | `./tools/export_google_slides.sh [file_id] [name]` |

詳細: [tools/README.md](tools/README.md)

---

## ⚙️ 設定ファイル

### CLAUDE.md

Claudeへの永続的な指示を記載。役割、事業概要、行動指針などを定義。

**主な内容**:
- Claudeの役割: 経営パートナー兼リサーチャー
- 事業概要: えほんインクのビジョン、サービス、ビジネスモデル
- 行動指針: プロアクティブ、データドリブン、具体的
- 優先順位: 戦略的判断 > 新規企画 > システム最適化

詳細: [CLAUDE.md](CLAUDE.md)

### DAILY.md

日次のログ、メモ、TODO管理に使用。

---

## 📝 ドキュメント

| ファイル | 内容 |
|---------|------|
| [README.md](README.md) | このファイル |
| [CLAUDE.md](CLAUDE.md) | Claudeへの指示・設定 |
| [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) | セットアップ手順 |
| [tools/README.md](tools/README.md) | ツールの使い方 |
| [output/business_analysis.md](output/business_analysis.md) | 事業概要分析 |

---

## 🔐 セキュリティ

### 機密情報の取り扱い

- **認証情報**: `~/.config/claude-code/gdrive/` に保存
- **Gitリポジトリ**: 認証情報をコミットしない
- **共有**: トークンファイルを他人と共有しない

### .gitignore設定（推奨）

```gitignore
# 認証情報
*.json
!requirements.json

# 出力ファイル
output/
*.log

# 環境設定
.env
```

---

## 🐛 トラブルシューティング

### よくある問題

#### 1. `401 Unauthorized` エラー

**解決策**: トークンを再取得
```bash
python3 tools/get_google_drive_token.py
```

#### 2. `403 Forbidden` エラー

**解決策**: Google Drive APIを有効化
- [Google Cloud Console](https://console.cloud.google.com/)
- 「APIとサービス」→「ライブラリ」→「Google Drive API」を有効化

#### 3. スクリプトが実行できない

**解決策**: 実行権限を付与
```bash
chmod +x tools/*.sh
```

詳細: [tools/README.md - トラブルシューティング](tools/README.md#-トラブルシューティング)

---

## 📚 参考資料

### 外部リンク

- [Google Drive API Documentation](https://developers.google.com/drive/api/guides/about-sdk)
- [Claude Code CLI](https://claude.ai/code)
- [OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)

### 内部ドキュメント

- [事業概要分析](output/business_analysis.md)
- [Google Drive連携ツール](tools/README.md)
- [セットアップ手順](SETUP_INSTRUCTIONS.md)

---

## 🛠️ 開発・運用

### システムの更新

```bash
# Python依存関係の更新
pip install -r requirements.txt --upgrade

# トークンの再取得（期限切れの場合）
python3 tools/get_google_drive_token.py
```

### 定期メンテナンス

- **週次**: Google Driveから最新ファイルを取得
- **月次**: 事業分析レポートの更新
- **四半期**: 戦略レビュー、目標設定

---

## 📞 サポート

### 質問・問題報告

- **CLAUDE.md参照**: AIの役割と行動指針
- **tools/README.md参照**: ツールの使い方
- **DAILY.md**: 日次のメモ・TODO

### 改善提案

システムの改善案があれば、DAILY.mdにメモするか、Claudeに相談してください。

---

## 📅 更新履歴

- **2026-02-13**: 主要アップデート
  - 8つのAPI連携完了（Notion、Gemini、OpenAI、Grok、GitHub、Figma、Playwright、Circleback）
  - 4つのスキル実装（agent-memory、daily-schedule、trend-check、write-draft）
  - えほんインク包括的戦略レポート作成（3,097行）
  - Circleback議事録自動連携機能追加
  - SETUP.md作成（他PCでのセットアップガイド）
  - GitHubプライベートリポジトリに保存
  - README.mdにクローン方法・SSH接続手順を追加

- **2026-02-12**: 初版作成
  - Google Drive連携機能の実装
  - 事業概要分析の作成
  - CLAUDE.md設定ファイルの作成
  - ディレクトリ構造の整備

---

## 📄 ライセンス

このシステムは、えほんインク（H本育株式会社）の内部管理用システムです。

---

**最終更新**: 2026年2月13日
