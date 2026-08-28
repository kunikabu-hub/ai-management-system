"""
自分史インタビューAPI テストクライアント
対話形式でインタビューを進め、最終的に自分史と絵本を生成
"""

import requests
import json
from typing import Literal

# APIエンドポイント
BASE_URL = "http://localhost:8000"

def interview(user_id: str, message: str, mode: str = "interview", project_type: str = "memoir"):
    """インタビューAPIを呼び出し"""
    url = f"{BASE_URL}/interview"
    payload = {
        "user_id": user_id,
        "message": message,
        "mode": mode,
        "project_type": project_type
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def get_materials(user_id: str):
    """素材生成"""
    url = f"{BASE_URL}/materials/{user_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def generate_story(user_id: str):
    """自分史生成"""
    url = f"{BASE_URL}/generate_story/{user_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def generate_picturebook(user_id: str, page_count: int = 36):
    """絵本生成"""
    url = f"{BASE_URL}/generate_picturebook/{user_id}"
    params = {"page_count": page_count}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def export_content(user_id: str, type: str = "story", format: str = "json"):
    """コンテンツエクスポート"""
    url = f"{BASE_URL}/export/{user_id}"
    params = {"type": type, "format": format}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def delete_session(user_id: str):
    """セッション削除"""
    url = f"{BASE_URL}/session/{user_id}"
    response = requests.delete(url)
    response.raise_for_status()
    return response.json()

def list_sessions():
    """セッション一覧"""
    url = f"{BASE_URL}/sessions"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

# ===============================================
# インタラクティブモード
# ===============================================

def interactive_interview(user_id: str):
    """対話形式インタビュー"""
    print("=" * 60)
    print("🎤 自分史インタビューを開始します")
    print("=" * 60)
    print("終了するには 'quit' または 'exit' と入力してください\n")

    # 最初のメッセージ
    first_message = "自分史を作りたいです"
    print(f"あなた: {first_message}")

    try:
        result = interview(user_id, first_message)
        print(f"\nAI: {result['reply']}\n")
    except Exception as e:
        print(f"❌ エラー: {e}")
        return

    # 対話ループ
    while True:
        user_input = input("あなた: ").strip()

        if user_input.lower() in ["quit", "exit", "終了"]:
            print("\n📝 インタビューを終了します。")
            break

        if not user_input:
            continue

        try:
            result = interview(user_id, user_input)
            print(f"\nAI: {result['reply']}\n")
        except Exception as e:
            print(f"❌ エラー: {e}\n")

def auto_test_flow(user_id: str = "test_user_auto"):
    """自動テストフロー（サンプルデータで全工程実行）"""
    print("=" * 60)
    print("🚀 自動テストフローを開始します")
    print("=" * 60)

    # サンプル対話データ
    sample_conversation = [
        "自分史を作りたいです",
        "人生を3つに分けるなら、幼少期（1960年代）、社会人時代（1980年代〜2000年代）、そして退職後（2020年代〜）です。",
        "幼少期で一番覚えているのは、父と一緒に自転車の練習をした日です。実家近くの公園で、何度も転びながら練習しました。",
        "そのとき、誇らしい気持ちと嬉しさでいっぱいでした。",
        "転機は大学卒業後、東京の電機メーカーに就職したことです。",
        "考え方が大きく変わりました。学生時代は受け身でしたが、仕事では自分から動かなければならないと学びました。",
        "責任を背負った時期は、プロジェクトリーダーになった30代です。大型案件を任され、チームをまとめる立場になりました。",
        "支えてくれたのは妻です。残業続きで家を空けがちな私を、一度も責めずに支えてくれました。",
        "しんどかった時期は40代後半、リストラの波が来たときです。同僚が次々と去っていく中、自分の仕事の意味を問い直しました。",
        "大事にしている言葉は『誠実であれ』です。父から教わりました。",
        "この自分史は孫たちに読んでほしいです。最後に伝えたいのは『どんな時代も、誠実に生きれば道は開ける』です。"
    ]

    # 1. インタビュー実行
    print("\n📝 Step 1: インタビュー実行中...")
    for i, message in enumerate(sample_conversation, 1):
        print(f"  [{i}/{len(sample_conversation)}] {message[:50]}...")
        try:
            result = interview(user_id, message)
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            return

    print("  ✅ インタビュー完了\n")

    # 2. 素材生成
    print("📦 Step 2: 素材（materials.json）生成中...")
    try:
        materials = get_materials(user_id)
        with open(f"output/{user_id}_materials.json", "w", encoding="utf-8") as f:
            json.dump(materials, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 素材生成完了: output/{user_id}_materials.json")
        print(f"     - タイムライン: {len(materials.get('timeline', []))}件")
        print(f"     - 人物: {len(materials.get('people', []))}人")
        print(f"     - エピソード: {len(materials.get('episodes', []))}件\n")
    except Exception as e:
        print(f"  ❌ エラー: {e}\n")
        return

    # 3. 自分史生成
    print("📖 Step 3: 自分史（story.json）生成中...")
    try:
        story = generate_story(user_id)
        with open(f"output/{user_id}_story.json", "w", encoding="utf-8") as f:
            json.dump(story, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 自分史生成完了: output/{user_id}_story.json")
        print(f"     - タイトル: {story.get('title')}")
        print(f"     - 章数: {len(story.get('chapters', []))}章\n")
    except Exception as e:
        print(f"  ❌ エラー: {e}\n")
        return

    # 4. 絵本生成
    print("📚 Step 4: 絵本（picturebook.json）生成中...")
    try:
        picturebook = generate_picturebook(user_id, page_count=24)
        with open(f"output/{user_id}_picturebook.json", "w", encoding="utf-8") as f:
            json.dump(picturebook, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 絵本生成完了: output/{user_id}_picturebook.json")
        print(f"     - タイトル: {picturebook.get('title')}")
        print(f"     - ページ数: {picturebook.get('total_pages')}ページ\n")
    except Exception as e:
        print(f"  ❌ エラー: {e}\n")
        return

    # 5. 完了
    print("=" * 60)
    print("🎉 自動テストフロー完了！")
    print("=" * 60)
    print(f"\n生成ファイル:")
    print(f"  - output/{user_id}_materials.json")
    print(f"  - output/{user_id}_story.json")
    print(f"  - output/{user_id}_picturebook.json\n")

# ===============================================
# メイン
# ===============================================

def main():
    print("\n" + "=" * 60)
    print("  自分史インタビューAPI テストクライアント")
    print("=" * 60)
    print("\nモードを選択してください:")
    print("  1. 対話形式インタビュー（手動入力）")
    print("  2. 自動テストフロー（サンプルデータで全工程実行）")
    print("  3. セッション一覧表示")
    print("  4. セッション削除")
    print("  5. 終了")

    choice = input("\n選択 (1-5): ").strip()

    if choice == "1":
        user_id = input("ユーザーID（例: user123）: ").strip()
        if not user_id:
            user_id = "default_user"
        interactive_interview(user_id)

    elif choice == "2":
        user_id = input("ユーザーID（例: test_user）[Enter=自動]: ").strip()
        if not user_id:
            user_id = "test_user_auto"
        auto_test_flow(user_id)

    elif choice == "3":
        print("\n📂 セッション一覧:")
        try:
            sessions = list_sessions()
            if sessions["count"] == 0:
                print("  セッションが見つかりません")
            else:
                for session_id in sessions["sessions"]:
                    print(f"  - {session_id}")
        except Exception as e:
            print(f"❌ エラー: {e}")

    elif choice == "4":
        user_id = input("削除するユーザーID: ").strip()
        if user_id:
            try:
                result = delete_session(user_id)
                print(f"✅ {result['message']}")
            except Exception as e:
                print(f"❌ エラー: {e}")

    elif choice == "5":
        print("👋 終了します")
        return

    else:
        print("❌ 無効な選択です")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 中断されました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
