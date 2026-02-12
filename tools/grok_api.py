#!/usr/bin/env python3
"""
Grok API Helper
xAI Grok APIを使用したX/Twitterトレンド分析と投稿生成
"""

import os
import sys
import json
import requests
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

GROK_API_KEY = os.getenv('GROK_API_KEY')
GROK_API_URL = 'https://api.x.ai/v1/chat/completions'


def call_grok(prompt, model='grok-3', max_tokens=2000):
    """Grok APIを呼び出す"""
    if not GROK_API_KEY:
        print("Error: GROK_API_KEY not found in environment variables")
        sys.exit(1)

    headers = {
        'Authorization': f'Bearer {GROK_API_KEY}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'system',
                'content': 'あなたはえほんインクの経営パートナーです。X/Twitterのトレンドを分析し、事業に関連する洞察を提供します。'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'max_tokens': max_tokens,
        'temperature': 0.7
    }

    try:
        response = requests.post(GROK_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling Grok API: {e}")
        sys.exit(1)


def analyze_trend(topic):
    """指定されたトピックのトレンド分析"""
    prompt = f"""
    以下のトピックについて、X/Twitterでのトレンドを分析してください：

    トピック: {topic}

    以下の観点で分析してください：
    1. 現在の話題性（トレンドスコア）
    2. 主要な議論のポイント
    3. えほんインク事業との関連性
    4. 活用できる機会
    5. 注意すべきリスク

    分析結果を構造化して返してください。
    """
    return call_grok(prompt)


def generate_post(topic, style='informative'):
    """X/Twitter投稿を生成"""
    prompt = f"""
    以下のトピックについて、えほんインクの公式アカウント用のX投稿を生成してください：

    トピック: {topic}
    スタイル: {style}

    要件：
    - 280文字以内
    - えほんインクの事業（AIパーソナライズ絵本）との関連を示す
    - エンゲージメントを高める要素を含める
    - ハッシュタグを2-3個含める

    3つのバリエーションを生成してください。
    """
    return call_grok(prompt)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python grok_api.py analyze <topic>  # トレンド分析")
        print("  python grok_api.py post <topic>     # 投稿生成")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'analyze' and len(sys.argv) > 2:
        topic = ' '.join(sys.argv[2:])
        print(f"\n🔍 トレンド分析: {topic}\n")
        result = analyze_trend(topic)
        print(result)

    elif command == 'post' and len(sys.argv) > 2:
        topic = ' '.join(sys.argv[2:])
        print(f"\n📝 投稿生成: {topic}\n")
        result = generate_post(topic)
        print(result)

    else:
        print("Invalid command or missing arguments")
        sys.exit(1)
