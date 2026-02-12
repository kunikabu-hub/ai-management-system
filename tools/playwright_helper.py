#!/usr/bin/env python3
"""
Playwright Helper
Web自動化・スクレイピング・スクリーンショット
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright


def take_screenshot(url, output_path=None, full_page=True):
    """指定URLのスクリーンショットを取得"""
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(__file__).parent.parent / 'output' / 'screenshots'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f'screenshot_{timestamp}.png'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(output_path), full_page=full_page)
        browser.close()

    print(f"✅ スクリーンショット保存: {output_path}")
    return output_path


def scrape_text(url, selector=None):
    """指定URLからテキストを抽出"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state('networkidle')

        if selector:
            content = page.locator(selector).all_text_contents()
        else:
            content = page.content()

        browser.close()
        return content


def monitor_competitor(url, output_file=None):
    """競合サイトをモニタリング（スクリーンショット+テキスト抽出）"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # スクリーンショット
    screenshot_dir = Path(__file__).parent.parent / 'output' / 'competitor_monitoring'
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshot_dir / f'{timestamp}_screenshot.png'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state('networkidle')

        # スクリーンショット
        page.screenshot(path=str(screenshot_path), full_page=True)

        # ページ情報取得
        title = page.title()
        content = page.content()

        # メタ情報取得
        meta_description = page.locator('meta[name="description"]').get_attribute('content') or ''
        meta_keywords = page.locator('meta[name="keywords"]').get_attribute('content') or ''

        browser.close()

    # 結果を保存
    result = {
        'timestamp': timestamp,
        'url': url,
        'title': title,
        'meta_description': meta_description,
        'meta_keywords': meta_keywords,
        'screenshot': str(screenshot_path)
    }

    if output_file is None:
        output_file = screenshot_dir / f'{timestamp}_data.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ モニタリング完了:")
    print(f"  - スクリーンショット: {screenshot_path}")
    print(f"  - データ: {output_file}")
    print(f"  - タイトル: {title}")
    print(f"  - 説明: {meta_description[:100]}...")

    return result


def check_website_status(url):
    """ウェブサイトの状態をチェック"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            response = page.goto(url)
            page.wait_for_load_state('networkidle')

            status = {
                'url': url,
                'status_code': response.status,
                'status_text': response.status_text,
                'title': page.title(),
                'load_time': page.evaluate('() => performance.timing.loadEventEnd - performance.timing.navigationStart'),
                'timestamp': datetime.now().isoformat()
            }

            browser.close()
            return status

        except Exception as e:
            browser.close()
            return {
                'url': url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def fill_form_example(url, form_data):
    """フォーム入力例（カスタマイズ可能）"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # ヘッドレスモードOFF（確認用）
        page = browser.new_page()
        page.goto(url)

        # フォーム入力（例）
        for selector, value in form_data.items():
            page.fill(selector, value)

        print("フォーム入力完了（確認用ブラウザを5秒間表示）")
        page.wait_for_timeout(5000)

        browser.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python playwright_helper.py screenshot <url>        # スクリーンショット")
        print("  python playwright_helper.py scrape <url>           # テキスト抽出")
        print("  python playwright_helper.py monitor <url>          # 競合モニタリング")
        print("  python playwright_helper.py status <url>           # サイト状態確認")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'screenshot' and len(sys.argv) > 2:
        url = sys.argv[2]
        take_screenshot(url)

    elif command == 'scrape' and len(sys.argv) > 2:
        url = sys.argv[2]
        content = scrape_text(url)
        print(content)

    elif command == 'monitor' and len(sys.argv) > 2:
        url = sys.argv[2]
        monitor_competitor(url)

    elif command == 'status' and len(sys.argv) > 2:
        url = sys.argv[2]
        status = check_website_status(url)
        print(json.dumps(status, indent=2, ensure_ascii=False))

    else:
        print("Invalid command or missing arguments")
        sys.exit(1)
