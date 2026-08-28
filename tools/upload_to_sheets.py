#!/usr/bin/env python3
"""
抽出したアンケートデータをGoogle Sheetsに書き込み
"""
import os
import sys
import json
import statistics
from collections import defaultdict
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_FILE = os.path.expanduser('~/.config/claude-code/gdrive/token.json')

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

def create_google_sheet(sheets_service, all_data):
    """Google Sheetsを作成してデータを書き込み"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    title = f"かんぽ生命 PoCアンケート集計（青森支店・全81名）_{timestamp}"

    # スプレッドシート新規作成
    print("\nGoogle Sheets作成中...")
    ss = sheets_service.spreadsheets().create(body={
        'properties': {'title': title},
        'sheets': [
            {'properties': {'title': '① rawデータ'}},
            {'properties': {'title': '② 設問別集計'}},
            {'properties': {'title': '③ 自由記述一覧'}},
        ]
    }).execute()

    ss_id = ss['spreadsheetId']
    print(f"  作成完了: {ss_id}")

    # ========== ① rawデータ ==========
    print("  ① rawデータシート書き込み中...")
    HEADERS = [
        '回答者ID', 'ページ', '物語タイトル', '性別', '年代',
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
        source_pages = ', '.join(d.get('source_pages', []))
        rows.append([
            d.get('respondent_id', ''), source_pages,
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
        if d.get('story_title'):
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
    all_respondents = [d for d in all_data if d.get('story_title')]
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

    return ss_id

def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description='アンケートデータをGoogle Sheetsに書き込み')
    parser.add_argument('json_file', help='JSONデータファイルのパス')
    args = parser.parse_args()

    # JSONファイル読み込み
    if not os.path.exists(args.json_file):
        print(f"❌ エラー: ファイルが見つかりません: {args.json_file}")
        sys.exit(1)

    with open(args.json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_data = data.get('respondents', [])
    if not all_data:
        print("❌ エラー: データが空です")
        sys.exit(1)

    print("=" * 80)
    print("Google Sheetsアップロード")
    print("=" * 80)
    print(f"データ件数: {len(all_data)} 名")

    # Google Sheets API
    with open(TOKEN_FILE, 'r') as f:
        token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    sheets_service = build('sheets', 'v4', credentials=creds)

    # スプレッドシート作成
    ss_id = create_google_sheet(sheets_service, all_data)

    # 最終結果
    print("\n" + "=" * 80)
    print("✅ 完了！")
    print("=" * 80)
    print(f"スプレッドシートURL: https://docs.google.com/spreadsheets/d/{ss_id}")
    print(f"処理回答者数: {len(all_data)} 名")

if __name__ == '__main__':
    main()
