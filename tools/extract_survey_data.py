#!/usr/bin/env python3
"""
かんぽ生命 PoCアンケート自動読み取り＆Google Sheets出力スクリプト

【処理フロー】
1. Google Driveフォルダから27名分のPDFファイル（9ファイル×3名）を取得
2. 各PDFを画像変換（1人2ページ）
3. Claude Vision APIで手書きアンケートを読み取り
4. Google Sheetsに4シート構成で出力
   - ① rawデータ
   - ② 設問別集計
   - ③ 自由記述一覧
   - ④ エラーログ
"""

import os
import sys
import json
import io
import base64
import re
import statistics
from collections import defaultdict
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

try:
    from pdf2image import convert_from_bytes
except ImportError:
    print("❌ pdf2image がインストールされていません")
    print("   pip3 install --user pdf2image")
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("❌ anthropic がインストールされていません")
    print("   pip3 install --user anthropic")
    sys.exit(1)

# 設定
TOKEN_FILE = os.path.expanduser('~/.config/claude-code/gdrive/token.json')
FOLDER_ID = "1GLnSezSNgWBhwYDvka3KgZ1ghEK8O9aM"  # 青森支店フォルダ
OUTPUT_DIR = "output"

# Claude Vision API用プロンプト
EXTRACTION_PROMPT = """
このアンケート用紙2枚（1人分）を読み取り、JSONのみを返してください。
前置き・説明文・コードブロックは不要です。

読み取りルール：
- 丸印（○）が付いている数字を正確に読み取る
- Q1〜Q8はスケール回答（丸が付いている数値）
- Q9は行動変容の手書き自由記述（ページ2の「具体的にどのような行動を変えようと思いましたか？」欄）
- Q10はNPS（0〜10の数値）
- Q11は阻害要因（1〜5の数値）
- Q12〜Q14は任意の手書き自由記述欄（空白なら null）
- 手書き文字は最善努力で読み取り、判読不能箇所は[判読不能]と記載
- 設問セクションの見出しは以下の通り：
  P1: ■全体を通しての評価(Q1-3) ■物語への没入度と共感(Q4) ■接客に対する「気づき」と自己客観視(Q5-6)
  P2: ■行動変容への意志(Q7-9) ■導入推薦度(Q10) ■行動変容の阻害要因(Q11) ■自由記述(Q12-14)

{
  "story_title": "物語タイトル（例: CX通信19-6 魔法の絵の具と大きなカバン）",
  "gender": "男性 または 女性",
  "age_group": "20代/30代/40代/50代/60代 のいずれか",
  "Q1_inspiring": 整数(1-4),
  "Q2_story_flow": 整数(1-4),
  "Q3_recommend_others": 整数(1-4),
  "Q4_character_empathy": 整数(1-4),
  "Q5_cx_reflection": 整数(1-4),
  "Q6_compassion_empathy": 整数(1-4),
  "Q7_want_to_change": 整数(1-4),
  "Q8_continue_with_confidence": 整数(1-4),
  "Q9_specific_action_text": "手書き自由記述 または null",
  "Q10_nps": 整数(0-10),
  "Q11_not_applicable": 整数(1-5),
  "Q12_insights_unnatural": "自由記述テキスト または null",
  "Q13_barriers_to_practice": "自由記述テキスト または null",
  "Q14_other_cx_importance": "自由記述テキスト または null"
}
"""


def get_drive_service():
    """Google Drive APIサービスを取得"""
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def get_sheets_service():
    """Google Sheets APIサービスを取得"""
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('sheets', 'v4', credentials=creds)


def list_pdf_files(drive_service):
    """フォルダ内のPDFファイル一覧を取得（名前順）"""
    query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
    results = drive_service.files().list(
        q=query,
        pageSize=100,
        fields="files(id, name)",
        orderBy="name",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    return results.get('files', [])


def img_to_base64(img):
    """PIL画像をbase64エンコード"""
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.standard_b64encode(buf.getvalue()).decode()


def extract_one_respondent(client, page1, page2):
    """Claude Vision APIで1人分のアンケートを読み取り"""
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_to_base64(page1)
                    }
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_to_base64(page2)
                    }
                },
                {"type": "text", "text": EXTRACTION_PROMPT}
            ]
        }]
    )

    text = response.content[0].text.strip()
    # コードブロックを除去
    text = re.sub(r'^```[a-z]*\n?', '', text, flags=re.MULTILINE)
    text = text.rstrip('`').strip()

    return json.loads(text)


def process_all_pdfs(drive_service, anthropic_client):
    """全PDFファイルを処理してデータ抽出"""
    pdf_files = list_pdf_files(drive_service)

    if not pdf_files:
        print("❌ PDFファイルが見つかりませんでした")
        return [], []

    print(f"\n取得PDFファイル数: {len(pdf_files)} 件")
    for f in pdf_files:
        print(f"  - {f['name']}")

    all_data = []
    error_log = []

    for pdf_file in pdf_files:
        print(f"\n{'=' * 80}")
        print(f"処理中: {pdf_file['name']}")
        print('=' * 80)

        # PDFダウンロード
        request = drive_service.files().get_media(fileId=pdf_file['id'])
        pdf_bytes = request.execute()

        # PDF→画像変換
        print("  PDF→画像変換中...")
        images = convert_from_bytes(pdf_bytes, dpi=200)
        print(f"  ページ数: {len(images)}ページ（{len(images)//2}名分）")

        # 2ページずつ処理
        for i in range(0, len(images), 2):
            if i + 1 >= len(images):
                print(f"  ⚠️  ページ{i+1}がペアになっていません（スキップ）")
                break

            respondent_num = len(all_data) + 1

            try:
                print(f"  [{respondent_num}人目] Claude Vision APIで読み取り中...", end=' ')
                data = extract_one_respondent(anthropic_client, images[i], images[i+1])
                data['respondent_id'] = respondent_num
                data['source_file'] = pdf_file['name']
                data['source_pages'] = f"p{i+1}-p{i+2}"
                all_data.append(data)

                print(f"✓ {data.get('story_title', '?')} / {data.get('gender', '?')} / {data.get('age_group', '?')}")

            except Exception as e:
                print(f"✗ エラー: {e}")
                error_log.append({
                    'respondent_id': respondent_num,
                    'file': pdf_file['name'],
                    'pages': f"p{i+1}-p{i+2}",
                    'error': str(e)
                })
                all_data.append({
                    'respondent_id': respondent_num,
                    'source_file': pdf_file['name'],
                    'source_pages': f"p{i+1}-p{i+2}",
                    'error': str(e)
                })

    return all_data, error_log


def nps_label(value):
    """NPS値から区分ラベルを返す"""
    if value is None or not isinstance(value, (int, float)):
        return ''
    if value <= 6:
        return '批判者(0-6)'
    if value <= 8:
        return '中立者(7-8)'
    return '推薦者(9-10)'


def avg(data_list, key):
    """指定キーの平均値を計算"""
    vals = [d[key] for d in data_list if isinstance(d.get(key), (int, float))]
    return round(statistics.mean(vals), 2) if vals else ''


def create_google_sheet(sheets_service, all_data, error_log):
    """Google Sheetsを作成してデータを書き込み"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    title = f"かんぽ生命 PoCアンケート集計（青森支店）_{timestamp}"

    # スプレッドシート新規作成
    print("\nGoogle Sheets作成中...")
    ss = sheets_service.spreadsheets().create(body={
        'properties': {'title': title},
        'sheets': [
            {'properties': {'title': '① rawデータ'}},
            {'properties': {'title': '② 設問別集計'}},
            {'properties': {'title': '③ 自由記述一覧'}},
            {'properties': {'title': '④ エラーログ'}}
        ]
    }).execute()

    ss_id = ss['spreadsheetId']
    print(f"  作成完了: {ss_id}")

    # ========== ① rawデータ ==========
    print("  ① rawデータシート書き込み中...")
    HEADERS = [
        '回答者ID', 'ファイル名', 'ページ', '物語タイトル', '性別', '年代',
        'Q1_感動・気づき(1-4)', 'Q2_話の流れ納得(1-4)', 'Q3_他者推薦(1-4)',
        'Q4_登場人物共感(1-4)',
        'Q5_CX振り返りきっかけ(1-4)', 'Q6_寄り添い方共感(1-4)',
        'Q7_変えてみたい(1-4)', 'Q8_自信を持って継続(1-4)',
        'Q9_具体的行動変容【手書き】',
        'Q10_NPS導入推薦度(0-10)', 'Q10_NPS区分',
        'Q11_業務非該当感・阻害要因(1-5)',
        'Q12_なるほど・不自然【自由記述】',
        'Q13_実践の障害【自由記述】',
        'Q14_接客で重要なこと【自由記述】'
    ]

    rows = [HEADERS]
    for d in all_data:
        rows.append([
            d.get('respondent_id', ''), d.get('source_file', ''), d.get('source_pages', ''),
            d.get('story_title', ''), d.get('gender', ''), d.get('age_group', ''),
            d.get('Q1_inspiring', ''), d.get('Q2_story_flow', ''), d.get('Q3_recommend_others', ''),
            d.get('Q4_character_empathy', ''),
            d.get('Q5_cx_reflection', ''), d.get('Q6_compassion_empathy', ''),
            d.get('Q7_want_to_change', ''), d.get('Q8_continue_with_confidence', ''),
            d.get('Q9_specific_action_text') or '',
            d.get('Q10_nps', ''), nps_label(d.get('Q10_nps')),
            d.get('Q11_not_applicable', ''),
            d.get('Q12_insights_unnatural') or '',
            d.get('Q13_barriers_to_practice') or '',
            d.get('Q14_other_cx_importance') or ''
        ])

    sheets_service.spreadsheets().values().update(
        spreadsheetId=ss_id, range='① rawデータ!A1',
        valueInputOption='RAW', body={'values': rows}
    ).execute()

    # ========== ② 設問別集計 ==========
    print("  ② 設問別集計シート書き込み中...")
    by_story = defaultdict(list)
    for d in all_data:
        if d.get('story_title') and 'error' not in d:
            by_story[d['story_title']].append(d)

    SCORE_KEYS = [
        'Q1_inspiring', 'Q2_story_flow', 'Q3_recommend_others',
        'Q4_character_empathy',
        'Q5_cx_reflection', 'Q6_compassion_empathy',
        'Q7_want_to_change', 'Q8_continue_with_confidence',
        'Q10_nps', 'Q11_not_applicable'
    ]
    SCORE_LABELS = [
        'Q1_感動・気づき', 'Q2_話の流れ納得', 'Q3_他者推薦',
        'Q4_登場人物共感',
        'Q5_CX振り返り', 'Q6_寄り添い方共感',
        'Q7_変えてみたい', 'Q8_自信を持って継続',
        'Q10_NPS平均', 'Q11_阻害要因'
    ]

    summary_rows = [
        ['物語タイトル'] + SCORE_LABELS + ['回答数', 'NPS推薦者%', 'NPS中立者%', 'NPS批判者%', 'NPS(推薦者-批判者)']
    ]

    all_respondents = [d for d in all_data if d.get('story_title') and 'error' not in d]

    for story in sorted(by_story.keys()):
        group = by_story[story]
        nps_vals = [d['Q10_nps'] for d in group if isinstance(d.get('Q10_nps'), (int, float))]
        n = len(group)
        promoters = sum(1 for v in nps_vals if v >= 9)
        neutrals = sum(1 for v in nps_vals if 7 <= v <= 8)
        detractors = sum(1 for v in nps_vals if v <= 6)
        nps_score = round((promoters - detractors) / len(nps_vals) * 100, 1) if nps_vals else ''

        row = [story] + [avg(group, k) for k in SCORE_KEYS] + [
            n,
            f"{promoters/n*100:.0f}%" if n else '',
            f"{neutrals/n*100:.0f}%" if n else '',
            f"{detractors/n*100:.0f}%" if n else '',
            nps_score
        ]
        summary_rows.append(row)

    # 全体行
    n_all = len(all_respondents)
    if n_all > 0:
        nps_all = [d['Q10_nps'] for d in all_respondents if isinstance(d.get('Q10_nps'), (int, float))]
        p_all = sum(1 for v in nps_all if v >= 9)
        ne_all = sum(1 for v in nps_all if 7 <= v <= 8)
        d_all = sum(1 for v in nps_all if v <= 6)
        summary_rows.append(
            ['【全体】'] + [avg(all_respondents, k) for k in SCORE_KEYS] + [
                n_all,
                f"{p_all/n_all*100:.0f}%" if n_all else '',
                f"{ne_all/n_all*100:.0f}%" if n_all else '',
                f"{d_all/n_all*100:.0f}%" if n_all else '',
                round((p_all - d_all) / len(nps_all) * 100, 1) if nps_all else ''
            ]
        )

    sheets_service.spreadsheets().values().update(
        spreadsheetId=ss_id, range='② 設問別集計!A1',
        valueInputOption='RAW', body={'values': summary_rows}
    ).execute()

    # ========== ③ 自由記述一覧 ==========
    print("  ③ 自由記述一覧シート書き込み中...")
    FREE_HEADERS = [
        '回答者ID', '物語タイトル', '性別', '年代',
        'Q9_具体的行動変容', 'Q12_なるほど・不自然', 'Q13_実践の障害', 'Q14_接客で重要なこと'
    ]
    free_rows = [FREE_HEADERS]

    for d in all_data:
        if 'error' in d:
            continue
        q9 = d.get('Q9_specific_action_text')
        q12 = d.get('Q12_insights_unnatural')
        q13 = d.get('Q13_barriers_to_practice')
        q14 = d.get('Q14_other_cx_importance')
        if any([q9, q12, q13, q14]):
            free_rows.append([
                d.get('respondent_id', ''), d.get('story_title', ''),
                d.get('gender', ''), d.get('age_group', ''),
                q9 or '', q12 or '', q13 or '', q14 or ''
            ])

    sheets_service.spreadsheets().values().update(
        spreadsheetId=ss_id, range='③ 自由記述一覧!A1',
        valueInputOption='RAW', body={'values': free_rows}
    ).execute()

    # ========== ④ エラーログ ==========
    if error_log:
        print("  ④ エラーログシート書き込み中...")
        err_rows = [['回答者ID', 'ファイル名', 'ページ', 'エラー内容']]
        for e in error_log:
            err_rows.append([e['respondent_id'], e['file'], e['pages'], e['error']])
        sheets_service.spreadsheets().values().update(
            spreadsheetId=ss_id, range='④ エラーログ!A1',
            valueInputOption='RAW', body={'values': err_rows}
        ).execute()

    return ss_id


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description='かんぽ生命 PoCアンケート自動読み取り & Google Sheets出力')
    parser.add_argument('--api-key', help='Anthropic APIキー（環境変数 ANTHROPIC_API_KEY でも可）')
    args = parser.parse_args()

    print("=" * 80)
    print("かんぽ生命 PoCアンケート自動読み取り & Google Sheets出力")
    print("=" * 80)

    # APIキー確認
    api_key = args.api_key or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n❌ エラー: ANTHROPIC_API_KEY が設定されていません")
        print("\n以下のいずれかの方法で設定してください:")
        print("  1. 環境変数: export ANTHROPIC_API_KEY='your-api-key-here'")
        print("  2. 引数指定: python3 extract_survey_data.py --api-key 'your-api-key-here'")
        sys.exit(1)

    # サービス初期化
    drive_service = get_drive_service()
    sheets_service = get_sheets_service()
    anthropic_client = anthropic.Anthropic(api_key=api_key)

    # PDF処理
    all_data, error_log = process_all_pdfs(drive_service, anthropic_client)

    if not all_data:
        print("\n❌ データが取得できませんでした")
        return

    # 結果サマリー
    print("\n" + "=" * 80)
    print("処理完了サマリー")
    print("=" * 80)
    print(f"総回答者数: {len(all_data)} 名")
    print(f"エラー件数: {len(error_log)} 件")

    # 判読不能チェック
    unreadable = []
    for d in all_data:
        for key, val in d.items():
            if isinstance(val, str) and '[判読不能]' in val:
                unreadable.append({
                    'respondent_id': d.get('respondent_id'),
                    'question': key,
                    'text': val
                })

    if unreadable:
        print(f"\n【判読不能箇所】 {len(unreadable)} 件")
        for u in unreadable:
            print(f"  回答者{u['respondent_id']} / {u['question']}: {u['text'][:50]}...")

    # Google Sheets出力
    ss_id = create_google_sheet(sheets_service, all_data, error_log)

    # 最終結果
    print("\n" + "=" * 80)
    print("✅ 完了！")
    print("=" * 80)
    print(f"スプレッドシートURL: https://docs.google.com/spreadsheets/d/{ss_id}")
    print(f"処理回答者数: {len(all_data)} 名")
    print(f"判読不能箇所: {len(unreadable)} 件")
    print(f"エラー: {len(error_log)} 件")

    # ローカルにもJSONで保存
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_json = os.path.join(OUTPUT_DIR, f'survey_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            'all_data': all_data,
            'error_log': error_log,
            'unreadable': unreadable
        }, f, indent=2, ensure_ascii=False)
    print(f"\nローカルバックアップ: {output_json}")


if __name__ == '__main__':
    main()
