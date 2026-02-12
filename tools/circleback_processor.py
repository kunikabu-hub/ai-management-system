#!/usr/bin/env python3
"""
Circleback Data Processor
受信した議事録データを処理し、適切な場所に保存する
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
MEETINGS_DIR = PROJECT_ROOT / 'output' / 'meetings'
MEMORIES_DIR = PROJECT_ROOT / '00_context' / 'memories'


def sanitize_filename(text):
    """
    ファイル名として使用できるように文字列をサニタイズ
    """
    # 不正な文字を削除
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    # 空白をアンダースコアに
    text = re.sub(r'\s+', '_', text)
    # 長さ制限
    return text[:50]


def extract_action_items(data):
    """
    アクションアイテムを抽出
    """
    action_items = data.get('action_items', [])
    if not action_items:
        return []

    items = []
    for item in action_items:
        if isinstance(item, dict):
            items.append({
                'task': item.get('task', ''),
                'assignee': item.get('assignee', ''),
                'due_date': item.get('due_date', '')
            })
        elif isinstance(item, str):
            items.append({'task': item, 'assignee': '', 'due_date': ''})

    return items


def extract_key_decisions(summary_text):
    """
    要約から重要な意思決定を抽出（簡易版）
    """
    # 決定に関連するキーワード
    decision_keywords = ['決定', '決めた', '合意', '承認', '採用', '中止', '見送り', '優先']

    decisions = []
    lines = summary_text.split('\n')

    for line in lines:
        if any(keyword in line for keyword in decision_keywords):
            decisions.append(line.strip())

    return decisions


def save_meeting_markdown(data):
    """
    議事録をMarkdownファイルとして保存
    """
    # ファイル名の生成
    meeting_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    meeting_title = data.get('title', 'Untitled Meeting')
    safe_title = sanitize_filename(meeting_title)

    filename = f"{meeting_date}_{safe_title}.md"
    filepath = MEETINGS_DIR / filename

    # 議事録の内容を生成
    content = f"""# {meeting_title}

**日時**: {meeting_date}
**Meeting ID**: {data.get('meeting_id', 'N/A')}

---

## 📝 要約

{data.get('summary', '要約がありません')}

---

## 🎯 アクションアイテム

"""

    # アクションアイテムの追加
    action_items = extract_action_items(data)
    if action_items:
        for item in action_items:
            assignee = f" (@{item['assignee']})" if item['assignee'] else ""
            due_date = f" [期限: {item['due_date']}]" if item['due_date'] else ""
            content += f"- [ ] {item['task']}{assignee}{due_date}\n"
    else:
        content += "なし\n"

    content += "\n---\n\n"

    # トランスクリプトの追加（存在する場合）
    if 'transcript' in data and data['transcript']:
        content += "## 💬 トランスクリプト\n\n"
        content += f"{data['transcript']}\n\n"
        content += "---\n\n"

    # インサイトの追加（存在する場合）
    if 'insights' in data and data['insights']:
        content += "## 💡 インサイト\n\n"
        insights = data['insights']
        if isinstance(insights, list):
            for insight in insights:
                content += f"- {insight}\n"
        else:
            content += f"{insights}\n"
        content += "\n---\n\n"

    # メタデータの追加
    content += "## 📎 メタデータ\n\n"
    content += f"- **録音URL**: {data.get('recording_url', 'N/A')}\n"
    content += f"- **Circlebackリンク**: https://app.circleback.ai/meeting/{data.get('meeting_id', '')}\n"

    # ファイル保存
    MEETINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 議事録を保存しました: {filepath}")
    return str(filepath)


def save_to_memory(data):
    """
    重要な意思決定をメモリに保存
    """
    summary = data.get('summary', '')
    decisions = extract_key_decisions(summary)

    if not decisions:
        return None

    # decisions.mdに追記
    decisions_file = MEMORIES_DIR / 'decisions.md'

    if not decisions_file.exists():
        return None

    # 現在の内容を読み込み
    with open(decisions_file, 'r', encoding='utf-8') as f:
        existing_content = f.read()

    # 新しいエントリーを追加
    meeting_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    meeting_title = data.get('title', 'ミーティング')

    new_entry = f"\n## {meeting_title} ({meeting_date})\n\n"
    new_entry += "**決定内容**:\n"
    for decision in decisions:
        new_entry += f"- {decision}\n"

    new_entry += f"\n**関連議事録**: [議事録リンク](../output/meetings/)\n"
    new_entry += f"\n**タグ**: #意思決定 #ミーティング\n\n---\n"

    # 最終更新日を更新
    updated_content = existing_content.replace(
        f"**最終更新**: {datetime.now().strftime('%Y-%m-%d')}",
        f"**最終更新**: {datetime.now().strftime('%Y-%m-%d')}"
    )

    # 末尾に追記
    updated_content += new_entry

    # ファイル保存
    with open(decisions_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"✅ 重要な決定をメモリに保存しました: {decisions_file}")
    return str(decisions_file)


def process_meeting_data(data):
    """
    議事録データを処理するメイン関数
    """
    try:
        saved_files = []

        # 1. 議事録をMarkdownファイルとして保存
        markdown_file = save_meeting_markdown(data)
        saved_files.append(markdown_file)

        # 2. 重要な意思決定をメモリに保存
        memory_file = save_to_memory(data)
        if memory_file:
            saved_files.append(memory_file)

        return {
            'success': True,
            'saved_files': saved_files
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    # テストデータ
    test_data = {
        'meeting_id': 'test-123',
        'title': 'えほんインク戦略ミーティング',
        'date': '2026-02-13',
        'summary': 'AIアバターへの完全シフトを決定しました。3Dアバターは今後推進しない方針です。',
        'action_items': [
            {'task': 'AIアバター生成の精度向上', 'assignee': '開発チーム', 'due_date': '2026-03-01'},
            {'task': 'ペット絵本のMVP開発', 'assignee': 'プロダクトチーム', 'due_date': '2026-03-15'}
        ],
        'transcript': 'これはテストトランスクリプトです。',
        'insights': ['AIアバターのコスト削減効果が確認された'],
        'recording_url': 'https://example.com/recording'
    }

    print("🧪 テストデータで動作確認中...")
    result = process_meeting_data(test_data)
    print(f"\n結果: {json.dumps(result, indent=2, ensure_ascii=False)}")
