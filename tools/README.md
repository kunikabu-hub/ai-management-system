# Google Drive連携ツール

このディレクトリには、Google Drive APIと連携するためのスクリプトが含まれています。

---

## 📋 含まれるスクリプト

### 1. `get_google_drive_token.py`
Google Drive API用のOAuth2トークンを取得するスクリプト

### 2. `show_drive_files.sh`
Google Driveのファイル一覧を見やすく表示するシェルスクリプト

### 3. `export_google_slides.sh`
Google Slidesをテキスト形式でエクスポートするシェルスクリプト

### 4. `list_google_drive_files.py`
Google Drive APIを使ってファイル一覧を取得するPythonスクリプト

### 5. `list_drive_files_simple.py`
requestsライブラリを使ったシンプル版ファイル一覧取得スクリプト

---

## 🚀 クイックスタート

### 前提条件

1. **Python 3.9以上**がインストールされていること
2. **Google Cloud Project**でGoogle Drive APIが有効化されていること
3. **OAuth2認証情報**が取得済みであること

### セットアップ

#### 1. 依存関係のインストール

プロジェクトルートから実行：

```bash
pip install -r requirements.txt
```

必要なパッケージ：
- `google-auth-oauthlib`
- `google-auth-httplib2`
- `google-api-python-client`
- `requests`

#### 2. OAuth2認証の設定

認証情報ファイルを配置：

```bash
# 認証情報ディレクトリを作成
mkdir -p ~/.config/claude-code/gdrive/

# credentials.jsonを配置
# Google Cloud Consoleからダウンロードした認証情報を配置
cp /path/to/your/credentials.json ~/.config/claude-code/gdrive/
```

#### 3. トークンの取得

初回のみ、OAuth2トークンを取得：

```bash
cd /path/to/ai-management-system
python3 tools/get_google_drive_token.py
```

ブラウザが開くので、Googleアカウントでログインし、アクセスを承認してください。

---

## 📖 各スクリプトの使用方法

### `get_google_drive_token.py`

**用途**: OAuth2リフレッシュトークンの取得

**使い方**:
```bash
python3 tools/get_google_drive_token.py
```

**実行結果**:
- ブラウザが開き、Google認証画面が表示される
- 認証後、リフレッシュトークンが `~/.config/claude-code/gdrive/token.json` に保存される
- トークン情報がターミナルに表示される

**トラブルシューティング**:
- **エラー: 認証情報ファイルが見つかりません**
  - `~/.config/claude-code/gdrive/credentials.json` が存在するか確認
  - Google Cloud Consoleから再度ダウンロード

- **ブラウザが開かない**
  - 手動でターミナルに表示されたURLを開く

---

### `show_drive_files.sh`

**用途**: Google Driveのファイル一覧を見やすく表示

**使い方**:
```bash
# プロジェクトルートから実行
./tools/show_drive_files.sh [取得件数]

# 例: 50件のファイルを取得
./tools/show_drive_files.sh 50

# 例: デフォルト（50件）
./tools/show_drive_files.sh
```

**実行結果**:
```
================================================================================
Google Drive ファイル一覧
================================================================================

Google Drive APIに接続中...
✅ 取得件数: 50 件

名前                                       タイプ                  更新日時                 サイズ
-----------------------------------------------------------------------------------------------
NanoBanana用 プロンプト集ORG　X                  📊 スプレッドシート           2026-02-12 04:37     10.0 MB
履歴事項全部証明書_えほんインク20260212.pdf             📕 PDF                2026-02-12 02:43     3.4 MB
...
```

**出力ファイル**:
- `output/google_drive_files.json`: ファイル一覧の詳細情報（JSON形式）

---

### `export_google_slides.sh`

**用途**: Google Slidesをテキスト形式でエクスポート

**使い方**:
```bash
# プロジェクトルートから実行
./tools/export_google_slides.sh [file_id] [output_name]

# 例:
./tools/export_google_slides.sh 1i1lE78sPSHJUCDxbF2jW6WS_wnExIlIHcs3k5Hycscg my_presentation
```

**パラメータ**:
- `file_id`: Google SlidesのファイルID（URLから取得）
- `output_name`: 出力ファイル名（省略可）

**ファイルIDの取得方法**:
Google SlidesのURL:
```
https://docs.google.com/presentation/d/1i1lE78sPSHJUCDxbF2jW6WS_wnExIlIHcs3k5Hycscg/edit
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                      この部分がファイルID
```

**出力ファイル**:
- `output/slides/[output_name].txt`: エクスポートされたテキストファイル

**実行結果**:
```
================================================================================
Google Slides エクスポート
================================================================================
ファイルID: 1i1lE78sPSHJUCDxbF2jW6WS_wnExIlIHcs3k5Hycscg

ファイル情報を取得中...
ファイル名: people_forest_service_202602
タイプ: application/vnd.google-apps.presentation

テキスト形式でエクスポート中...
✅ エクスポート成功: output/slides/my_presentation.txt
```

---

### `list_google_drive_files.py`

**用途**: Google Drive APIを使ってファイル一覧を取得（Python版）

**使い方**:
```bash
python3 tools/list_google_drive_files.py [取得件数]

# 例:
python3 tools/list_google_drive_files.py 100
```

**注意**:
- このスクリプトは `httplib2` を使用しているため、環境によってはタイムアウトする可能性があります
- タイムアウトが発生する場合は、`list_drive_files_simple.py` または `show_drive_files.sh` を使用してください

---

### `list_drive_files_simple.py`

**用途**: requestsライブラリを使ったシンプル版ファイル一覧取得

**使い方**:
```bash
python3 tools/list_drive_files_simple.py [取得件数]

# 例:
python3 tools/list_drive_files_simple.py 50
```

**特徴**:
- `requests` ライブラリを使用（より安定）
- タイムアウト設定が適切
- `httplib2` の問題を回避

---

## 🔧 トラブルシューティング

### 共通の問題

#### 1. `401 Unauthorized` エラー

**原因**: トークンの有効期限切れ

**解決策**:
```bash
# トークンを再取得
python3 tools/get_google_drive_token.py
```

#### 2. `403 Forbidden` エラー

**原因**: Google Drive APIが有効化されていない

**解決策**:
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを選択
3. 「APIとサービス」→「ライブラリ」
4. 「Google Drive API」を検索して有効化

#### 3. `404 Not Found` エラー

**原因**:
- ファイルIDが間違っている
- ファイルへのアクセス権限がない
- 共有ファイルで、自分のDriveにコピーされていない

**解決策**:
- ファイルIDを確認
- ファイルの共有設定を確認
- 共有ファイルの場合は、自分のDriveにコピーする

#### 4. タイムアウトエラー

**原因**: ネットワーク接続の問題、またはライブラリの問題

**解決策**:
- `list_drive_files_simple.py` または `show_drive_files.sh` を使用
- ネットワーク接続を確認

---

## 📝 設定ファイルの場所

### 認証情報
```
~/.config/claude-code/gdrive/
├── credentials.json       # OAuth2クライアント認証情報
└── token.json            # アクセストークン・リフレッシュトークン
```

### 出力ファイル
```
ai-management-system/output/
├── google_drive_files.json    # ファイル一覧（JSON）
└── slides/                    # エクスポートされたスライド
    ├── presentation1.txt
    └── presentation2.txt
```

---

## 🔐 セキュリティ注意事項

1. **認証情報の保護**:
   - `credentials.json` と `token.json` は機密情報です
   - Gitリポジトリにコミットしないでください
   - 他人と共有しないでください

2. **トークンの有効期限**:
   - アクセストークン: 約1時間
   - リフレッシュトークン: 無期限（手動で取り消さない限り）

3. **APIクォータ**:
   - Google Drive APIには利用制限があります
   - 大量のリクエストを送信する場合は注意してください

---

## 💡 ヒント

### ファイル一覧から特定のファイルを検索

```bash
# JSONファイルから「えほん」を含むファイルを検索
cat output/google_drive_files.json | python3 -c "
import sys, json
files = json.load(sys.stdin)
for f in files:
    if 'えほん' in f['name']:
        print(f['name'], '->', f['id'])
"
```

### 複数のスライドを一括エクスポート

```bash
# ファイルIDのリストを作成
FILE_IDS=(
  "1i1lE78sPSHJUCDxbF2jW6WS_wnExIlIHcs3k5Hycscg"
  "1aD54lcuh9qVUhxnqZY2dk9-ePbFHzqybx0aUGMlKC8M"
)

# 一括エクスポート
for id in "${FILE_IDS[@]}"; do
  ./tools/export_google_slides.sh "$id"
done
```

---

## 📚 参考資料

- [Google Drive API Documentation](https://developers.google.com/drive/api/guides/about-sdk)
- [OAuth 2.0 for Client-side Web Applications](https://developers.google.com/identity/protocols/oauth2/javascript-implicit-flow)
- [プロジェクトルートのREADME.md](../README.md)
- [CLAUDE.md](../CLAUDE.md) - AI Management Systemの設定

---

**更新日**: 2026年2月12日
