#!/usr/bin/env python3
"""
Wonderbly Book Preview Scraper
Playwrightを使用してWonderblyの絵本プレビューを自動取得
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeout
import time

# 設定
OUTPUT_DIR = Path(__file__).parent.parent / "output" / "wonderbly_screenshots"
CHILD_NAME = "Hana"

# 対象タイトル
BOOKS = [
    {
        "url": "https://www.wonderbly.com/personalized-products/lost-my-name-book",
        "title": "lost_my_name",
        "name": "The Little Girl Who Lost Her Name"
    },
    {
        "url": "https://www.wonderbly.com/personalized-products/the-wondrous-road-book",
        "title": "the_wondrous_road",
        "name": "The Wondrous Road Ahead"
    },
    {
        "url": "https://www.wonderbly.com/personalized-products/where-are-you-book",
        "title": "where_are_you",
        "name": "Where Are You?"
    }
]


async def wait_for_page_load(page: Page, timeout: int = 10000):
    """ページの読み込みを待つ"""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except PlaywrightTimeout:
        print(f"  ⚠️ タイムアウト: ネットワークアイドル待機")
    await asyncio.sleep(1)


async def customize_book(page: Page, book_title: str):
    """
    絵本のカスタマイズを行う
    """
    print(f"\n📝 カスタマイズ開始: {book_title}")

    # "Personalize my book" ボタンを探してクリック
    try:
        # いくつかのパターンを試す
        personalize_selectors = [
            'button:has-text("Personalize my book")',
            'a:has-text("Personalize my book")',
            '[data-testid="personalize-button"]',
            '.personalize-button'
        ]

        clicked = False
        for selector in personalize_selectors:
            try:
                button = page.locator(selector).first
                if await button.is_visible(timeout=2000):
                    print(f"  ✓ ボタン発見: {selector}")
                    await button.click()
                    clicked = True
                    break
            except:
                continue

        if not clicked:
            print(f"  ⚠️ 'Personalize'ボタンが見つかりません")
            return False

        await wait_for_page_load(page)

    except Exception as e:
        print(f"  ❌ エラー: {e}")
        return False

    # 名前入力フィールドを探す
    try:
        print(f"  📝 名前を入力中: {CHILD_NAME}")

        # 複数のパターンで名前入力フィールドを探す
        name_selectors = [
            'input[name="name"]',
            'input[name="firstName"]',
            'input[name="childName"]',
            'input[placeholder*="name"]',
            'input[type="text"]'
        ]

        filled = False
        for selector in name_selectors:
            try:
                name_input = page.locator(selector).first
                if await name_input.is_visible(timeout=2000):
                    await name_input.fill(CHILD_NAME)
                    print(f"  ✓ 名前入力完了: {selector}")
                    filled = True
                    break
            except:
                continue

        if not filled:
            print(f"  ⚠️ 名前入力フィールドが見つかりません")
            # 続行を試みる

        await asyncio.sleep(1)

    except Exception as e:
        print(f"  ⚠️ 名前入力エラー: {e}")

    # 性別選択（女の子）
    try:
        gender_selectors = [
            'button:has-text("Girl")',
            'input[value="female"]',
            '[data-gender="girl"]',
            '[data-gender="female"]'
        ]

        for selector in gender_selectors:
            try:
                gender = page.locator(selector).first
                if await gender.is_visible(timeout=2000):
                    await gender.click()
                    print(f"  ✓ 性別選択: Girl")
                    break
            except:
                continue

        await asyncio.sleep(1)

    except Exception as e:
        print(f"  ⚠️ 性別選択エラー: {e}")

    # "Next" または "Continue" ボタンをクリック（複数回必要な場合がある）
    try:
        for _ in range(5):  # 最大5回試行
            next_selectors = [
                'button:has-text("Next")',
                'button:has-text("Continue")',
                'button:has-text("Preview")',
                '[data-testid="next-button"]',
                '.next-button'
            ]

            clicked_next = False
            for selector in next_selectors:
                try:
                    next_button = page.locator(selector).first
                    if await next_button.is_visible(timeout=2000):
                        await next_button.click()
                        print(f"  ✓ Nextボタンクリック")
                        clicked_next = True
                        await asyncio.sleep(2)
                        break
                except:
                    continue

            if not clicked_next:
                break

    except Exception as e:
        print(f"  ⚠️ Nextボタンエラー: {e}")

    return True


async def access_preview(page: Page):
    """
    プレビューページにアクセス
    """
    print(f"\n🔍 プレビューページを探索中...")

    # "Preview" ボタンを探してクリック
    preview_selectors = [
        'button:has-text("Preview")',
        'a:has-text("Preview")',
        'button:has-text("Preview Full Book")',
        'button:has-text("See Preview")',
        '[data-testid="preview-button"]'
    ]

    for selector in preview_selectors:
        try:
            preview_button = page.locator(selector).first
            if await preview_button.is_visible(timeout=3000):
                print(f"  ✓ プレビューボタン発見: {selector}")
                await preview_button.click()
                await wait_for_page_load(page)
                return True
        except:
            continue

    print(f"  ℹ️ プレビューボタンが見つかりません（既にプレビューページの可能性）")
    return False


async def capture_preview_pages(page: Page, book_title: str):
    """
    プレビューページの全ページをキャプチャ
    """
    print(f"\n📸 スクリーンショット撮影開始: {book_title}")

    # 出力ディレクトリ作成
    book_dir = OUTPUT_DIR / book_title
    book_dir.mkdir(parents=True, exist_ok=True)

    # 初期ページをキャプチャ
    page_num = 1
    screenshot_path = book_dir / f"page_{page_num:03d}.png"
    await page.screenshot(path=str(screenshot_path), full_page=True)
    print(f"  ✓ Page {page_num} 保存: {screenshot_path.name}")

    # ページめくりを試みる
    max_pages = 50  # 最大ページ数

    for i in range(max_pages):
        page_num = i + 2

        # 次のページへ移動する方法を試す
        next_page_selectors = [
            'button[aria-label="Next page"]',
            'button:has-text("Next")',
            '.next-page',
            '[data-testid="next-page"]',
            'button.arrow-right',
            '.page-next'
        ]

        clicked = False
        for selector in next_page_selectors:
            try:
                next_button = page.locator(selector).first
                if await next_button.is_visible(timeout=1000):
                    await next_button.click()
                    await asyncio.sleep(2)
                    clicked = True
                    break
            except:
                continue

        # ボタンが見つからない場合、クリックで次のページへ
        if not clicked:
            try:
                # ページの右側をクリック
                await page.click('body', position={"x": 800, "y": 400})
                await asyncio.sleep(2)
            except:
                print(f"  ℹ️ これ以上ページがありません（{page_num - 1}ページまで）")
                break

        # スクリーンショットを撮影
        screenshot_path = book_dir / f"page_{page_num:03d}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"  ✓ Page {page_num} 保存: {screenshot_path.name}")

        # 終了判定（同じページが続いたら終了）
        if i > 0:
            prev_screenshot = book_dir / f"page_{page_num - 1:03d}.png"
            curr_screenshot = screenshot_path

            # ファイルサイズで簡易比較（完全一致は別途必要）
            if prev_screenshot.stat().st_size == curr_screenshot.stat().st_size:
                # 同じサイズなら最後のページの可能性
                await asyncio.sleep(1)

    print(f"  ✅ 完了: {page_num}ページ保存")
    return page_num


async def scrape_book(browser, book):
    """
    1冊の絵本をスクレイピング
    """
    print(f"\n{'='*60}")
    print(f"📚 処理開始: {book['name']}")
    print(f"{'='*60}")

    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    )
    page = await context.new_page()

    try:
        # 1. 商品ページにアクセス
        print(f"\n🌐 アクセス中: {book['url']}")
        try:
            await page.goto(book['url'], wait_until="domcontentloaded", timeout=60000)
        except PlaywrightTimeout:
            print(f"  ⚠️ ページ読み込みタイムアウト（続行）")
        await asyncio.sleep(5)

        # ページ全体のスクリーンショットを保存
        product_dir = OUTPUT_DIR / book['title']
        product_dir.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(product_dir / "product_page.png"), full_page=True)
        print(f"  ✓ 商品ページ保存")

        # 2. カスタマイズ
        customize_success = await customize_book(page, book['name'])

        if not customize_success:
            print(f"  ⚠️ カスタマイズに失敗しました")

        await asyncio.sleep(2)

        # 現在のページを保存（カスタマイズ後）
        await page.screenshot(path=str(product_dir / "customize_page.png"), full_page=True)
        print(f"  ✓ カスタマイズページ保存")

        # 3. プレビューにアクセス
        preview_success = await access_preview(page)
        await asyncio.sleep(3)

        # 4. プレビューページをキャプチャ
        num_pages = await capture_preview_pages(page, book['title'])

        print(f"\n✅ 完了: {book['name']} ({num_pages}ページ)")

    except Exception as e:
        print(f"\n❌ エラー発生: {book['name']}")
        print(f"   {type(e).__name__}: {e}")

        # エラー時のスクリーンショット
        try:
            error_path = OUTPUT_DIR / book['title'] / "error_screenshot.png"
            error_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(error_path), full_page=True)
            print(f"   エラー時のスクリーンショット保存: {error_path}")
        except:
            pass

    finally:
        await context.close()


async def main():
    """
    メイン処理
    """
    print("="*60)
    print("🚀 Wonderbly Book Preview Scraper")
    print("="*60)
    print(f"出力先: {OUTPUT_DIR}")
    print(f"子どもの名前: {CHILD_NAME}")
    print(f"対象タイトル数: {len(BOOKS)}")
    print("="*60)

    # 出力ディレクトリ作成
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    async with async_playwright() as p:
        # ブラウザ起動（headless=False でブラウザを表示）
        print("\n🌐 ブラウザ起動中...")
        browser = await p.chromium.launch(
            headless=False,  # ブラウザを表示（デバッグ用）
            slow_mo=100  # 操作を少しゆっくりに
        )

        # 各書籍を処理
        for book in BOOKS:
            await scrape_book(browser, book)
            await asyncio.sleep(2)

        await browser.close()

    elapsed_time = time.time() - start_time
    print("\n" + "="*60)
    print(f"✅ 全タイトル処理完了")
    print(f"⏱️ 処理時間: {elapsed_time:.1f}秒")
    print(f"📁 保存先: {OUTPUT_DIR}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
