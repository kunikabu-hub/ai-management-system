#!/usr/bin/env python3
"""
かんぽ生命PoC：脚本AI自動採点システム
脚本ファイルを読み込み、Claude APIで採点し、Googleスプレッドシートに出力
"""

import os
import json
import anthropic
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# 設定
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
TOKEN_PATH = os.path.expanduser('~/.config/claude-code/gdrive/token.json')
SCORING_PROMPT_PATH = 'tools/kanpo_script_scoring_prompt.md'

# スプレッドシートID（後で設定）
SPREADSHEET_ID = None  # 初回実行時に作成


def load_scoring_prompt():
    """採点プロンプトを読み込む"""
    with open(SCORING_PROMPT_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def score_script(script_text, script_name):
    """
    Claudeを使って脚本を採点

    Args:
        script_text: 脚本のテキスト
        script_name: 脚本の名前

    Returns:
        dict: 採点結果（JSON）
    """
    # プロンプトテンプレートを読み込み
    prompt_template = load_scoring_prompt()

    # 脚本テキストを埋め込み
    prompt = prompt_template.replace('<<SCRIPT_TEXT>>', script_text)

    # Claude APIで採点
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    print(f"📊 採点中: {script_name}")

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # レスポンスからJSONを抽出
    response_text = message.content[0].text

    # JSONのみを抽出（前後の説明文を除去）
    import re
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        json_text = json_match.group()
        result = json.loads(json_text)
    else:
        result = json.loads(response_text)

    return result


def create_or_get_spreadsheet():
    """Googleスプレッドシートを作成または取得"""
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    service = build('sheets', 'v4', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)

    # スプレッドシートのタイトル
    title = f"かんぽ脚本AI採点結果_{datetime.now().strftime('%Y%m%d')}"

    # 既存のスプレッドシートを検索
    query = f"name='{title}' and mimeType='application/vnd.google-apps.spreadsheet'"
    results = drive_service.files().list(q=query, fields='files(id, name)').execute()
    files = results.get('files', [])

    if files:
        spreadsheet_id = files[0]['id']
        print(f"✅ 既存のスプレッドシートを使用: {spreadsheet_id}")
    else:
        # 新規作成
        spreadsheet = {
            'properties': {'title': title},
            'sheets': [
                {'properties': {'title': 'サマリー'}},
                {'properties': {'title': '詳細結果'}},
                {'properties': {'title': '感情曲線'}}
            ]
        }

        spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = spreadsheet['spreadsheetId']
        print(f"✅ 新規スプレッドシートを作成: {spreadsheet_id}")
        print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

    return spreadsheet_id, service


def write_summary_sheet(service, spreadsheet_id, results):
    """サマリーシートに結果を書き込む"""
    # ヘッダー行
    headers = [
        ['脚本名', '総合点', 'PASS/FAIL', 'A:感情曲線', 'B:振幅', 'C:転換点', 'D:教訓臭', 'E:行動示唆', '評価日時']
    ]

    # データ行
    rows = []
    for result in results:
        scores = result['scores']
        rows.append([
            result['script_name'],
            result['total'],
            'PASS' if result['pass'] else 'FAIL',
            scores['A'],
            scores['B'],
            scores['C'],
            scores['D'],
            scores['E'],
            result['timestamp']
        ])

    # 書き込み
    data = headers + rows
    body = {'values': data}

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='サマリー!A1',
        valueInputOption='RAW',
        body=body
    ).execute()

    print(f"✅ サマリーシートに {len(rows)} 件を書き込みました")


def write_detail_sheet(service, spreadsheet_id, results):
    """詳細結果シートに結果を書き込む"""
    rows = [['脚本名', '項目', 'スコア', '引用/理由']]

    for result in results:
        script_name = result['script_name']
        scores = result['scores']
        rationales = result.get('rationales', {})

        for key, score in scores.items():
            reasons = rationales.get(key, [])
            reason_text = ' | '.join(reasons) if reasons else ''

            rows.append([
                script_name,
                f"{key}: {get_criteria_name(key)}",
                score,
                reason_text
            ])

        # 改善提案
        improvements = result.get('improvements', [])
        if improvements:
            rows.append([script_name, '改善提案', '', '\n'.join(improvements)])

        rows.append(['', '', '', ''])  # 空行

    body = {'values': rows}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='詳細結果!A1',
        valueInputOption='RAW',
        body=body
    ).execute()

    print(f"✅ 詳細結果シートに書き込みました")


def write_emotion_curve_sheet(service, spreadsheet_id, results):
    """感情曲線シートに結果を書き込む"""
    rows = [['脚本名', 'シーン', 'ラベル', '感情', '感情値']]

    for result in results:
        script_name = result['script_name']
        emotion_curve = result.get('emotion_curve', [])

        for point in emotion_curve:
            rows.append([
                script_name,
                point.get('scene', ''),
                point.get('label', ''),
                point.get('emotion', ''),
                point.get('value', 0)
            ])

        rows.append(['', '', '', '', ''])  # 空行

    body = {'values': rows}
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='感情曲線!A1',
        valueInputOption='RAW',
        body=body
    ).execute()

    print(f"✅ 感情曲線シートに書き込みました")


def get_criteria_name(key):
    """採点項目のキーから名称を取得"""
    names = {
        'A': '感情曲線設計',
        'B': '感情振幅',
        'C': '転換点の自然性',
        'D': '教訓臭・説明臭の低さ',
        'E': '行動示唆の具体性'
    }
    return names.get(key, key)


def main(script_files):
    """
    メイン処理

    Args:
        script_files: [(script_name, script_path), ...] のリスト
    """
    if not ANTHROPIC_API_KEY:
        print("❌ エラー: ANTHROPIC_API_KEY 環境変数が設定されていません")
        return

    results = []

    # 各脚本を採点
    for script_name, script_path in script_files:
        try:
            # 脚本ファイルを読み込み
            with open(script_path, 'r', encoding='utf-8') as f:
                script_text = f.read()

            # 採点実行
            score_result = score_script(script_text, script_name)

            # 結果にメタデータを追加
            score_result['script_name'] = script_name
            score_result['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            results.append(score_result)

            # 結果を表示
            print(f"\n📊 {script_name}")
            print(f"   総合点: {score_result['total']}/40")
            print(f"   判定: {'✅ PASS' if score_result['pass'] else '❌ FAIL'}")
            print(f"   内訳: A={score_result['scores']['A']} B={score_result['scores']['B']} "
                  f"C={score_result['scores']['C']} D={score_result['scores']['D']} "
                  f"E={score_result['scores']['E']}")
            print()

        except Exception as e:
            print(f"❌ エラー: {script_name} の採点に失敗しました: {e}")

    # 結果をスプレッドシートに出力
    if results:
        spreadsheet_id, service = create_or_get_spreadsheet()

        write_summary_sheet(service, spreadsheet_id, results)
        write_detail_sheet(service, spreadsheet_id, results)
        write_emotion_curve_sheet(service, spreadsheet_id, results)

        print(f"\n✅ すべての結果をスプレッドシートに出力しました")
        print(f"🔗 https://docs.google.com/spreadsheets/d/{spreadsheet_id}")

        # JSONファイルにも保存
        output_json = f"output/kanpo_scoring_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"💾 JSON形式でも保存: {output_json}")


if __name__ == '__main__':
    # 使用例
    # 提出版の3つの脚本を採点
    script_files = [
        ('生成プロット_CX通信19_6_提出版', 'path/to/script_6.txt'),
        ('生成プロット_CX通信19_7_提出版', 'path/to/script_7.txt'),
        ('生成プロット_CX通信19_15_提出版', 'path/to/script_15.txt'),
    ]

    # 実行
    # main(script_files)

    print("="*80)
    print("かんぽ脚本AI自動採点システム")
    print("="*80)
    print("\n使用方法:")
    print("1. ANTHROPIC_API_KEY 環境変数を設定")
    print("2. script_files のパスを実際のファイルパスに変更")
    print("3. main(script_files) のコメントを解除して実行")
    print("\nまたは、Pythonスクリプトから直接呼び出し:")
    print("  from auto_score_scripts import main")
    print("  main([(name, path), ...])")
