#!/usr/bin/env python3
"""
サンプルPDFを1つダウンロードして画像として保存
"""
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from pdf2image import convert_from_bytes

TOKEN_FILE = os.path.expanduser('~/.config/claude-code/gdrive/token.json')
FOLDER_ID = "1GLnSezSNgWBhwYDvka3KgZ1ghEK8O9aM"
OUTPUT_DIR = "output/sample_survey_images"

def main():
    # Google Drive認証
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    drive = build('drive', 'v3', credentials=creds)

    # PDFファイル一覧取得
    query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
    results = drive.files().list(
        q=query,
        pageSize=1,
        fields="files(id, name)",
        orderBy="name",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    files = results.get('files', [])
    if not files:
        print("❌ PDFファイルが見つかりませんでした")
        return

    pdf_file = files[0]
    print(f"サンプルPDF: {pdf_file['name']}")

    # PDFダウンロード
    print("  ダウンロード中...")
    request = drive.files().get_media(fileId=pdf_file['id'])
    pdf_bytes = request.execute()

    # PDF→画像変換
    print("  画像変換中...")
    images = convert_from_bytes(pdf_bytes, dpi=200)
    print(f"  ページ数: {len(images)}")

    # 画像保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for i, img in enumerate(images):
        output_path = os.path.join(OUTPUT_DIR, f"page_{i+1:02d}.png")
        img.save(output_path, 'PNG')
        print(f"  保存: {output_path}")

    print(f"\n✅ 完了: {len(images)}枚の画像を {OUTPUT_DIR} に保存しました")

if __name__ == '__main__':
    main()
