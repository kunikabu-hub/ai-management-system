#!/usr/bin/env python3
"""
Google Driveのファイル一覧を表示するスクリプト（requests版）

使用方法:
python3 list_drive_files_simple.py [取得件数]
"""

import os
import json
import requests
import sys
from datetime import datetime

# トークンファイルのパス
TOKEN_FILE = os.path.expanduser('~/.config/claude-code/gdrive/token.json')

def get_access_token():
    """トークンファイルからアクセストークンを取得"""
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ エラー: トークンファイルが見つかりません")
        print(f"   パス: {TOKEN_FILE}")
        return None

    try:
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)
        return token_data.get('token')
    except Exception as e:
        print(f"❌ トークン読み込みエラー: {e}")
        return None

def list_files(max_results=50):
    """Google Driveのファイル一覧を取得"""

    access_token = get_access_token()
    if not access_token:
        return None

    print("=" * 80)
    print("Google Drive ファイル一覧")
    print("=" * 80)
    print()

    # APIエンドポイント
    url = "https://www.googleapis.com/drive/v3/files"

    # リクエストパラメータ
    params = {
        'pageSize': max_results,
        'fields': 'files(id,name,mimeType,modifiedTime,size,webViewLink,owners)',
        'orderBy': 'modifiedTime desc',
        'q': 'trashed=false'
    }

    # リクエストヘッダー
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    try:
        print("Google Drive APIに接続中...")
        response = requests.get(url, params=params, headers=headers, timeout=30)

        if response.status_code == 401:
            print("❌ 認証エラー: トークンが無効です")
            print("   get_google_drive_token.py を実行して認証をやり直してください")
            return None

        if response.status_code != 200:
            print(f"❌ APIエラー: {response.status_code}")
            print(response.text)
            return None

        data = response.json()
        files = data.get('files', [])

        if not files:
            print('\nファイルが見つかりませんでした。')
            return []

        print(f'✅ 取得件数: {len(files)} 件\n')
        print(f"{'名前':<40} {'タイプ':<25} {'更新日時':<20} {'サイズ':<15}")
        print("-" * 100)

        for item in files:
            name = item['name']
            if len(name) > 38:
                name = name[:38] + '..'

            mime_type = item.get('mimeType', 'N/A')

            # MIMEタイプを短く表示
            if 'folder' in mime_type:
                type_display = '📁 フォルダ'
            elif 'document' in mime_type:
                type_display = '📄 ドキュメント'
            elif 'spreadsheet' in mime_type:
                type_display = '📊 スプレッドシート'
            elif 'presentation' in mime_type:
                type_display = '📽️  プレゼンテーション'
            elif 'image' in mime_type:
                type_display = '🖼️  画像'
            elif 'pdf' in mime_type:
                type_display = '📕 PDF'
            elif 'video' in mime_type:
                type_display = '🎬 動画'
            elif 'audio' in mime_type:
                type_display = '🎵 音声'
            else:
                type_display = mime_type.split('.')[-1][:23]

            # 更新日時
            modified = item.get('modifiedTime', 'N/A')
            if modified != 'N/A':
                try:
                    dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                    modified = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    modified = modified[:19].replace('T', ' ')

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
            json.dump(files, f, indent=2, ensure_ascii=False)

        print(f"\n📁 詳細情報を {output_file} に保存しました。")

        return files

    except requests.exceptions.Timeout:
        print("❌ タイムアウトエラー: 接続がタイムアウトしました")
        print("   ネットワーク接続を確認してください")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ リクエストエラー: {e}")
        return None
    except Exception as e:
        print(f'❌ エラーが発生しました: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
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
