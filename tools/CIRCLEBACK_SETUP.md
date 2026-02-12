# Circleback Webhook 連携セットアップガイド

Circleback AIからの議事録を自動的に受信・処理するためのセットアップ手順です。

---

## 📋 前提条件

- Circlebackアカウントを持っていること
- Python 3.9以上がインストールされていること
- Flask、python-dotenvがインストールされていること（requirements.txtに含まれています）

---

## 🚀 セットアップ手順

### 1. 依存関係のインストール

```bash
cd /Users/attadesign/Documents/ai-management-system
pip3 install -r requirements.txt
```

### 2. Webhook Serverの起動

```bash
cd tools
./start_webhook_server.sh
```

サーバーが起動すると、以下のように表示されます：

```
🚀 Circleback Webhook Serverを起動します...
📡 Webhook URL: http://localhost:5000/webhook/circleback
💚 Health Check: http://localhost:5000/health
```

### 3. 外部からアクセス可能にする（ngrok使用）

Circlebackからローカルサーバーにアクセスできるようにするため、ngrokを使用します。

#### ngrokのインストール

```bash
# Homebrewを使用
brew install ngrok

# または公式サイトからダウンロード
# https://ngrok.com/download
```

#### ngrokの起動

別のターミナルで以下を実行：

```bash
ngrok http 5000
```

ngrokが起動すると、以下のような出力が表示されます：

```
Forwarding   https://xxxx-xxxx-xxxx.ngrok-free.app -> http://localhost:5000
```

この `https://xxxx-xxxx-xxxx.ngrok-free.app` がCirclebackに設定するWebhook URLです。

### 4. CirclebackでWebhookを設定

1. **Circlebackにログイン**
   - https://app.circleback.ai/ にアクセス

2. **Settings → Webhook** に移動

3. **Webhook URLを設定**
   - URL: `https://xxxx-xxxx-xxxx.ngrok-free.app/webhook/circleback`
   - （ngrokで表示されたURLの末尾に `/webhook/circleback` を追加）

4. **Signing Secretを取得**
   - Circlebackの設定画面に表示される「Signing Secret」をコピー

5. **.envファイルに設定**

   `.env` ファイルを編集して、Signing Secretを設定：

   ```bash
   CIRCLEBACK_WEBHOOK_SECRET=your_actual_signing_secret_here
   ```

6. **Webhook Serverを再起動**

   Webhook Serverを一度停止（Ctrl+C）して再起動：

   ```bash
   ./start_webhook_server.sh
   ```

### 5. 動作確認

1. **ヘルスチェック**

   ブラウザまたはcurlで動作確認：

   ```bash
   curl http://localhost:5000/health
   ```

   レスポンス例：
   ```json
   {
     "status": "healthy",
     "service": "circleback-webhook",
     "timestamp": "2026-02-13T10:00:00"
   }
   ```

2. **Circlebackでテスト送信**

   - Circlebackの設定画面で「Test Webhook」ボタンをクリック
   - Webhook Serverのログに受信メッセージが表示されることを確認

3. **実際のミーティングでテスト**

   - ZoomやGoogle Meetでミーティングを実施
   - Circlebackで議事録が生成される
   - 自動的にWebhookが送信され、ローカルに保存される

---

## 📁 保存場所

議事録データは以下の場所に自動保存されます：

### 1. 議事録ファイル

```
output/meetings/YYYY-MM-DD_meeting_title.md
```

**内容**:
- 要約
- アクションアイテム
- トランスクリプト（全文文字起こし）
- インサイト
- メタデータ（録音URL、Circlebackリンク）

### 2. メモリファイル

重要な意思決定が検出された場合：

```
00_context/memories/decisions.md
```

**抽出される内容**:
- 「決定」「合意」「承認」などのキーワードを含む発言
- プロジェクトの方向性に関する議論

---

## 🔧 トラブルシューティング

### Webhook Serverが起動しない

**原因**: ポート5000が既に使用されている

**解決方法**:
```bash
# 使用中のプロセスを確認
lsof -i :5000

# プロセスを停止
kill -9 <PID>
```

### Circlebackからデータが届かない

**確認項目**:
1. ngrokが起動しているか
2. Webhook URLが正しく設定されているか
3. Signing Secretが正しく設定されているか
4. Webhook Serverのログにエラーが表示されていないか

### 署名検証エラー

**原因**: CIRCLEBACK_WEBHOOK_SECRETが間違っている

**解決方法**:
1. Circlebackの設定画面でSigning Secretを再確認
2. `.env`ファイルを更新
3. Webhook Serverを再起動

---

## 🛑 サーバーの停止

Webhook Serverを停止するには：

```bash
# ターミナルで Ctrl+C を押す
```

ngrokも停止する場合：

```bash
# ngrokのターミナルで Ctrl+C を押す
```

---

## 📝 開発モード（署名検証なし）

開発・テスト時に署名検証をスキップする場合：

`.env`ファイルで `CIRCLEBACK_WEBHOOK_SECRET` を空にするか、コメントアウトします：

```bash
# CIRCLEBACK_WEBHOOK_SECRET=
```

⚠️ **注意**: 本番環境では必ず署名検証を有効にしてください。

---

## 🌐 本番環境へのデプロイ（オプション）

ローカル環境ではなく、クラウドサーバーで常時稼働させる場合：

### 推奨サービス
- **Heroku**: 簡単にデプロイ可能
- **Railway**: 無料プランあり
- **Render**: シンプルな設定
- **AWS EC2**: フルコントロール可能

### デプロイ手順（Heroku例）

1. **Procfileを作成**

   ```
   web: python tools/circleback_webhook.py
   ```

2. **Herokuにデプロイ**

   ```bash
   heroku create your-app-name
   git push heroku main
   ```

3. **環境変数を設定**

   ```bash
   heroku config:set CIRCLEBACK_WEBHOOK_SECRET=your_secret
   ```

4. **Webhook URLを更新**

   Circlebackの設定で：
   ```
   https://your-app-name.herokuapp.com/webhook/circleback
   ```

---

## 📞 サポート

問題が解決しない場合は、以下を確認してください：

1. **ログの確認**: Webhook Serverのコンソール出力
2. **Circlebackのドキュメント**: https://circleback.ai/docs/webhook-integration
3. **ngrokのステータス**: http://localhost:4040 でリクエスト履歴を確認

---

**作成日**: 2026-02-13
**最終更新**: 2026-02-13
