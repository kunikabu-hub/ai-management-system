#!/usr/bin/env python3
"""
Wonderbly Book Preview Scraper V2
より高度なカスタマイズフロー対応版
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout
import time
import json

# 設定
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "wonderbly_screenshots_v2"
CHILD_NAME = "Hana"
LAST_NAME = "Yamada"
DEBUG = True

# 対象タイトル
BOOKS = [
    {
        "url": "https://www.wonderbly.com/personalized-products/where-are-you-book",
        "title": "where_are_you",
        "name": "Where Are You?"
    },
    {
        "url": "https://www.wonderbly.com/personalized-products/how-you-got-your-name-book",
        "title": "how_you_got_your_name",
        "name": "How You Got Your Name"
    },
    {
        "url": "https://www.wonderbly.com/personalized-products/bedtime-for-name-book",
        "title": "bedtime_for_you",
        "name": "Bedtime For You"
    }
]


def log(message, level="INFO"):
    """ログ出力"""
    if DEBUG or level == "ERROR":
        print(f"  [{level}] {message}")


async def save_debug_screenshot(page: Page, book_dir: Path, name: str):
    """デバッグ用スクリーンショット"""
    try:
        debug_path = book_dir / f"debug_{name}.png"
        await page.screenshot(path=str(debug_path), full_page=True)
        log(f"Debug screenshot saved: {name}", "DEBUG")
    except Exception as e:
        log(f"Failed to save debug screenshot: {e}", "ERROR")


async def wait_and_check(page: Page, timeout: int = 5000):
    """ページ読み込み待機"""
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=timeout)
        await asyncio.sleep(1)
    except PlaywrightTimeout:
        log("Timeout waiting for page load", "WARN")


async def click_element(page: Page, selectors: list, description: str = "element"):
    """
    複数のセレクターを試してクリック
    """
    log(f"Trying to click: {description}")

    for selector in selectors:
        try:
            # まず存在確認
            element = page.locator(selector).first
            if await element.count() > 0:
                log(f"Found {description}: {selector}")

                # 表示されるまで待つ
                await element.wait_for(state="visible", timeout=3000)

                # スクロールして表示
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)

                # クリック
                await element.click(timeout=3000)
                log(f"Clicked {description}: {selector}", "SUCCESS")
                await asyncio.sleep(2)
                return True

        except Exception as e:
            log(f"Failed with {selector}: {str(e)[:100]}", "DEBUG")
            continue

    log(f"Could not click {description}", "WARN")
    return False


async def fill_input(page: Page, selectors: list, value: str, description: str = "input"):
    """
    複数のセレクターを試して入力
    """
    log(f"Trying to fill: {description} with '{value}'")

    for selector in selectors:
        try:
            element = page.locator(selector).first
            if await element.count() > 0:
                log(f"Found {description}: {selector}")
                await element.wait_for(state="visible", timeout=3000)
                await element.fill(value)
                log(f"Filled {description}: {selector}", "SUCCESS")
                await asyncio.sleep(1)
                return True
        except Exception as e:
            log(f"Failed with {selector}: {str(e)[:100]}", "DEBUG")
            continue

    log(f"Could not fill {description}", "WARN")
    return False


async def navigate_customization_flow(page: Page, book_dir: Path):
    """
    カスタマイズフローを進める
    """
    log("Starting customization flow navigation", "INFO")

    # Step 1: 名前入力
    name_selectors = [
        'input[name="name"]',
        'input[name="firstName"]',
        'input[name="childName"]',
        'input[placeholder*="name" i]',
        'input[placeholder*="Name" i]',
        'input[type="text"]:visible',
        'input#name',
        'input#firstName'
    ]

    await save_debug_screenshot(page, book_dir, "step1_before_name")

    # First nameとLast nameを順番に入力
    filled_first = await fill_input(page, name_selectors, CHILD_NAME, "First name field")
    await asyncio.sleep(1)
    await save_debug_screenshot(page, book_dir, "step1_after_firstname")

    # Last name入力
    lastname_selectors = [
        'input[name="lastName"]',
        'input[name="lastname"]',
        'input[name="surname"]',
        'input[placeholder*="last" i]',
        'input[placeholder*="surname" i]',
        'input#lastName',
        'input#lastname'
    ]

    filled_last = await fill_input(page, lastname_selectors, LAST_NAME, "Last name field")
    await asyncio.sleep(1)
    await save_debug_screenshot(page, book_dir, "step1_after_lastname")

    # Step 2: 性別選択（Girl）
    gender_selectors = [
        'button:has-text("Girl")',
        'button:has-text("girl")',
        '[data-value="girl"]',
        '[data-value="female"]',
        'input[value="girl"]',
        'input[value="female"]',
        '[aria-label*="Girl" i]'
    ]

    await save_debug_screenshot(page, book_dir, "step2_before_gender")
    await click_element(page, gender_selectors, "Girl button")
    await save_debug_screenshot(page, book_dir, "step2_after_gender")

    # Step 3-10: Next/Continue ボタンを繰り返しクリック
    for step in range(1, 11):
        log(f"Step {step + 2}: Looking for Next/Continue button")

        next_selectors = [
            'button:has-text("Next")',
            'button:has-text("Continue")',
            'button:has-text("next")',
            'button:has-text("continue")',
            '[data-testid="next-button"]',
            '[data-testid="continue-button"]',
            'button[type="submit"]',
            '.button--primary',
            '.btn-primary',
            'button.next',
            'button.continue'
        ]

        await save_debug_screenshot(page, book_dir, f"step{step + 2}_before_next")
        clicked = await click_element(page, next_selectors, f"Next/Continue button (step {step})")
        await save_debug_screenshot(page, book_dir, f"step{step + 2}_after_next")

        if not clicked:
            log(f"No more Next buttons found at step {step}", "INFO")
            break

        await asyncio.sleep(2)

    return True


async def find_and_access_preview(page: Page, book_dir: Path):
    """
    プレビューボタンを探してアクセス
    """
    log("Searching for Preview button", "INFO")

    # プレビューボタンの多様なパターン
    preview_selectors = [
        'button:has-text("Preview")',
        'a:has-text("Preview")',
        'button:has-text("preview")',
        'button:has-text("Preview Full Book")',
        'button:has-text("See Preview")',
        'button:has-text("Preview Book")',
        '[data-testid="preview-button"]',
        '[aria-label*="Preview" i]',
        '.preview-button',
        '#preview-button',
        'button:has-text("View")',
        'button:has-text("See Book")'
    ]

    await save_debug_screenshot(page, book_dir, "before_preview_search")

    # すべてのボタンを探す
    all_buttons = await page.locator('button, a').all()
    log(f"Found {len(all_buttons)} buttons/links on page", "DEBUG")

    # テキストを含むボタンを探す
    for i, button in enumerate(all_buttons[:20]):  # 最初の20個のみチェック
        try:
            text = await button.text_content()
            if text and ('preview' in text.lower() or 'view' in text.lower()):
                log(f"Button {i}: '{text}'", "DEBUG")
        except:
            pass

    clicked = await click_element(page, preview_selectors, "Preview button")

    if clicked:
        await wait_and_check(page)
        await save_debug_screenshot(page, book_dir, "after_preview_click")
        return True

    # プレビューボタンが見つからない場合、現在のページをプレビューとみなす
    log("No Preview button found, assuming current page is preview", "WARN")
    return False


async def extract_preview_text(page: Page, book_dir: Path):
    """
    プレビューページからテキストを抽出
    """
    log("Extracting text from preview page", "INFO")

    # ページの全テキストを抽出
    try:
        page_text = await page.locator('body').text_content()
        text_file = book_dir / "preview_text.txt"
        text_file.write_text(page_text, encoding='utf-8')
        log(f"Extracted {len(page_text)} characters", "SUCCESS")
    except Exception as e:
        log(f"Failed to extract text: {e}", "ERROR")

    # ストーリー要素を探す
    story_selectors = [
        '.story-content',
        '.book-content',
        '.page-content',
        '[data-story]',
        'p',
        '.text-content'
    ]

    for selector in story_selectors:
        try:
            elements = await page.locator(selector).all()
            if elements:
                log(f"Found {len(elements)} elements with {selector}", "DEBUG")
                texts = []
                for elem in elements:
                    text = await elem.text_content()
                    if text and len(text.strip()) > 10:
                        texts.append(text.strip())

                if texts:
                    content_file = book_dir / f"content_{selector.replace('.', '').replace('[', '').replace(']', '')}.json"
                    content_file.write_text(json.dumps(texts, indent=2, ensure_ascii=False), encoding='utf-8')
                    log(f"Saved {len(texts)} text blocks", "SUCCESS")
        except Exception as e:
            log(f"Failed with {selector}: {e}", "DEBUG")


async def capture_book_pages(page: Page, book_dir: Path):
    """
    絵本の全ページをキャプチャ（改善版）
    """
    log("Starting page capture", "INFO")

    page_num = 1
    max_pages = 60

    # 初期ページ
    screenshot_path = book_dir / f"page_{page_num:03d}.png"
    await page.screenshot(path=str(screenshot_path), full_page=True)
    log(f"Page {page_num} saved", "SUCCESS")

    # ページめくりの多様な方法
    for i in range(max_pages):
        page_num = i + 2

        # 方法1: Next/Arrow ボタン
        next_selectors = [
            'button[aria-label*="Next" i]',
            'button[aria-label*="next" i]',
            'button:has-text("Next")',
            '.next-page',
            '.arrow-right',
            '[data-testid="next-page"]',
            'button.page-next',
            'svg[data-icon="arrow-right"]',
            '[aria-label="Go to next page"]'
        ]

        clicked = False
        for selector in next_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(2)
                    clicked = True
                    log(f"Clicked next button: {selector}", "DEBUG")
                    break
            except:
                continue

        # 方法2: 右側をクリック
        if not clicked:
            try:
                await page.mouse.click(1200, 500)
                await asyncio.sleep(2)
                log("Clicked right side of page", "DEBUG")
            except:
                pass

        # 方法3: キーボード操作
        if not clicked:
            try:
                await page.keyboard.press("ArrowRight")
                await asyncio.sleep(2)
                log("Pressed ArrowRight key", "DEBUG")
            except:
                pass

        # スクリーンショット
        screenshot_path = book_dir / f"page_{page_num:03d}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        log(f"Page {page_num} saved", "SUCCESS")

        # 終了判定（URLの変化をチェック）
        current_url = page.url
        if 'thank' in current_url.lower() or 'checkout' in current_url.lower():
            log("Reached end of preview (checkout/thank you page)", "INFO")
            break

    log(f"Total pages captured: {page_num}", "INFO")
    return page_num


async def scrape_book_v2(browser, book):
    """
    1冊の絵本をスクレイピング（V2）
    """
    print(f"\n{'='*60}")
    print(f"📚 Processing: {book['name']}")
    print(f"{'='*60}")

    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = await context.new_page()

    # 出力ディレクトリ
    book_dir = OUTPUT_DIR / book['title']
    book_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. 商品ページにアクセス
        log(f"Navigating to: {book['url']}", "INFO")
        await page.goto(book['url'], wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)
        await save_debug_screenshot(page, book_dir, "01_product_page")

        # 2. "Personalize" ボタンをクリック
        personalize_selectors = [
            'button:has-text("Personalize my book")',
            'a:has-text("Personalize my book")',
            'button:has-text("personalize")',
            '[data-testid="personalize-button"]',
            '.personalize-button'
        ]

        clicked = await click_element(page, personalize_selectors, "Personalize button")

        if clicked:
            await wait_and_check(page)
            await save_debug_screenshot(page, book_dir, "02_after_personalize_click")
        else:
            log("Personalize button not found, continuing anyway", "WARN")

        # 3. カスタマイズフローをナビゲート
        await navigate_customization_flow(page, book_dir)
        await save_debug_screenshot(page, book_dir, "03_after_customization")

        # 4. プレビューボタンを探してクリック
        await find_and_access_preview(page, book_dir)
        await save_debug_screenshot(page, book_dir, "04_preview_page")

        # 5. テキストを抽出
        await extract_preview_text(page, book_dir)

        # 6. 全ページをキャプチャ
        num_pages = await capture_book_pages(page, book_dir)

        log(f"✅ Completed: {book['name']} ({num_pages} pages)", "SUCCESS")

    except Exception as e:
        log(f"❌ Error: {book['name']}", "ERROR")
        log(f"   {type(e).__name__}: {e}", "ERROR")
        await save_debug_screenshot(page, book_dir, "error_final")

    finally:
        await context.close()


async def main():
    """
    メイン処理
    """
    print("="*60)
    print("🚀 Wonderbly Book Preview Scraper V2")
    print("="*60)
    print(f"Output: {OUTPUT_DIR}")
    print(f"Child name: {CHILD_NAME}")
    print(f"Books: {len(BOOKS)}")
    print(f"Debug mode: {DEBUG}")
    print("="*60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    start_time = time.time()

    async with async_playwright() as p:
        print("\n🌐 Launching browser...")
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=50
        )

        for book in BOOKS:
            await scrape_book_v2(browser, book)
            await asyncio.sleep(3)

        await browser.close()

    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print(f"✅ All books processed")
    print(f"⏱️  Time: {elapsed:.1f}s")
    print(f"📁 Output: {OUTPUT_DIR}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
