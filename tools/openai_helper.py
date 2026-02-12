#!/usr/bin/env python3
"""
OpenAI Helper (ChatGPT)
GPT-4/GPT-3.5を使用した記事執筆、要約、分析
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

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'


def call_openai(prompt, model='gpt-4o-mini', max_tokens=4000, temperature=0.7, system_message=None):
    """OpenAI APIを呼び出す"""
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in environment variables")
        sys.exit(1)

    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }

    messages = []

    if system_message:
        messages.append({
            'role': 'system',
            'content': system_message
        })
    else:
        messages.append({
            'role': 'system',
            'content': 'あなたはえほんインク（AIパーソナライズ絵本事業）の専門アシスタントです。'
        })

    messages.append({
        'role': 'user',
        'content': prompt
    })

    data = {
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature
    }

    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        sys.exit(1)


def write_article(topic, target_audience='一般', word_count=1500, model='gpt-4o'):
    """記事を執筆する"""
    prompt = f"""
    以下の条件で記事を執筆してください：

    【記事テーマ】
    {topic}

    【ターゲット読者】
    {target_audience}

    【文字数】
    約{word_count}文字

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
    return call_openai(prompt, model=model, max_tokens=4000)


def summarize_text(text, max_length=300):
    """テキストを要約する"""
    prompt = f"""
    以下のテキストを{max_length}文字程度で要約してください。
    重要なポイントを箇条書きで含めてください。

    【テキスト】
    {text}
    """
    return call_openai(prompt, model='gpt-4o-mini', max_tokens=1000)


def analyze_competitor(company_name, focus='全体'):
    """競合企業を分析する"""
    prompt = f"""
    以下の企業について、えほんインクの競合として分析してください：

    【企業名】
    {company_name}

    【分析フォーカス】
    {focus}

    【分析項目】
    1. 事業概要とターゲット顧客
    2. 製品・サービスの特徴
    3. 強みと弱み
    4. えほんインクとの差別化ポイント
    5. 学べる点・参考にすべき点
    6. 対抗戦略の提案

    具体的かつ実践的な分析を提供してください。
    """
    return call_openai(prompt, model='gpt-4o', max_tokens=3000)


def generate_social_media_post(topic, platform='X', tone='informative'):
    """SNS投稿を生成する"""
    platform_specs = {
        'X': '280文字以内、ハッシュタグ2-3個',
        'Instagram': '2200文字以内、ハッシュタグ10-15個、絵文字使用',
        'Facebook': '自由、詳細な説明を含める',
        'LinkedIn': 'プロフェッショナルなトーン、1300文字程度'
    }

    spec = platform_specs.get(platform, platform_specs['X'])

    prompt = f"""
    以下のトピックについて、{platform}用の投稿を生成してください：

    【トピック】
    {topic}

    【プラットフォーム】
    {platform}（{spec}）

    【トーン】
    {tone}

    【要件】
    - えほんインク事業との関連を示す
    - エンゲージメントを高める要素を含める
    - 適切なハッシュタグを含める

    3つのバリエーションを生成してください。
    """
    return call_openai(prompt, model='gpt-4o-mini', max_tokens=1500)


def improve_text(text, focus='全体'):
    """テキストを改善する"""
    prompt = f"""
    以下のテキストを改善してください。

    【改善フォーカス】
    {focus}

    【元のテキスト】
    {text}

    【改善ポイント】
    1. 読みやすさの向上
    2. 論理展開の明確化
    3. 具体例の追加
    4. エンゲージメント向上

    改善したテキストと、主な変更点を箇条書きで説明してください。
    """
    return call_openai(prompt, model='gpt-4o', max_tokens=3000)


def brainstorm_ideas(theme, count=10):
    """アイデアをブレインストーミング"""
    prompt = f"""
    以下のテーマについて、{count}個のアイデアをブレインストーミングしてください：

    【テーマ】
    {theme}

    【要件】
    - えほんインク事業に関連する
    - 実現可能性を考慮
    - 革新的かつ実用的
    - 各アイデアに簡単な説明を添える

    アイデアを番号付きリストで出力してください。
    """
    return call_openai(prompt, model='gpt-4o', max_tokens=2000)


def translate_text(text, target_language='English'):
    """テキストを翻訳する"""
    prompt = f"""
    以下のテキストを{target_language}に翻訳してください。
    自然で流暢な表現を心がけてください。

    【テキスト】
    {text}
    """
    return call_openai(prompt, model='gpt-4o-mini', max_tokens=2000)


def save_output(content, filename=None, subdir='openai'):
    """出力をファイルに保存"""
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'output_{timestamp}.md'

    output_dir = Path(__file__).parent.parent / 'output' / subdir
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✅ 出力を保存: {output_path}")
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python openai_helper.py write <topic>              # 記事執筆")
        print("  python openai_helper.py summarize <text_or_file>   # テキスト要約")
        print("  python openai_helper.py analyze <company_name>     # 競合分析")
        print("  python openai_helper.py social <platform> <topic>  # SNS投稿生成")
        print("  python openai_helper.py improve <text_or_file>     # テキスト改善")
        print("  python openai_helper.py brainstorm <theme>         # アイデア生成")
        print("  python openai_helper.py translate <text_or_file>   # 翻訳")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'write' and len(sys.argv) > 2:
        topic = ' '.join(sys.argv[2:])
        print(f"\n📝 記事執筆中: {topic}\n")
        result = write_article(topic)
        print(result)
        print("\n保存しますか？ (y/n): ", end='')
        if input().lower() == 'y':
            save_output(result)

    elif command == 'summarize' and len(sys.argv) > 2:
        input_text = ' '.join(sys.argv[2:])
        # ファイルパスの場合は読み込む
        if os.path.exists(input_text):
            with open(input_text, 'r', encoding='utf-8') as f:
                input_text = f.read()
        print(f"\n📊 要約中...\n")
        result = summarize_text(input_text)
        print(result)

    elif command == 'analyze' and len(sys.argv) > 2:
        company = ' '.join(sys.argv[2:])
        print(f"\n🔍 競合分析中: {company}\n")
        result = analyze_competitor(company)
        print(result)
        print("\n保存しますか？ (y/n): ", end='')
        if input().lower() == 'y':
            save_output(result, f'analysis_{company}.md')

    elif command == 'social' and len(sys.argv) > 3:
        platform = sys.argv[2]
        topic = ' '.join(sys.argv[3:])
        print(f"\n📱 {platform}投稿生成中: {topic}\n")
        result = generate_social_media_post(topic, platform)
        print(result)

    elif command == 'improve' and len(sys.argv) > 2:
        input_text = ' '.join(sys.argv[2:])
        if os.path.exists(input_text):
            with open(input_text, 'r', encoding='utf-8') as f:
                input_text = f.read()
        print(f"\n✨ テキスト改善中...\n")
        result = improve_text(input_text)
        print(result)

    elif command == 'brainstorm' and len(sys.argv) > 2:
        theme = ' '.join(sys.argv[2:])
        print(f"\n💡 アイデア生成中: {theme}\n")
        result = brainstorm_ideas(theme)
        print(result)

    elif command == 'translate' and len(sys.argv) > 2:
        input_text = ' '.join(sys.argv[2:])
        if os.path.exists(input_text):
            with open(input_text, 'r', encoding='utf-8') as f:
                input_text = f.read()
        print(f"\n🌐 翻訳中...\n")
        result = translate_text(input_text)
        print(result)

    else:
        print("Invalid command or missing arguments")
        sys.exit(1)
