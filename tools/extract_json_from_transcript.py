#!/usr/bin/env python3
"""
エージェントトランスクリプトからJSONデータを抽出
"""
import sys
import json
import re

def extract_json(transcript_file, output_file):
    with open(transcript_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # {"respondents": で始まるJSONを探す
    pattern = r'\{"respondents":\s*\[.*?\]\s*\}'
    matches = re.findall(pattern, content, re.DOTALL)

    if not matches:
        print(f"❌ JSONデータが見つかりませんでした")
        return False

    # 最後のマッチを使用（最新のデータ）
    json_str = matches[-1]

    try:
        data = json.loads(json_str)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ JSONデータを {output_file} に保存しました")
        print(f"   回答者数: {len(data.get('respondents', []))}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析エラー: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("使用方法: python3 extract_json_from_transcript.py <transcript_file> <output_file>")
        sys.exit(1)

    extract_json(sys.argv[1], sys.argv[2])
