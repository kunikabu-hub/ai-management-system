#!/usr/bin/env python3
"""
全バッチのJSONデータを結合
"""
import os
import json
import glob

OUTPUT_DIR = "../output"
BATCH_PATTERN = "batch_*.json"
MERGED_FILE = "extracted_survey_data_all_81.json"

def main():
    os.chdir(os.path.dirname(__file__))

    # バッチファイル一覧取得
    batch_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, BATCH_PATTERN)))

    if not batch_files:
        print(f"❌ バッチファイルが見つかりません: {OUTPUT_DIR}/{BATCH_PATTERN}")
        return

    print(f"バッチファイル数: {len(batch_files)}\n")

    all_respondents = []

    for batch_file in batch_files:
        print(f"  読み込み中: {os.path.basename(batch_file)}")

        with open(batch_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        respondents = data.get('respondents', [])
        print(f"    回答者数: {len(respondents)}")

        all_respondents.extend(respondents)

    # 回答者IDでソート
    all_respondents.sort(key=lambda x: x.get('respondent_id', 0))

    # 結合データ保存
    merged_path = os.path.join(OUTPUT_DIR, MERGED_FILE)
    with open(merged_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_respondents': len(all_respondents),
            'respondents': all_respondents
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 完了: {len(all_respondents)}名分のデータを {merged_path} に保存しました")

    # サマリー表示
    print("\n" + "=" * 80)
    print("データサマリー")
    print("=" * 80)

    # 物語別集計
    from collections import Counter
    story_counts = Counter(r.get('story_title', '不明') for r in all_respondents)
    print(f"\n【物語別回答数】")
    for story, count in sorted(story_counts.items()):
        print(f"  {story}: {count}名")

    # 性別集計
    gender_counts = Counter(r.get('gender', '不明') for r in all_respondents)
    print(f"\n【性別】")
    for gender, count in sorted(gender_counts.items()):
        print(f"  {gender}: {count}名")

    # 年代集計
    age_counts = Counter(r.get('age_group', '不明') for r in all_respondents)
    print(f"\n【年代】")
    for age, count in sorted(age_counts.items()):
        print(f"  {age}: {count}名")

    # NPS欠損チェック
    missing_nps = [r['respondent_id'] for r in all_respondents if r.get('Q10_nps') is None]
    if missing_nps:
        print(f"\n【NPS欠損】{len(missing_nps)}件: {missing_nps}")

    # 判読不能チェック
    unreadable_count = 0
    for r in all_respondents:
        for key, val in r.items():
            if isinstance(val, str) and '[判読不能]' in val:
                unreadable_count += 1

    if unreadable_count > 0:
        print(f"\n【判読不能】{unreadable_count}箇所")

if __name__ == '__main__':
    main()
