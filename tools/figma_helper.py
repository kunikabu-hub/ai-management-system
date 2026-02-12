#!/usr/bin/env python3
"""
Figma Helper
デザインファイル情報取得、コメント管理、画像エクスポート
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

FIGMA_TOKEN = os.getenv('FIGMA_TOKEN')
FIGMA_API_URL = 'https://api.figma.com/v1'


def call_figma_api(endpoint, method='GET', data=None):
    """Figma APIを呼び出す"""
    if not FIGMA_TOKEN:
        print("Error: FIGMA_TOKEN not found in environment variables")
        sys.exit(1)

    url = f"{FIGMA_API_URL}/{endpoint}"
    headers = {
        'X-Figma-Token': FIGMA_TOKEN
    }

    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"Error calling Figma API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)


def extract_file_key(url_or_key):
    """FigmaファイルURLまたはキーからファイルキーを抽出"""
    if 'figma.com' in url_or_key:
        # URL形式: https://www.figma.com/file/FILE_KEY/...
        parts = url_or_key.split('/')
        if 'file' in parts:
            file_index = parts.index('file')
            if len(parts) > file_index + 1:
                return parts[file_index + 1]
    # 既にキー形式の場合はそのまま返す
    return url_or_key


def get_file_info(file_key):
    """Figmaファイルの情報を取得"""
    file_key = extract_file_key(file_key)
    file_data = call_figma_api(f"files/{file_key}")

    print(f"\n🎨 Figma File Info:")
    print(f"  Name: {file_data['name']}")
    print(f"  Last Modified: {file_data['lastModified']}")
    print(f"  Version: {file_data['version']}")
    print(f"  Thumbnail: {file_data.get('thumbnailUrl', 'N/A')}\n")

    # ページ情報
    if 'document' in file_data:
        print(f"  📄 Pages:")
        for child in file_data['document'].get('children', []):
            print(f"    - {child.get('name', 'Unnamed')}")

    print()
    return file_data


def get_comments(file_key):
    """ファイルのコメント一覧を取得"""
    file_key = extract_file_key(file_key)
    comments_data = call_figma_api(f"files/{file_key}/comments")

    comments = comments_data.get('comments', [])
    print(f"\n💬 Comments ({len(comments)}):\n")

    for comment in comments:
        user = comment.get('user', {})
        print(f"👤 {user.get('handle', 'Unknown')}: {comment.get('message', '')}")
        print(f"   Created: {comment.get('created_at', 'N/A')}")
        print(f"   Resolved: {comment.get('resolved_at', 'Not resolved')}\n")

    return comments


def post_comment(file_key, message, client_meta=None):
    """ファイルにコメントを投稿"""
    file_key = extract_file_key(file_key)

    data = {
        'message': message
    }

    if client_meta:
        data['client_meta'] = client_meta

    result = call_figma_api(f"files/{file_key}/comments", method='POST', data=data)

    print(f"\n✅ コメント投稿完了:")
    print(f"  Message: {message}")
    print(f"  ID: {result.get('id', 'N/A')}\n")

    return result


def get_team_projects(team_id):
    """チームのプロジェクト一覧を取得"""
    projects = call_figma_api(f"teams/{team_id}/projects")

    print(f"\n📁 Team Projects:\n")
    for project in projects.get('projects', []):
        print(f"  {project.get('name', 'Unnamed')}")
        print(f"    ID: {project.get('id')}\n")

    return projects


def get_project_files(project_id):
    """プロジェクト内のファイル一覧を取得"""
    files = call_figma_api(f"projects/{project_id}/files")

    print(f"\n📄 Project Files:\n")
    for file in files.get('files', []):
        print(f"  {file.get('name', 'Unnamed')}")
        print(f"    Key: {file.get('key')}")
        print(f"    Last Modified: {file.get('last_modified')}\n")

    return files


def export_images(file_key, node_ids=None, scale=2, format='png'):
    """ノードを画像としてエクスポート"""
    file_key = extract_file_key(file_key)

    # node_idsが指定されていない場合は、ファイル全体の情報を取得
    if not node_ids:
        file_data = call_figma_api(f"files/{file_key}")
        # 最初のページの最初のフレームをエクスポート（例）
        if 'document' in file_data:
            first_page = file_data['document'].get('children', [{}])[0]
            first_frame = first_page.get('children', [{}])[0]
            node_ids = [first_frame.get('id')]

    if not node_ids:
        print("Error: No node IDs to export")
        return None

    # 画像URLを取得
    params = f"ids={','.join(node_ids)}&scale={scale}&format={format}"
    images_data = call_figma_api(f"images/{file_key}?{params}")

    print(f"\n🖼️  Image Export URLs:\n")
    for node_id, url in images_data.get('images', {}).items():
        print(f"  Node {node_id}: {url}\n")

    return images_data


def export_file_to_json(file_key, output_file=None):
    """ファイル情報をJSONにエクスポート"""
    file_key = extract_file_key(file_key)
    file_data = call_figma_api(f"files/{file_key}")

    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(__file__).parent.parent / 'output' / 'figma'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f'figma_{file_data["name"]}_{timestamp}.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(file_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ ファイル情報をエクスポート: {output_file}\n")
    return output_file


def get_user_info():
    """認証ユーザーの情報を取得"""
    user = call_figma_api("me")

    print(f"\n👤 Figma User Info:")
    print(f"  ID: {user.get('id')}")
    print(f"  Email: {user.get('email')}")
    print(f"  Handle: {user.get('handle')}\n")

    return user


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python figma_helper.py me                              # ユーザー情報")
        print("  python figma_helper.py info <file_key_or_url>         # ファイル情報")
        print("  python figma_helper.py comments <file_key_or_url>     # コメント一覧")
        print("  python figma_helper.py comment <file_key_or_url> <msg># コメント投稿")
        print("  python figma_helper.py export <file_key_or_url>       # JSONエクスポート")
        print("  python figma_helper.py images <file_key_or_url>       # 画像エクスポート")
        print("  python figma_helper.py team <team_id>                 # チームプロジェクト")
        print("  python figma_helper.py project <project_id>           # プロジェクトファイル")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'me':
        get_user_info()

    elif command == 'info' and len(sys.argv) > 2:
        file_key = sys.argv[2]
        get_file_info(file_key)

    elif command == 'comments' and len(sys.argv) > 2:
        file_key = sys.argv[2]
        get_comments(file_key)

    elif command == 'comment' and len(sys.argv) > 3:
        file_key = sys.argv[2]
        message = ' '.join(sys.argv[3:])
        post_comment(file_key, message)

    elif command == 'export' and len(sys.argv) > 2:
        file_key = sys.argv[2]
        export_file_to_json(file_key)

    elif command == 'images' and len(sys.argv) > 2:
        file_key = sys.argv[2]
        export_images(file_key)

    elif command == 'team' and len(sys.argv) > 2:
        team_id = sys.argv[2]
        get_team_projects(team_id)

    elif command == 'project' and len(sys.argv) > 2:
        project_id = sys.argv[2]
        get_project_files(project_id)

    else:
        print("Invalid command or missing arguments")
        sys.exit(1)
