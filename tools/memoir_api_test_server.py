"""
自分史インタビューAPI - テストサーバー（OpenAI不要）
動作確認用のモックレスポンスを返す
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal
import json

app = FastAPI(
    title="Memoir Editor API - Test Server",
    version="1.0.0-test",
    description="動作確認用のモックサーバー（OpenAI APIキー不要）"
)

# CORS設定を追加（ブラウザからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可（開発用）
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)

class InterviewReq(BaseModel):
    user_id: str
    message: str
    mode: Literal["interview", "edit"] = "interview"
    project_type: Literal["memoir", "picturebook"] = "memoir"

# モックレスポンス
MOCK_RESPONSES = [
    "はじめまして！自分史作りをお手伝いさせていただきます。\n\nまず最初の質問です。人生を3つの章に分けるなら、「いつ頃」「何がテーマ」になりそうですか？",
    "ありがとうございます。その時期について、もう少し詳しく教えていただけますか？",
    "なるほど、よくわかりました。では、幼少期で一番覚えている場面はどれですか？（場所・誰と・何があった）",
    "素敵なエピソードですね。そのとき、どんな気持ちでしたか？",
    "ありがとうございます。学生時代〜若い頃で「転機」になった出来事は何ですか？",
    "その転機で、何が変わりましたか？（考え方／行動／人間関係）",
    "なるほど。仕事・家庭など「責任を背負った時期」の象徴的な出来事を1つ教えてください。",
    "支えてくれた人は誰ですか？その人との具体的なエピソードを1つ教えてください。",
    "逆に、しんどかった時期は？その時どう乗り越えましたか？",
    "今のあなたを表す「大事にしている言葉／価値観」は何ですか？",
    "最後に、この自分史を誰に読んでほしいですか？その人に最後に伝えたい一言は？"
]

conversation_count = {}

@app.get("/")
def root():
    """API情報"""
    return {
        "service": "Memoir Editor API - Test Server",
        "version": "1.0.0-test",
        "status": "✅ 動作確認用モックサーバー（OpenAI不要）",
        "endpoints": [
            "POST /interview - インタビュー対話",
            "GET /materials/{user_id} - 素材生成（モック）",
            "GET /generate_story/{user_id} - 自分史生成（モック）",
            "GET /generate_picturebook/{user_id} - 絵本生成（モック）",
            "GET /health - ヘルスチェック"
        ]
    }

@app.get("/health")
def health():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "service": "memoir-api-test",
        "openai_required": False
    }

@app.post("/interview")
def interview(req: InterviewReq):
    """インタビュー対話（モック）"""
    if req.user_id not in conversation_count:
        conversation_count[req.user_id] = 0

    count = conversation_count[req.user_id]
    reply = MOCK_RESPONSES[min(count, len(MOCK_RESPONSES) - 1)]

    conversation_count[req.user_id] += 1

    return {
        "reply": reply,
        "message_count": count + 1,
        "mode": "mock"
    }

@app.get("/materials/{user_id}")
def get_materials(user_id: str):
    """素材生成（モック）"""
    return {
        "profile": {
            "name_display": "テスト太郎",
            "birth_year_approx": 1960,
            "current_age_approx": 66,
            "region": "東京都",
            "reader_intent": "家族に自分の歩みを伝えたい"
        },
        "timeline": [
            {
                "period": "幼少期（1965年頃）",
                "event": "初めて自転車に乗れた日",
                "place": "近所の公園",
                "people_involved": ["父"],
                "emotion": "嬉しさと誇らしさ",
                "meaning": "挑戦することの大切さ"
            }
        ],
        "people": [
            {
                "name": "父",
                "relation": "父親",
                "role_in_story": "優しく厳しい存在",
                "key_memory": "自転車の練習を付き合ってくれた"
            }
        ],
        "episodes": [
            {
                "title": "初めての自転車",
                "facts": "父と公園で自転車の練習をした",
                "feelings": "最初は怖かったが、乗れたときは嬉しかった",
                "insight": "諦めずに続ければできるようになる",
                "scene_details": {
                    "weather": "晴れ",
                    "sound": "鳥のさえずり",
                    "smell": "春の草の香り",
                    "objects": ["赤い自転車", "父の手"]
                },
                "sensitivity_level": "low"
            }
        ],
        "themes": ["家族", "挑戦", "成長"],
        "voice_style": {
            "base_style": "です・ます調",
            "allowed_variants": ["〜なのです", "〜のです"],
            "forbidden": ["説教口調", "断定過多"]
        },
        "open_questions": [],
        "_note": "これはモックデータです"
    }

@app.get("/generate_story/{user_id}")
def generate_story(user_id: str):
    """自分史生成（モック）"""
    return {
        "title": "歩んできた道",
        "subtitle": "ある人生の物語",
        "author": "テスト太郎",
        "chapters": [
            {
                "chapter_number": 1,
                "title": "幼き日々",
                "body": "昭和四十年、春の午後のことでした。近所の公園で、私は初めて自転車に乗ることができたのです。\n\n父が後ろで支えてくれていることに気づかず、一人で漕いでいたあの瞬間。風が頬をなでる感覚と、父の優しい笑顔が今でも忘れられません。\n\n何度転んでも、父は黙って見守ってくれていました。その姿が、後の人生で困難に直面したときの支えになっていたのかもしれません。"
            }
        ],
        "_note": "これはモックデータです"
    }

@app.get("/generate_picturebook/{user_id}")
def generate_picturebook(user_id: str, page_count: int = 24):
    """絵本生成（モック）"""
    return {
        "title": "おじいちゃんの自転車",
        "author": "テスト太郎",
        "total_pages": page_count,
        "pages": [
            {
                "page_number": 1,
                "text": "むかし、ぼくがちいさかったころ。はるのひに、じてんしゃにのれるようになりました。",
                "illustration_prompt": "A young boy with a red bicycle in a Japanese park in the 1960s. Cherry blossoms blooming. Warm sunlight. Father standing nearby. Nostalgic watercolor style.",
                "illustration_style_note": "温かみのある水彩画風"
            },
            {
                "page_number": 2,
                "text": "おとうさんが、うしろでささえてくれていました。",
                "illustration_prompt": "Father's gentle hands supporting the back of a small bicycle. Boy concentrating on pedaling. Park path with green grass. Soft afternoon light.",
                "illustration_style_note": "温かみのある水彩画風"
            }
        ],
        "_note": "これはモックデータです（実際は{page_count}ページ生成されます）"
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("  🧪 テストサーバー起動中（OpenAI不要）")
    print("=" * 60)
    print("\n✅ OpenAI APIキーは不要です")
    print("📍 URL: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("\n停止するには Ctrl+C を押してください\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
