#!/usr/bin/env python3
"""
全PDFファイルをダウンロードして画像として保存
"""
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pdf2image import convert_from_bytes

TOKEN_FILE = os.path.expanduser('~/.config/claude-code/gdrive/token.json')
FOLDER_ID = "1GLnSezSNgWBhwYDvka3KgZ1ghEK8O9aM"
OUTPUT_DIR = "output/all_survey_images"

def main():
    # Google Drive認証
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    drive = build('drive', 'v3', credentials=creds)

    # PDFファイル一覧取得（名前順）
    query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
    results = drive.files().list(
        q=query,
        pageSize=100,
        fields="files(id, name)",
        orderBy="name",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    pdf_files = results.get('files', [])
    if not pdf_files:
        print("❌ PDFファイルが見つかりませんでした")
        return

    print(f"\n取得PDFファイル数: {len(pdf_files)} 件\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_pages = 0
    file_info = []

    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f"[{idx}/{len(pdf_files)}] {pdf_file['name']}")

        # PDFダウンロード
        print("  ダウンロード中...", end=' ')
        request = drive.files().get_media(fileId=pdf_file['id'])
        pdf_bytes = request.execute()
        print("✓")

        # PDF→画像変換
        print("  画像変換中...", end=' ')
        images = convert_from_bytes(pdf_bytes, dpi=200)
        page_count = len(images)
        print(f"✓ ({page_count}ページ)")

        # 画像保存
        start_page = total_pages + 1
        for i, img in enumerate(images):
            page_num = total_pages + i + 1
            output_path = os.path.join(OUTPUT_DIR, f"page_{page_num:03d}.png")
            img.save(output_path, 'PNG')

        print(f"  保存: page_{start_page:03d}.png 〜 page_{total_pages + page_count:03d}.png")

        file_info.append({
            'file_name': pdf_file['name'],
            'file_id': pdf_file['id'],
            'page_count': page_count,
            'start_page': start_page,
            'end_page': total_pages + page_count
        })

        total_pages += page_count
        print()

    # ファイル情報を保存
    info_path = os.path.join(OUTPUT_DIR, 'file_info.json')
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_files': len(pdf_files),
            'total_pages': total_pages,
            'files': file_info
        }, f, indent=2, ensure_ascii=False)

    print("=" * 80)
    print(f"✅ 完了: {len(pdf_files)}ファイル、{total_pages}ページの画像を {OUTPUT_DIR} に保存しました")
    print(f"   ファイル情報: {info_path}")

if __name__ == '__main__':
    main()
