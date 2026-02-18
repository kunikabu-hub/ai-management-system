# 自分史インタビュー&編集者AI - API仕様書

## 概要

このAPIは、ユーザーとの対話を通じて人生エピソードを収集し、自分史（小説風）と自分史絵本（短文＋挿絵指示）を生成するシステムです。

## 特徴

- **丁寧なインタビュー**: 事実・感情・意味を段階的に引き出す
- **構造化素材生成**: 年表、人物、エピソード、テーマを整理
- **2種類の出力**: 小説風自分史 + 絵本版（ページ割＋挿絵プロンプト）
- **文体制御**: です・ます調、断定過多を避け、温かみのある語り口
- **事実尊重**: 推測や捏造を避け、不足情報は質問で補完

## 技術スタック

- **FastAPI**: REST APIフレームワーク
- **OpenAI GPT-4**: Structured Outputs対応
- **ファイルベースストレージ**: セッション管理（JSON）

---

## セットアップ

### 1. 依存関係インストール

```bash
pip install fastapi uvicorn openai pydantic
```

### 2. OpenAI APIキー設定

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. サーバー起動

```bash
cd tools
python memoir_editor_api.py
```

または

```bash
uvicorn memoir_editor_api:app --reload --host 0.0.0.0 --port 8000
```

### 4. 動作確認

ブラウザで `http://localhost:8000/docs` を開くとSwagger UIでAPIを確認できます。

---

## APIエンドポイント

### 1. `POST /interview`

ユーザーとの対話を進める。次の質問または要約確認を返す。

**リクエスト例**:
```json
{
  "user_id": "user123",
  "message": "はじめまして。自分史を作りたいです。",
  "mode": "interview",
  "project_type": "memoir"
}
```

**レスポンス例**:
```json
{
  "reply": "はじめまして！自分史作りをお手伝いさせていただきます。\n\nこれから10問程度の質問をさせていただきます。所要時間は15〜30分ほどです。\n\nまず最初の質問です。人生を3つの章に分けるなら、「いつ頃」「何がテーマ」になりそうですか？",
  "message_count": 2
}
```

**パラメータ**:
- `user_id`: ユーザー識別子（セッション管理用）
- `message`: ユーザーの発言
- `mode`: `interview` または `edit`
- `project_type`: `memoir` または `picturebook`

---

### 2. `GET /materials/{user_id}`

会話ログから構造化素材（materials.json）を生成。

**リクエスト例**:
```bash
curl http://localhost:8000/materials/user123
```

**レスポンス例**:
```json
{
  "profile": {
    "name_display": "田中太郎",
    "birth_year_approx": 1960,
    "current_age_approx": 66,
    "region": "東京都",
    "reader_intent": "孫たちに自分の歩みを伝えたい"
  },
  "timeline": [
    {
      "period": "小学校低学年（1966年頃）",
      "event": "初めて自転車に乗れた日",
      "place": "実家近くの公園",
      "people_involved": ["父"],
      "emotion": "誇らしさと嬉しさ",
      "meaning": "挑戦することの大切さを学んだ"
    }
  ],
  "people": [
    {
      "name": "父",
      "relation": "父親",
      "role_in_story": "厳しくも優しい存在",
      "key_memory": "自転車の練習を根気強く付き合ってくれた"
    }
  ],
  "episodes": [...],
  "themes": ["家族", "挑戦", "仕事観", "誇り"],
  "voice_style": {
    "base_style": "です・ます調",
    "allowed_variants": ["〜なのです", "〜のです", "〜かもしれません"],
    "forbidden": ["である調", "説教口調", "過度な教訓"]
  },
  "open_questions": [
    "学生時代の具体的なエピソードをもう1つ教えていただけますか？"
  ]
}
```

---

### 3. `GET /generate_story/{user_id}`

materials.jsonから自分史（小説風）を生成。

**リクエスト例**:
```bash
curl http://localhost:8000/generate_story/user123
```

**レスポンス例**:
```json
{
  "title": "歩んできた道 〜ある技術者の物語〜",
  "subtitle": "家族とともに",
  "author": "田中太郎",
  "chapters": [
    {
      "chapter_number": 1,
      "title": "小さな自転車と大きな一歩",
      "body": "昭和四十一年、春の午後のことでした。実家近くの公園で、私は初めて自転車に乗ることができたのです。父が後ろで支えてくれていたことに気づかず、一人で漕いでいたあの瞬間の感動は、今でも忘れられません。\n\n転んでは起き、泣いては笑い、何度も挑戦したあの日々。父は一度も急かすことなく、ただ黙って見守ってくれていました。その優しさと厳しさが、後の人生で困難に直面したときの支えになっていたのかもしれません。..."
    }
  ]
}
```

---

### 4. `GET /generate_picturebook/{user_id}?page_count=36`

materials.jsonから自分史絵本を生成。

**パラメータ**:
- `page_count`: ページ数（12〜48、デフォルト36）

**リクエスト例**:
```bash
curl "http://localhost:8000/generate_picturebook/user123?page_count=36"
```

**レスポンス例**:
```json
{
  "title": "おじいちゃんの自転車",
  "author": "田中太郎",
  "total_pages": 36,
  "pages": [
    {
      "page_number": 1,
      "text": "むかし、ぼくがちいさかったころ。はるのひに、じてんしゃにのれるようになりました。",
      "illustration_prompt": "A young Japanese boy in 1960s clothing standing next to a small bicycle in a neighborhood park. Cherry blossoms in the background. Warm afternoon sunlight. Nostalgic watercolor style.",
      "illustration_style_note": "温かみのある水彩画風、ノスタルジック、明るい色調"
    }
  ]
}
```

---

### 5. `GET /export/{user_id}?type=story&format=json`

生成済みコンテンツのエクスポート。

**パラメータ**:
- `type`: `materials` | `story` | `picturebook`
- `format`: `json` （将来的にPDF対応予定）

**リクエスト例**:
```bash
curl "http://localhost:8000/export/user123?type=story&format=json"
```

---

### 6. `DELETE /session/{user_id}` （デバッグ用）

セッションの削除。

**リクエスト例**:
```bash
curl -X DELETE http://localhost:8000/session/user123
```

---

### 7. `GET /sessions` （デバッグ用）

全セッション一覧を取得。

**リクエスト例**:
```bash
curl http://localhost:8000/sessions
```

---

## ワークフロー例

### 完全な自分史生成フロー

```bash
# 1. インタビュー開始
curl -X POST http://localhost:8000/interview \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "自分史を作りたいです",
    "mode": "interview",
    "project_type": "memoir"
  }'

# 2. 質問に答える（10回程度繰り返す）
curl -X POST http://localhost:8000/interview \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "幼少期は東京の下町で育ちました。父は町工場を営んでいました。",
    "mode": "interview",
    "project_type": "memoir"
  }'

# 3. 素材を構造化
curl http://localhost:8000/materials/user123 > materials.json

# 4. 自分史生成
curl http://localhost:8000/generate_story/user123 > story.json

# 5. 絵本版生成
curl "http://localhost:8000/generate_picturebook/user123?page_count=36" > picturebook.json

# 6. エクスポート
curl "http://localhost:8000/export/user123?type=story&format=json" > final_story.json
```

---

## 設定

### モデルの変更

`memoir_editor_api.py` の以下の行を編集：

```python
MODEL_NAME = "gpt-4-turbo-preview"  # または gpt-4o, gpt-4-1106-preview など
```

### データ保存先の変更

```python
DATA_DIR = Path("./sessions")  # お好みのディレクトリに変更
```

---

## トラブルシューティング

### エラー: "OpenAI API Error: ..."

- `OPENAI_API_KEY` 環境変数が正しく設定されているか確認
- APIキーの有効期限とクレジットを確認

### エラー: "Materials not found"

- 先に `/interview` で対話を完了してから `/materials/{user_id}` を実行
- 最低でも3〜5往復の対話が必要

### JSONパースエラー

- OpenAIのStructured Outputs対応モデルを使用しているか確認
- `gpt-4-turbo-preview` 以降のモデルが推奨

### セッションが残らない

- `DATA_DIR` のパーミッションを確認
- サーバー再起動時に消えないよう、絶対パスを指定

---

## 将来の拡張

- [ ] PDF出力（自分史・絵本）
- [ ] AI画像生成統合（DALL-E, Stable Diffusion）
- [ ] 音声インタビュー対応（Whisper）
- [ ] 複数言語対応
- [ ] Web UI（React/Vue）
- [ ] データベース統合（PostgreSQL, MongoDB）
- [ ] 認証・マルチユーザー対応

---

## ライセンス

社内プロジェクト用。商用利用の際はOpenAI利用規約を確認してください。

---

## サポート

質問・バグ報告は社内Slackまたはプロジェクト管理ツールへ。
