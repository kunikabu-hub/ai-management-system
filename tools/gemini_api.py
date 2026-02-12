#!/usr/bin/env python3
"""
Gemini API Helper
Google Gemini APIを使用した記事執筆支援
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = 'gemini-2.5-flash'
GEMINI_API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent'


def call_gemini(prompt, temperature=0.7):
    """Gemini APIを呼び出す"""
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not found in environment variables")
        sys.exit(1)

    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        'contents': [
            {
                'parts': [
                    {
                        'text': prompt
                    }
                ]
            }
        ],
        'generationConfig': {
            'temperature': temperature,
            'topK': 40,
            'topP': 0.95,
            'maxOutputTokens': 8192,
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        sys.exit(1)


def write_article(topic, target_audience='一般', word_count=1500, tone='informative'):
    """記事を執筆する"""
    prompt = f"""
    あなたはえほんインク（AIパーソナライズ絵本事業）の専門ライターです。
    以下の条件で記事を執筆してください：

    【記事テーマ】
    {topic}

    【ターゲット読者】
    {target_audience}

    【文字数】
    約{word_count}文字

    【トーン】
    {tone}

    【要件】
    1. 読者の興味を引く導入部
    2. 論理的な構成（序論・本論・結論）
    3. えほんインク事業との関連性を自然に織り込む
    4. 具体例やデータを含める
    5. 行動を促すCTA（Call to Action）を含める
    6. SEOを意識した見出し構成

    【出力形式】
    - タイトル（H1）
    - リード文
    - 見出し（H2, H3）付きの本文
    - まとめ
    - CTA

    マークダウン形式で出力してください。
    """
    return call_gemini(prompt)


def improve_article(article_text, focus='全体'):
    """既存の記事を改善する"""
    prompt = f"""
    以下の記事を改善してください。

    【改善フォーカス】
    {focus}

    【元の記事】
    {article_text}

    【改善ポイント】
    1. 読みやすさの向上
    2. 論理展開の明確化
    3. 具体例の追加
    4. SEO最適化
    5. エンゲージメント向上

    改善した記事をマークダウン形式で出力し、主な変更点も箇条書きで説明してください。
    """
    return call_gemini(prompt)


def generate_outline(topic, sections=5):
    """記事のアウトラインを生成する"""
    prompt = f"""
    以下のテーマで記事のアウトラインを作成してください：

    【テーマ】
    {topic}

    【セクション数】
    {sections}個の主要セクション

    【要件】
    - 各セクションに2-3個のサブトピックを含める
    - えほんインク事業との関連性を示す
    - 読者の関心を引く構成にする
    - SEOキーワードを自然に配置する

    アウトラインをマークダウン形式で出力してください。
    """
    return call_gemini(prompt)


def save_article(content, filename=None):
    """記事をファイルに保存"""
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"article_{timestamp}.md"

    output_dir = Path(__file__).parent.parent / 'output' / 'articles'
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✅ 記事を保存しました: {output_path}")
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python gemini_api.py write <topic>           # 記事を執筆")
        print("  python gemini_api.py outline <topic>         # アウトライン生成")
        print("  python gemini_api.py improve <file>          # 記事を改善")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'write' and len(sys.argv) > 2:
        topic = ' '.join(sys.argv[2:])
        print(f"\n📝 記事執筆中: {topic}\n")
        result = write_article(topic)
        print(result)

        # 保存するか確認
        print("\n記事を保存しますか？ (y/n): ", end='')
        if input().lower() == 'y':
            save_article(result)

    elif command == 'outline' and len(sys.argv) > 2:
        topic = ' '.join(sys.argv[2:])
        print(f"\n📋 アウトライン生成中: {topic}\n")
        result = generate_outline(topic)
        print(result)

    elif command == 'improve' and len(sys.argv) > 2:
        file_path = sys.argv[2]
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

        with open(file_path, 'r', encoding='utf-8') as f:
            article_text = f.read()

        print(f"\n✨ 記事改善中: {file_path}\n")
        result = improve_article(article_text)
        print(result)

        # 保存するか確認
        print("\n改善版を保存しますか？ (y/n): ", end='')
        if input().lower() == 'y':
            filename = f"improved_{Path(file_path).name}"
            save_article(result, filename)

    else:
        print("Invalid command or missing arguments")
        sys.exit(1)
