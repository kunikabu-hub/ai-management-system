#!/usr/bin/env python3
"""
Markdown to PDF Converter
Playwrightを使用してMarkdownファイルをPDFに変換
"""

import sys
import markdown
from pathlib import Path
from playwright.sync_api import sync_playwright


def convert_md_to_pdf(md_file, output_pdf=None):
    """MarkdownファイルをPDFに変換"""

    # MarkdownファイルをHTMLに変換
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Markdown → HTML変換（拡張機能付き）
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'nl2br']
    )

    # CSSスタイル付きHTMLテンプレート
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Noto Sans JP", Meiryo, sans-serif;
                line-height: 1.8;
                max-width: 900px;
                margin: 40px auto;
                padding: 20px;
                color: #333;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-top: 40px;
            }}
            h2 {{
                color: #34495e;
                border-bottom: 2px solid #95a5a6;
                padding-bottom: 8px;
                margin-top: 30px;
            }}
            h3 {{
                color: #7f8c8d;
                margin-top: 25px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: "Courier New", monospace;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            ul, ol {{
                margin: 15px 0;
                padding-left: 30px;
            }}
            li {{
                margin: 8px 0;
            }}
            strong {{
                color: #2c3e50;
            }}
            @media print {{
                body {{
                    margin: 0;
                    padding: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # 出力ファイル名
    if output_pdf is None:
        md_path = Path(md_file)
        output_pdf = md_path.parent / f"{md_path.stem}.pdf"

    # PlaywrightでPDF生成
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(full_html)

        # PDF生成オプション
        page.pdf(
            path=str(output_pdf),
            format='A4',
            margin={
                'top': '20mm',
                'right': '15mm',
                'bottom': '20mm',
                'left': '15mm'
            },
            print_background=True
        )

        browser.close()

    print(f"✅ PDF変換完了: {output_pdf}")
    return output_pdf


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python md_to_pdf.py <markdown_file> [output_pdf]")
        sys.exit(1)

    md_file = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else None

    convert_md_to_pdf(md_file, output_pdf)
