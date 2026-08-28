#!/usr/bin/env python3
"""
共有ドライブ対応のフォルダ一覧取得スクリプト
"""
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

TOKEN_FILE = os.path.expanduser('~/.config/claude-code/gdrive/token.json')

def list_folder_files_with_shared_drives(folder_id):
    """共有ドライブ対応でフォルダ内のファイルを取得"""
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    try:
        print("=" * 80)
        print("フォルダ情報を取得中...")
        print("=" * 80)

        # フォルダ情報を取得（共有ドライブ対応）
        file_info = service.files().get(
            fileId=folder_id,
            fields="id, name, mimeType, driveId",
            supportsAllDrives=True
        ).execute()

        print(f"フォルダ名: {file_info.get('name')}")
        print(f"フォルダID: {file_info.get('id')}")
        print(f"MIMEタイプ: {file_info.get('mimeType')}")
        drive_id = file_info.get('driveId')
        if drive_id:
            print(f"共有ドライブID: {drive_id}")
        print()

        # フォルダ内のファイル一覧を取得
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, size, modifiedTime)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora='allDrives' if drive_id else 'user'
        ).execute()

        items = results.get('files', [])

        print("=" * 80)
        print(f"取得ファイル数: {len(items)} 件")
        print("=" * 80)

        if items:
            print(f"\n{'ファイル名':<60} {'タイプ':<30} {'サイズ':<15}")
            print("-" * 110)

            for item in items:
                name = item['name'][:58] + '..' if len(item['name']) > 60 else item['name']
                mime_type = item.get('mimeType', 'N/A')

                # タイプ表示を簡潔に
                if 'pdf' in mime_type:
                    type_display = 'PDF'
                elif 'folder' in mime_type:
                    type_display = 'フォルダ'
                else:
                    type_display = mime_type.split('.')[-1][:28]

                size = item.get('size', '-')
                if size != '-':
                    size_int = int(size)
                    if size_int < 1024 * 1024:
                        size_display = f"{size_int / 1024:.1f} KB"
                    else:
                        size_display = f"{size_int / (1024 * 1024):.1f} MB"
                else:
                    size_display = "-"

                print(f"{name:<60} {type_display:<30} {size_display:<15}")
                print(f"  ID: {item['id']}")

            # JSON保存
            output_file = 'output/survey_folder_files.json'
            os.makedirs('output', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            print(f"\n詳細情報を {output_file} に保存しました。")

            return items
        else:
            print("\nフォルダ内にファイルが見つかりませんでした。")
            return []

    except HttpError as error:
        print(f"❌ エラー: {error}")
        if error.resp.status == 404:
            print("\n【対処方法】")
            print("1. フォルダのオーナーに、kunikabu@ehon.inc へのアクセス権限付与を依頼")
            print("2. Google Driveでフォルダを開き、「共有」→「ユーザーを追加」→ kunikabu@ehon.inc")
            print("3. 権限は「閲覧者」または「編集者」を選択")
        return None

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("使用方法: python list_folder_with_shared_drive.py <folder_id>")
        sys.exit(1)

    folder_id = sys.argv[1]
    list_folder_files_with_shared_drives(folder_id)
