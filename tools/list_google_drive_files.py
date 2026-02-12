#!/usr/bin/env python3
"""
Google Driveのファイル一覧を表示するスクリプト

使用方法:
1. 認証設定が完了していること（get_google_drive_token.pyを実行済み）
2. このスクリプトを実行: python list_google_drive_files.py
"""

import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import socket

# デフォルトのタイムアウトを設定（秒）
socket.setdefaulttimeout(30)

# トークンファイルのパス
TOKEN_FILE = os.path.expanduser('~/.config/claude-code/gdrive/token.json')
CREDENTIALS_FILE = os.path.expanduser('~/.config/claude-code/gdrive/credentials.json')

def list_files(max_results=50, folder_id=None):
    """Google Driveのファイル一覧を取得"""

    # トークンファイルの存在確認
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ エラー: トークンファイルが見つかりません")
        print(f"   パス: {TOKEN_FILE}")
        print(f"\n先に get_google_drive_token.py を実行して認証を完了してください。")
        return None

    try:
        # 認証情報を読み込み
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)

        creds = Credentials.from_authorized_user_info(token_data)

        # トークンが期限切れの場合は更新
        if creds and creds.expired and creds.refresh_token:
            print("トークンを更新しています...")
            try:
                creds.refresh(Request())
                # 更新したトークンを保存
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print("✅ トークンを更新しました。\n")
            except Exception as e:
                print(f"⚠️  トークン更新に失敗しました: {e}")
                print("認証をやり直してください（get_google_drive_token.pyを実行）\n")

        # Google Drive APIサービスを構築
        print("Google Drive APIに接続中...")
        service = build('drive', 'v3', credentials=creds)

        # クエリの構築
        query = "trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"

        # ファイル一覧を取得
        print("=" * 80)
        print("Google Drive ファイル一覧")
        print("=" * 80)

        results = service.files().list(
            pageSize=max_results,
            q=query,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime, size, webViewLink)",
            orderBy="modifiedTime desc"
        ).execute()

        items = results.get('files', [])

        if not items:
            print('\nファイルが見つかりませんでした。')
            return []

        print(f'\n取得件数: {len(items)} 件\n')
        print(f"{'名前':<40} {'タイプ':<25} {'更新日時':<20} {'サイズ':<15}")
        print("-" * 80)

        for item in items:
            name = item['name'][:38] + '..' if len(item['name']) > 40 else item['name']
            mime_type = item.get('mimeType', 'N/A')

            # MIMEタイプを短く表示
            if 'folder' in mime_type:
                type_display = '📁 フォルダ'
            elif 'document' in mime_type:
                type_display = '📄 ドキュメント'
            elif 'spreadsheet' in mime_type:
                type_display = '📊 スプレッドシート'
            elif 'presentation' in mime_type:
                type_display = '📊 プレゼンテーション'
            elif 'image' in mime_type:
                type_display = '🖼️  画像'
            elif 'pdf' in mime_type:
                type_display = '📕 PDF'
            else:
                type_display = mime_type.split('.')[-1][:23]

            modified = item.get('modifiedTime', 'N/A')[:19].replace('T', ' ')

            # サイズ（Google Docsなどはサイズがない）
            size = item.get('size')
            if size:
                size_int = int(size)
                if size_int < 1024:
                    size_display = f"{size_int} B"
                elif size_int < 1024 * 1024:
                    size_display = f"{size_int / 1024:.1f} KB"
                elif size_int < 1024 * 1024 * 1024:
                    size_display = f"{size_int / (1024 * 1024):.1f} MB"
                else:
                    size_display = f"{size_int / (1024 * 1024 * 1024):.2f} GB"
            else:
                size_display = "-"

            print(f"{name:<40} {type_display:<25} {modified:<20} {size_display:<15}")

        print("\n" + "=" * 80)

        # 詳細情報をJSON形式で保存
        output_file = 'output/google_drive_files.json'
        os.makedirs('output', exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

        print(f"\n詳細情報を {output_file} に保存しました。")

        return items

    except HttpError as error:
        print(f'❌ APIエラーが発生しました: {error}')
        return None
    except Exception as e:
        print(f'❌ エラーが発生しました: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    import sys

    # 引数で取得件数を指定可能
    max_results = 50
    if len(sys.argv) > 1:
        try:
            max_results = int(sys.argv[1])
        except ValueError:
            print(f"警告: 無効な引数 '{sys.argv[1]}'。デフォルト値 50 を使用します。")

    files = list_files(max_results=max_results)

    if files is not None:
        print("\n✅ 完了！")
    else:
        print("\n❌ 失敗しました。エラーメッセージを確認してください。")
