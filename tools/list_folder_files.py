#!/usr/bin/env python3
"""
指定したGoogle DriveフォルダのファイルIDを取得するスクリプト
"""
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_FILE = os.path.expanduser('~/.config/claude-code/gdrive/token.json')

def list_folder_files(folder_id):
    """指定フォルダ内のファイル一覧を取得"""
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    # フォルダ内のファイルを取得
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        pageSize=100,
        fields="files(id, name, mimeType, size, modifiedTime)"
    ).execute()

    items = results.get('files', [])

    print(f"\n取得件数: {len(items)} 件\n")
    print(f"{'ファイル名':<50} {'タイプ':<30} {'サイズ':<15}")
    print("-" * 100)

    for item in items:
        name = item['name']
        mime_type = item.get('mimeType', 'N/A')
        size = item.get('size', '-')

        if size != '-':
            size_int = int(size)
            if size_int < 1024 * 1024:
                size_display = f"{size_int / 1024:.1f} KB"
            else:
                size_display = f"{size_int / (1024 * 1024):.1f} MB"
        else:
            size_display = "-"

        print(f"{name:<50} {mime_type:<30} {size_display:<15}")
        print(f"  ID: {item['id']}")

    return items

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("使用方法: python list_folder_files.py <folder_id>")
        sys.exit(1)

    folder_id = sys.argv[1]
    files = list_folder_files(folder_id)

    # JSON形式で保存
    output_file = 'output/folder_files.json'
    os.makedirs('output', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(files, f, indent=2, ensure_ascii=False)

    print(f"\n詳細情報を {output_file} に保存しました。")
