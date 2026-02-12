#!/bin/bash
# Google Driveのファイル一覧を表示するシェルスクリプト

# トークンを取得
TOKEN=$(cat ~/.config/claude-code/gdrive/token.json | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")

# 取得件数（デフォルト: 50）
PAGE_SIZE=${1:-50}

echo "================================================================================"
echo "Google Drive ファイル一覧"
echo "================================================================================"
echo ""
echo "Google Drive APIに接続中..."

# APIを呼び出してJSONを取得
RESPONSE=$(curl -s -m 30 -H "Authorization: Bearer $TOKEN" \
  "https://www.googleapis.com/drive/v3/files?pageSize=$PAGE_SIZE&fields=files(id,name,mimeType,modifiedTime,size)&orderBy=modifiedTime%20desc&q=trashed=false")

# エラーチェック
if echo "$RESPONSE" | grep -q "error"; then
  echo "❌ APIエラーが発生しました:"
  echo "$RESPONSE" | python3 -m json.tool
  exit 1
fi

# ファイル一覧を整形して表示
echo "$RESPONSE" | python3 -c "
import sys, json
from datetime import datetime

data = json.load(sys.stdin)
files = data.get('files', [])

if not files:
    print('ファイルが見つかりませんでした。')
    sys.exit(0)

print(f'✅ 取得件数: {len(files)} 件\n')
print(f\"{'名前':<40} {'タイプ':<20} {'更新日時':<20} {'サイズ':<15}\")
print('-' * 95)

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
        type_display = '📽️  プレゼン'
    elif 'image' in mime_type:
        type_display = '🖼️  画像'
    elif 'pdf' in mime_type:
        type_display = '📕 PDF'
    elif 'video' in mime_type:
        type_display = '🎬 動画'
    elif 'audio' in mime_type:
        type_display = '🎵 音声'
    else:
        type_display = mime_type.split('.')[-1][:18]

    # 更新日時
    modified = item.get('modifiedTime', 'N/A')
    if modified != 'N/A':
        try:
            dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
            modified = dt.strftime('%Y-%m-%d %H:%M')
        except:
            modified = modified[:19].replace('T', ' ')

    # サイズ
    size = item.get('size')
    if size:
        size_int = int(size)
        if size_int < 1024:
            size_display = f'{size_int} B'
        elif size_int < 1024 * 1024:
            size_display = f'{size_int / 1024:.1f} KB'
        elif size_int < 1024 * 1024 * 1024:
            size_display = f'{size_int / (1024 * 1024):.1f} MB'
        else:
            size_display = f'{size_int / (1024 * 1024 * 1024):.2f} GB'
    else:
        size_display = '-'

    print(f'{name:<40} {type_display:<20} {modified:<20} {size_display:<15}')

print()
print('=' * 95)

# JSONファイルに保存
import os
os.makedirs('output', exist_ok=True)
with open('output/google_drive_files.json', 'w', encoding='utf-8') as f:
    json.dump(files, f, indent=2, ensure_ascii=False)

print('\n📁 詳細情報を output/google_drive_files.json に保存しました。')
"

echo ""
echo "✅ 完了！"
