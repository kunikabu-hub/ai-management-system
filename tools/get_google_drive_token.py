#!/usr/bin/env python3
"""
Google Drive & Calendar OAuth2 リフレッシュトークン取得スクリプト

使用方法:
1. 必要なライブラリをインストール: pip install google-auth-oauthlib google-auth-httplib2
2. このスクリプトを実行: python get_google_drive_token.py
3. ブラウザが開くので、Googleアカウントでログイン・承認
4. 取得したリフレッシュトークンをClaude設定に追加
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Google API のスコープ
# Google Drive: フルアクセス
# Google Calendar: 読み取り専用
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/calendar.readonly'
]

# 認証情報ファイルのパス
CREDENTIALS_FILE = os.path.expanduser('~/.config/claude-code/gdrive/credentials.json')
TOKEN_FILE = os.path.expanduser('~/.config/claude-code/gdrive/token.json')

def get_refresh_token():
    """OAuth2フローを実行してリフレッシュトークンを取得"""

    print("=" * 60)
    print("Google Drive & Calendar OAuth2 認証")
    print("=" * 60)

    # 認証情報ファイルの存在確認
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ エラー: 認証情報ファイルが見つかりません")
        print(f"   パス: {CREDENTIALS_FILE}")
        return None

    print(f"✅ 認証情報ファイルを読み込みました")
    print(f"   パス: {CREDENTIALS_FILE}\n")

    creds = None

    # 既存のトークンがある場合は読み込み
    if os.path.exists(TOKEN_FILE):
        print("既存のトークンファイルが見つかりました。削除して新しく認証します...")
        os.remove(TOKEN_FILE)

    # OAuth2フローを実行
    try:
        print("\n🌐 ブラウザが開きます...")
        print("   Googleアカウントでログインし、アクセスを承認してください\n")

        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES,
            redirect_uri='http://localhost'
        )

        # ローカルサーバーを起動して認証
        creds = flow.run_local_server(port=8080)

        # トークンを保存
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

        print("\n" + "=" * 60)
        print("✅ 認証成功！")
        print("=" * 60)

        # 認証情報を読み込み
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)

        if 'refresh_token' in token_data:
            refresh_token = token_data['refresh_token']

            print("\n📋 リフレッシュトークン:")
            print("-" * 60)
            print(refresh_token)
            print("-" * 60)

            print("\n📝 次のステップ:")
            print("1. 上記のリフレッシュトークンをコピー")
            print("2. Claude設定ファイルを編集:")
            print(f"   ~/Library/Application Support/Claude/claude_desktop_config.json")
            print("3. GOOGLE_REFRESH_TOKEN に貼り付け")
            print("4. Claude Codeを再起動\n")

            # 設定ファイルの例を表示
            print("=" * 60)
            print("設定ファイルの例:")
            print("=" * 60)

            config_example = {
                "mcpServers": {
                    "gdrive": {
                        "command": "npx",
                        "args": ["-y", "mcp-google-drive"],
                        "env": {
                            "GOOGLE_CLIENT_ID": "your-client-id",
                            "GOOGLE_CLIENT_SECRET": "your-client-secret",
                            "GOOGLE_REDIRECT_URI": "http://localhost",
                            "GOOGLE_REFRESH_TOKEN": refresh_token
                        }
                    }
                }
            }

            print(json.dumps(config_example, indent=2, ensure_ascii=False))
            print()

            return refresh_token
        else:
            print("\n❌ エラー: リフレッシュトークンが取得できませんでした")
            print("   'access_type' を 'offline' に設定する必要があります")
            return None

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    refresh_token = get_refresh_token()

    if refresh_token:
        print("✅ 完了！")
    else:
        print("❌ 失敗しました。エラーメッセージを確認してください。")
