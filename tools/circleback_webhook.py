#!/usr/bin/env python3
"""
Circleback Webhook Server
Circlebackからの議事録データを受信し、自動処理するWebhookサーバー
"""

import os
import hmac
import hashlib
import json
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from circleback_processor import process_meeting_data

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)

# Circleback Webhook Signing Secret
WEBHOOK_SECRET = os.getenv('CIRCLEBACK_WEBHOOK_SECRET', '')

def verify_signature(payload_body, signature_header):
    """
    Webhook署名を検証（HMAC-SHA256）
    """
    if not WEBHOOK_SECRET:
        print("⚠️ CIRCLEBACK_WEBHOOK_SECRETが設定されていません")
        return True  # 開発時は署名検証をスキップ

    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature_header, expected_signature)


@app.route('/webhook/circleback', methods=['POST'])
def circleback_webhook():
    """
    Circlebackからのwebhookを受信
    """
    try:
        # 署名検証
        signature = request.headers.get('X-Circleback-Signature', '')
        payload_body = request.get_data()

        if not verify_signature(payload_body, signature):
            print("❌ 署名検証失敗")
            return jsonify({'error': 'Invalid signature'}), 401

        # JSONデータの取得
        data = request.get_json()

        if not data:
            print("❌ データが空です")
            return jsonify({'error': 'No data received'}), 400

        print(f"\n📥 Circleback Webhookを受信しました")
        print(f"Meeting ID: {data.get('meeting_id', 'Unknown')}")

        # データ処理（別モジュール）
        result = process_meeting_data(data)

        if result['success']:
            print(f"✅ 議事録処理完了: {result['saved_files']}")
            return jsonify({
                'status': 'success',
                'message': 'Meeting data processed successfully',
                'saved_files': result['saved_files']
            }), 200
        else:
            print(f"⚠️ 処理中にエラー: {result['error']}")
            return jsonify({
                'status': 'error',
                'message': result['error']
            }), 500

    except Exception as e:
        print(f"❌ エラー: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    ヘルスチェックエンドポイント
    """
    return jsonify({
        'status': 'healthy',
        'service': 'circleback-webhook',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/', methods=['GET'])
def index():
    """
    ルートエンドポイント（動作確認用）
    """
    return jsonify({
        'service': 'Circleback Webhook Server',
        'version': '1.0.0',
        'endpoints': {
            'webhook': '/webhook/circleback (POST)',
            'health': '/health (GET)'
        }
    }), 200


if __name__ == '__main__':
    print("\n🚀 Circleback Webhook Serverを起動します...")
    print(f"📡 Webhook URL: http://localhost:5000/webhook/circleback")
    print(f"💚 Health Check: http://localhost:5000/health")

    if not WEBHOOK_SECRET:
        print("\n⚠️ WARNING: CIRCLEBACK_WEBHOOK_SECRETが設定されていません")
        print("   開発モードで署名検証なしで起動します")
        print("   本番環境では必ず.envファイルにCIRCLEBACK_WEBHOOK_SECRETを設定してください\n")

    # サーバー起動
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
