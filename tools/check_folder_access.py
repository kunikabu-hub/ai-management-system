#!/usr/bin/env python3
"""
Google Driveフォルダのアクセス権限を確認するスクリプト
"""
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

TOKEN_FILE = os.path.expanduser('~/.config/claude-code/gdrive/token.json')

def check_folder_access(folder_id):
    """フォルダの詳細情報とアクセス権限を確認"""
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    try:
        # フォルダの詳細情報を取得
        file = service.files().get(
            fileId=folder_id,
            fields="id, name, mimeType, owners, shared, capabilities, permissions"
        ).execute()

        print("=" * 80)
        print("フォルダ情報")
        print("=" * 80)
        print(f"ID: {file.get('id')}")
        print(f"名前: {file.get('name')}")
        print(f"MIMEタイプ: {file.get('mimeType')}")
        print(f"共有: {file.get('shared')}")
        print(f"\nオーナー: {file.get('owners')}")
        print(f"\n権限:")
        print(json.dumps(file.get('capabilities'), indent=2, ensure_ascii=False))

        # フォルダ内のファイル一覧を試行
        print("\n" + "=" * 80)
        print("フォルダ内ファイル一覧を取得中...")
        print("=" * 80)

        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, size)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        items = results.get('files', [])
        print(f"\n取得件数: {len(items)} 件")

        for item in items:
            print(f"  - {item['name']} (ID: {item['id']})")

    except HttpError as error:
        print(f"❌ エラー: {error}")
        if error.resp.status == 404:
            print("フォルダが見つかりません。URLを確認してください。")
        elif error.resp.status == 403:
            print("アクセス権限がありません。フォルダが共有されているか確認してください。")

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("使用方法: python check_folder_access.py <folder_id>")
        sys.exit(1)

    folder_id = sys.argv[1]
    check_folder_access(folder_id)
