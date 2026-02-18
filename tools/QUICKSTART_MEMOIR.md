# 🚀 クイックスタートガイド - 自分史インタビューAPI

## 5分で始める

### 1. OpenAI APIキーを設定

```bash
export OPENAI_API_KEY="sk-..."
```

または、`.env`ファイルに追加：

```bash
echo 'OPENAI_API_KEY=sk-...' >> ~/.bashrc
source ~/.bashrc
```

### 2. 依存関係をインストール

```bash
cd /Users/attadesign/Documents/ai-management-system
pip install -r requirements.txt
```

### 3. サーバーを起動

```bash
cd tools
./start_memoir_api.sh
```

または、直接起動：

```bash
cd tools
python memoir_editor_api.py
```

起動したら、ブラウザで http://localhost:8000/docs を開いて動作確認。

---

## 使い方

### 方法1: テストクライアントを使う（推奨）

```bash
cd tools
python test_memoir_api.py
```

メニューから選択：
- **1. 対話形式インタビュー**: 手動で質問に答えながら進める
- **2. 自動テストフロー**: サンプルデータで全工程を一気に実行

### 方法2: curlで直接叩く

#### インタビュー開始

```bash
curl -X POST http://localhost:8000/interview \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "message": "自分史を作りたいです",
    "mode": "interview",
    "project_type": "memoir"
  }'
```

#### 質問に答える（繰り返す）

```bash
curl -X POST http://localhost:8000/interview \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user001",
    "message": "幼少期は東京で育ちました",
    "mode": "interview",
    "project_type": "memoir"
  }'
```

#### 素材生成

```bash
curl http://localhost:8000/materials/user001 | jq . > materials.json
```

#### 自分史生成

```bash
curl http://localhost:8000/generate_story/user001 | jq . > story.json
```

#### 絵本生成

```bash
curl "http://localhost:8000/generate_picturebook/user001?page_count=36" | jq . > picturebook.json
```

---

## 動作確認

### ヘルスチェック

```bash
curl http://localhost:8000/
```

レスポンス例：
```json
{
  "service": "Memoir Editor AI API",
  "version": "1.0.0",
  "endpoints": [...]
}
```

### Swagger UIで確認

ブラウザで http://localhost:8000/docs を開く。
すべてのエンドポイントを視覚的にテストできます。

---

## ファイル構成

```
tools/
├── memoir_editor_api.py          # APIサーバー本体
├── test_memoir_api.py            # テストクライアント
├── start_memoir_api.sh           # 起動スクリプト
├── README_MEMOIR_API.md          # 詳細ドキュメント
├── QUICKSTART_MEMOIR.md          # このファイル
└── sessions/                     # セッションデータ（自動生成）
    ├── user001.json
    └── ...

output/
├── user001_materials.json        # 構造化素材
├── user001_story.json            # 自分史
└── user001_picturebook.json      # 絵本
```

---

## トラブルシューティング

### ❌ "OPENAI_API_KEY not found"

```bash
export OPENAI_API_KEY="sk-..."
```

### ❌ "ModuleNotFoundError: No module named 'fastapi'"

```bash
pip install -r requirements.txt
```

### ❌ "Address already in use"

ポート8000が使用中。別のポートで起動：

```bash
uvicorn memoir_editor_api:app --port 8001
```

### ❌ JSONパースエラー

- GPT-4 Turbo以降のモデルを使用しているか確認
- `memoir_editor_api.py`の`MODEL_NAME`を確認

---

## 次のステップ

1. **詳細ドキュメント**: `README_MEMOIR_API.md` を参照
2. **カスタマイズ**: `memoir_editor_api.py`のシステムプロンプトやスキーマを調整
3. **PDF出力**: 将来的に実装予定（ReportLabなど）
4. **AI画像生成**: DALL-E統合（OpenAI Images API）
5. **Web UI**: React/Vueで対話型インターフェース構築

---

## 参考リンク

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Structured Outputs Guide](https://platform.openai.com/docs/guides/structured-outputs)

---

## サポート

質問・バグ報告:
- プロジェクト管理ツール
- 社内Slack
- GitHub Issues（将来的に）

---

**Happy Storytelling! 📖✨**
