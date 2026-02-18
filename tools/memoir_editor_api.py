"""
自分史インタビュー&編集者AI - FastAPI実装
OpenAI Chat Completions API + Structured Outputs を使用
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import json
from typing import Literal, Optional, Any, Dict, List
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ---- Load Environment Variables ----
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# ---- OpenAI Client Setup ----
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "gpt-4o-2024-08-06"  # Structured Outputs対応モデル

# ---- Data Directory ----
DATA_DIR = Path("./sessions")
DATA_DIR.mkdir(exist_ok=True)

# ---- Image Output Directory ----
IMAGE_DIR = Path("../output/picturebook_images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# ---- System Prompt ----
SYSTEM_PROMPT = """あなたは「自分史絵本」のライト版AIインタビュアー兼編集者です。
目的は、ユーザーがノープランでも15分程度で「物語の骨子」を抽出し、最後に編集可能な要約（テーマ／転換点2つ／価値観／読者）を提示することです。

# 重要な設計思想
- ユーザーに抽象化を強要しない。抽象化はAIが仮説提示→Yes/Noで補正させる。
- 「終わりが見えない負担」を避ける：必ず5ステップ表示で進める（内部ロジックは分岐して良い）。
- 最大質問数は原則12問以内（補助質問含む）。沈黙時のみ救済質問を追加（合計最大15問）。
- 深掘りはしない。「編集可能な素材」が出たら次へ進む。
- 同じ構文の連発禁止（例：「どう感じましたか？」を連発しない）。
- ユーザーの負担を下げる言い回しを入れる（例：「短くてOK」「思い出せる範囲で」）。

# 修正ルール（重要）
- ライト版では「3年前」など長期比較は原則禁止。比較は「転換点の前後」に限定する。
- 返答の冒頭で感想や称賛（例：興味深い、大きな変化）を基本的に書かず、編集要約→確認を優先する。
- 「影響力」など手段的ワードが出たら、価値観に昇華するための1問（理由の選択式）を必ず挟む。
- 最終出力の締めは営業トーン禁止。次アクション選択で終える。

# UI表示要件
各ターンで必ず進捗を冒頭に付ける：
【Step X/5】タイトル（例：方向性／転換点1／転換点2／今の自分／読者）
※表示は短く。

# 収集する最終フィールド（必須）
- story_type: "growth" | "family" | "work" | "unknown"
- turning_point_1: {event, before_state, after_change}
- turning_point_2: {event, before_state, after_change}
- current_state: {delta_3y_increase, delta_3y_decrease(optional), chosen_state_label, ai_one_liner_confirmed}
- values: [value1, value2(optional)]
- audience: {who, desired_feeling}
- notes: [任意のキーワード]（後工程の編集用）

# 5ステップの会話フロー（外見は固定、内部は分岐）
## Step1: 方向性選択（必須）
提示：
「約15分・全5ステップ。途中で変更OKです。まず方向性を選んでください。」
選択肢：
1) 成長の物語（挑戦・失敗・転機）
2) 家族へのメッセージ（感謝・責任・絆）
3) 仕事の哲学（価値観・判断軸）
4) 話しながら見つけたい
→ 入力からstory_typeを決定。

## Step2: 転換点1（必須）
story_typeごとに主質問を変えるが、取得する構造は同じ（event/before/after）
- growth: 「印象に残っている転機は？」→ before_state → after_change
- family: 「この物語を向けたい人は？」（audience.whoの候補収集も兼ねる）→ 「その人との印象的な出来事は？」→ before_state(当時の状況)→ after_change(関係や自分が変わった点)
- work: 「仕事で価値観が揺れた出来事は？」→ before_state → after_change（判断軸に触れればnotesへ）
- unknown: 「最近の自分を変えた出来事は？」→ before_state → after_change
※各転換点で3問以内に収める。
※最後に必ずAI要約を1行で返す（感想・称賛なし）：「転換点1：◯◯で、◯◯から◯◯に変わった、ですね。」

### 沈黙救済（「特にない」「わからない」等）
以下を順番に1つずつ出し、それでもダメなら選択式へ：
A) 出来事リスト提示（引っ越し／進学／就職／転職／結婚／出産／独立／大きな失敗／大きな達成）
B) 比較質問「今と3年前で一番違うところは？」
C) 違和感質問「『このままでいいのかな』と思った時期は？」
D) 選択式：「一番近いのは？ 挑戦／迷い／責任／立て直し／変化／安定」
→ どれか出たらeventに変換して進行。

## Step3: 転換点2（必須）
Step2と同様だが、別の時期・別の角度を促す：
- growth: 「もう1つ、人生の流れを変えた出来事は？」
- family: 「その人に対して"守ろう"と思った瞬間は？」
- work: 「仕事で誇れた or 苦しかった判断は？」
- unknown: 「もう1つ、印象に残る出来事は？」
同様にevent/before/afterを回収し、AI要約1行（感想・称賛なし）：「転換点2：◯◯で、◯◯から◯◯に変わった、ですね。」

## Step4: 今の自分（必須）
ユーザーに一言で言わせない。素材→AI仮説提示。
質問（2問以内）：
1) 「転換点を経て、今"増えたもの"は？」（責任／自信／不安／収入／自由／忙しさ 等でもOK）
2) （余力があれば）「減ったものは？」（任意）
次に選択式：
「今の状態に近いのは？（複数可）」挑戦中／迷い中／守り／走り続けている／立て直し／仕上げ
→ AIが一言仮説を提示（冒頭に感想・称賛は書かない）：
「転換点1は◯◯、転換点2は◯◯ですね。今のあなたは『◯◯し続ける人』に見えます。合っていますか？（はい／違う／近いけど修正）」
→ confirmedなone-linerに確定。values候補もAIが2つ提示してYes/Noで採用（例：「自走」「責任」「誠実」「挑戦」「家族」等）
※「影響力」など手段的ワードが出たら、理由を選択式で聞く（例：なぜそれが大事？→人を守りたい／成長したい／認められたい）

## Step5: 読者（必須）
質問（2問）：
1) 「誰に読んでほしいですか？」（社外の人／家族／子ども／未来の自分 等）
2) 「読み終えた人に、どう感じてほしいですか？」（安心／勇気／誇り／感謝／行動したくなる 等）
→ 最終サマリーを提示し終了

# 出力フォーマット
- 会話中：自然文（日本語、簡潔、押し付けない、感想・称賛を冒頭に書かない）
- 最終：Markdownで「物語の骨子」を提示
- 最後にJSONも必ず出す（後工程で保存するため）。JSONはコードブロックで。
- 締めは営業トーン禁止。次アクション選択で終える。
- ユーザーが「絵本制作へ進む」を選んだ場合、具体的な操作方法を案内する：
  「画面右側の『▶ 物語を生成する』ボタンをクリックしてください。自動的に素材生成→自分史生成→絵本生成が行われます。」

最終出力（例）：
---
## あなたの物語の骨子

**テーマ（方向性）**：成長の物語

**転換点1**：[出来事] → [変化]

**転換点2**：[出来事] → [変化]

**今のあなた**：[一言要約]

**大切にしている価値観（仮）**：[価値観1]、[価値観2]

**読者**：[誰に]

**読後に残したい感情**：[感情]

---

```json
{
  "story_type": "growth",
  "turning_point_1": {"event": "", "before_state": "", "after_change": ""},
  "turning_point_2": {"event": "", "before_state": "", "after_change": ""},
  "current_state": {"delta_increase": "", "chosen_state_label": "", "ai_one_liner_confirmed": ""},
  "values": ["", ""],
  "audience": {"who": "", "desired_feeling": ""},
  "notes": []
}
```

**次のアクション**：
1. このまま絵本制作へ進む
2. 骨子を編集する
3. もう一度インタビューする

どれにしますか？

---

質問は1つずつ。進捗表示を忘れずに。
"""

# ---- JSON Schemas ----
MATERIALS_SCHEMA = {
    "type": "object",
    "required": ["profile", "timeline", "people", "episodes", "themes", "voice_style", "open_questions"],
    "properties": {
        "profile": {
            "type": "object",
            "required": ["name_display", "birth_year_approx", "current_age_approx", "region", "reader_intent"],
            "properties": {
                "name_display": {"type": "string"},
                "birth_year_approx": {"type": "integer"},
                "current_age_approx": {"type": "integer"},
                "region": {"type": "string"},
                "reader_intent": {"type": "string", "description": "誰に向けて何を残したいか"}
            },
            "additionalProperties": False
        },
        "timeline": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["period", "event", "place", "people_involved", "emotion", "meaning"],
                "properties": {
                    "period": {"type": "string", "description": "例：小学校低学年、2008年頃、社会人1年目"},
                    "event": {"type": "string"},
                    "place": {"type": "string"},
                    "people_involved": {"type": "array", "items": {"type": "string"}},
                    "emotion": {"type": "string"},
                    "meaning": {"type": "string", "description": "価値観の変化・学び（説教口調は禁止）"}
                },
                "additionalProperties": False
            }
        },
        "people": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "relation", "role_in_story", "key_memory"],
                "properties": {
                    "name": {"type": "string"},
                    "relation": {"type": "string"},
                    "role_in_story": {"type": "string"},
                    "key_memory": {"type": "string"}
                },
                "additionalProperties": False
            }
        },
        "episodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["title", "facts", "feelings", "insight", "scene_details", "sensitivity_level"],
                "properties": {
                    "title": {"type": "string"},
                    "facts": {"type": "string"},
                    "feelings": {"type": "string"},
                    "insight": {"type": "string"},
                    "scene_details": {
                        "type": "object",
                        "required": ["weather", "sound", "smell", "objects"],
                        "properties": {
                            "weather": {"type": "string"},
                            "sound": {"type": "string"},
                            "smell": {"type": "string"},
                            "objects": {"type": "array", "items": {"type": "string"}}
                        },
                        "additionalProperties": False
                    },
                    "sensitivity_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "高の場合は詳細描写を控え、確認質問を優先"
                    }
                },
                "additionalProperties": False
            }
        },
        "themes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "例：家族、挑戦、仕事観、恩返し、学び、誇り"
        },
        "voice_style": {
            "type": "object",
            "required": ["base_style", "allowed_variants", "forbidden"],
            "properties": {
                "base_style": {"type": "string", "description": "基本文体（です・ます調）"},
                "allowed_variants": {"type": "array", "items": {"type": "string"}},
                "forbidden": {"type": "array", "items": {"type": "string"}}
            },
            "additionalProperties": False
        },
        "open_questions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "不足情報を埋めるための追加質問"
        }
    },
    "additionalProperties": False
}

STORY_SCHEMA = {
    "type": "object",
    "required": ["title", "subtitle", "author", "chapters"],
    "properties": {
        "title": {"type": "string", "description": "自分史のタイトル"},
        "subtitle": {"type": "string", "description": "サブタイトル（任意だが空文字でもOK）"},
        "author": {"type": "string", "description": "著者名"},
        "chapters": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["chapter_number", "title", "body"],
                "properties": {
                    "chapter_number": {"type": "integer"},
                    "title": {"type": "string"},
                    "body": {"type": "string", "description": "です・ます調の本文。断定過多を避け、情景描写豊か。"}
                },
                "additionalProperties": False
            }
        }
    },
    "additionalProperties": False
}

PICTUREBOOK_SCHEMA = {
    "type": "object",
    "required": ["title", "author", "total_pages", "pages"],
    "properties": {
        "title": {"type": "string"},
        "author": {"type": "string"},
        "total_pages": {"type": "integer"},
        "pages": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["page_number", "text", "illustration_prompt", "illustration_style_note"],
                "properties": {
                    "page_number": {"type": "integer"},
                    "text": {
                        "type": "string",
                        "minLength": 200,
                        "maxLength": 500,
                        "description": "200〜400字の文章（です・ます調）。具体的な情景描写、五感、内的独白、Showing技法を含む。最低4〜6文で構成。"
                    },
                    "illustration_prompt": {
                        "type": "string",
                        "minLength": 50,
                        "description": "AI画像生成用の英語プロンプト（詳細な情景描写、具体的な場所・時間・感情を含む）"
                    },
                    "illustration_style_note": {
                        "type": "string",
                        "description": "絵本の雰囲気やトーン（温かみ、ノスタルジック等）"
                    }
                },
                "additionalProperties": False
            }
        }
    },
    "additionalProperties": False
}

# ---- Storage Functions ----
def load_session(user_id: str) -> dict:
    """ユーザーセッションをファイルから読み込み"""
    fp = DATA_DIR / f"{user_id}.json"
    if fp.exists():
        return json.loads(fp.read_text(encoding="utf-8"))
    return {
        "messages": [],
        "materials": None,
        "story": None,
        "picturebook": None
    }

def save_session(user_id: str, data: dict):
    """ユーザーセッションをファイルに保存"""
    fp = DATA_DIR / f"{user_id}.json"
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- AI Image Generation ----
def generate_image(prompt: str, user_id: str, page_number: int) -> Optional[str]:
    """
    DALL-E 3で画像を生成し、ローカルに保存
    Returns: 画像ファイルパス（相対パス）
    """
    try:
        # DALL-E 3で画像生成
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )

        image_url = response.data[0].url

        # 画像をダウンロード
        image_response = requests.get(image_url, timeout=30)
        image_response.raise_for_status()

        # 保存先ディレクトリ作成
        user_image_dir = IMAGE_DIR / user_id
        user_image_dir.mkdir(parents=True, exist_ok=True)

        # ファイル名生成（タイムスタンプ付き）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"page_{page_number:02d}_{timestamp}.png"
        image_path = user_image_dir / image_filename

        # 画像を保存
        with open(image_path, "wb") as f:
            f.write(image_response.content)

        # 相対パスを返す
        return str(image_path.relative_to(Path(".")))

    except Exception as e:
        print(f"画像生成エラー (page {page_number}): {str(e)}")
        return None

# ---- OpenAI API Call ----
def call_ai(messages: List[Dict[str, str]], json_schema: Optional[dict] = None, temperature: float = 0.7) -> str:
    """
    OpenAI Chat Completions APIを呼び出し
    json_schemaが指定されている場合はStructured Outputsを使用
    """
    kwargs = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature
    }

    # Structured Outputs（JSON mode）を使用する場合
    if json_schema:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "output_schema",
                "strict": True,
                "schema": json_schema
            }
        }

    try:
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        return content if content else ""
    except Exception as e:
        raise HTTPException(500, f"OpenAI API Error: {str(e)}")

# ---- FastAPI App ----
app = FastAPI(
    title="Memoir Editor AI API",
    version="1.0.0",
    description="自分史インタビュー&編集者AI - OpenAI Structured Outputs対応"
)

# CORS設定を追加（ブラウザからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # すべてのオリジンを許可（開発用）
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)

# ---- Request Models ----
class InterviewReq(BaseModel):
    user_id: str
    message: str
    mode: Literal["interview", "edit"] = "interview"
    project_type: Literal["memoir", "picturebook"] = "memoir"

# ---- API Endpoints ----

@app.get("/")
def root():
    """API情報"""
    return {
        "service": "Memoir Editor AI API",
        "version": "2.0.0",
        "endpoints": [
            "/interview (POST) - インタビュー対話",
            "/complete_story_generation/{user_id} (POST) - 【統合】materials→story→picturebook自動生成",
            "/materials/{user_id} (GET) - 素材生成",
            "/generate_story/{user_id} (GET) - 自分史生成",
            "/generate_picturebook/{user_id} (GET) - 絵本生成",
            "/generate_picturebook_with_images/{user_id} (GET) - 絵本生成（画像付き）",
            "/export/{user_id} (GET) - エクスポート"
        ],
        "features": [
            "✅ 15分・5ステップのライトインタビュー",
            "✅ N型感情曲線 × 弁証法構造",
            "✅ DALL-E 3による画像生成",
            "✅ 統合フロー（インタビュー→物語生成）"
        ]
    }

@app.post("/interview")
def interview(req: InterviewReq):
    """
    インタビュー対話エンドポイント
    ユーザーのメッセージを受け取り、次の質問または確認を返す
    """
    sess = load_session(req.user_id)

    # ユーザーメッセージを保存
    sess["messages"].append({"role": "user", "content": req.message})

    # システムプロンプト + 会話履歴を構築
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 会話履歴を追加（最新10ターンのみ、長くなりすぎないように）
    recent_messages = sess["messages"][-20:]  # 最新20メッセージ（10往復）
    messages.extend(recent_messages)

    # コンテキストを追加
    context_prompt = f"""
モード: {req.mode} | 種類: {req.project_type}

会話履歴を見て、現在のステップ（Step 1-5）を判断し、適切な質問を1つ返してください。
必ず【Step X/5】を冒頭に付けてください。
最終ステップ完了時は「物語の骨子」をMarkdown+JSONで出力してください。
"""
    messages.append({"role": "system", "content": context_prompt})

    # AI応答を取得
    reply = call_ai(messages)

    # アシスタントメッセージを保存
    sess["messages"].append({"role": "assistant", "content": reply})
    save_session(req.user_id, sess)

    return {"reply": reply, "message_count": len(sess["messages"])}

def check_materials_insufficiency(materials: dict) -> dict:
    """
    materialsの不足をチェックし、追加質問を生成

    Returns:
        {
            "insufficient": bool,
            "missing_elements": list[str],
            "additional_questions": list[str],
            "reasoning": str
        }
    """
    missing = []
    questions = []

    # 1. 谷（Nadir）の不足チェック
    episodes = materials.get("episodes", [])
    has_conflict = any(
        "不安" in ep.get("feelings", "") or
        "心配" in ep.get("feelings", "") or
        "困難" in ep.get("facts", "") or
        "大変" in ep.get("facts", "") or
        ep.get("sensitivity_level") == "high"
        for ep in episodes
    )

    if not has_conflict:
        missing.append("谷（葛藤・困難）")
        questions.append("この8年間で、一番心配や不安を感じた出来事はありますか？（病気、別れの不安、困ったことなど）")

    # 2. 具体的な情景の不足チェック
    has_scene_details = any(
        ep.get("scene_details", {}).get("weather") or
        ep.get("scene_details", {}).get("sound") or
        ep.get("scene_details", {}).get("smell")
        for ep in episodes
    )

    if not has_scene_details:
        missing.append("具体的な情景")
        questions.append("印象に残っている場面で、その時の天気や周りの音、匂いなど、覚えていることはありますか？")

    # 3. タイムラインの深さチェック
    timeline = materials.get("timeline", [])
    if len(timeline) < 3:
        missing.append("時間の流れ")
        questions.append("ポラーと過ごした8年間で、他に印象的だった時期や出来事はありますか？（成長、変化、特別な日など）")

    # 4. 内面的な変化の不足チェック
    has_inner_change = any(
        "変わった" in ep.get("insight", "") or
        "気づいた" in ep.get("insight", "") or
        "感じた" in ep.get("insight", "")
        for ep in episodes
    )

    if not has_inner_change:
        missing.append("内面的な変化")
        questions.append("ポラーがいることで、あなた自身の考え方や生活で変わったことは何ですか？")

    insufficient = len(missing) > 0

    # 最大3問まで
    questions = questions[:3]

    return {
        "insufficient": insufficient,
        "missing_elements": missing,
        "additional_questions": questions,
        "reasoning": f"物語の深みのために、以下の要素が不足しています：{', '.join(missing)}" if insufficient else "十分な情報が揃っています"
    }

@app.get("/materials/{user_id}")
def get_materials(user_id: str):
    """
    会話ログから materials.json を生成
    構造化素材（年表・人物・エピソード・テーマ）を抽出
    """
    sess = load_session(user_id)

    if not sess["messages"]:
        raise HTTPException(400, "No session messages found. Start an interview first.")

    # 会話履歴を整形
    conversation_log = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in sess["messages"]
    ])

    prompt = f"""
以下の会話ログから、自分史の編集素材を抽出してJSONで出力してください。
必ず指定スキーマに厳密準拠してください。推測で埋めず、不足はopen_questionsに入れてください。

重要な注意事項：
1. 事実として語られていない情報は推測しないでください
2. 年齢・年代が不明な場合は「不明」「推定〜年代」のように記載
3. 不足情報はopen_questionsに明記してください
4. です・ます調を維持してください
5. 説教口調・教訓押し付けは禁止です

会話ログ:
{conversation_log}
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    # Structured Outputsで生成
    response_text = call_ai(messages, json_schema=MATERIALS_SCHEMA, temperature=0.3)

    try:
        parsed = json.loads(response_text)
        sess["materials"] = parsed
        save_session(user_id, sess)
        return parsed
    except json.JSONDecodeError as e:
        raise HTTPException(500, f"Failed to parse materials JSON: {str(e)}\nRaw output: {response_text[:500]}")

@app.get("/check_insufficiency/{user_id}")
def check_insufficiency(user_id: str):
    """
    materialsの不足をチェックし、追加質問を返す
    """
    sess = load_session(user_id)

    if not sess.get("materials"):
        raise HTTPException(400, "Materials not found. Generate materials first.")

    result = check_materials_insufficiency(sess["materials"])

    return {
        "user_id": user_id,
        "insufficient": result["insufficient"],
        "missing_elements": result["missing_elements"],
        "additional_questions": result["additional_questions"],
        "reasoning": result["reasoning"]
    }

@app.post("/answer_additional_questions/{user_id}")
def answer_additional_questions(user_id: str, request: dict):
    """
    追加質問への回答を受け取り、materialsを更新

    Request body:
    {
        "answers": [
            {"question": "質問1", "answer": "回答1"},
            {"question": "質問2", "answer": "回答2"}
        ]
    }
    """
    sess = load_session(user_id)

    if not sess.get("materials"):
        raise HTTPException(400, "Materials not found.")

    answers = request.get("answers", [])

    if not answers:
        raise HTTPException(400, "No answers provided.")

    print(f"🔧 Processing {len(answers)} answers...")

    # 回答をmessagesに追加
    for qa in answers:
        sess["messages"].append({
            "role": "user",
            "content": f"追加質問: {qa['question']}\n回答: {qa['answer']}"
        })

    # 追加情報を直接episodesに追加（より確実）
    materials = sess["materials"]
    print(f"📊 Current episodes: {len(materials.get('episodes', []))}")

    for qa in answers:
        question = qa["question"]
        answer = qa["answer"]

        # 新しいepisodeを作成
        new_episode = {
            "title": f"追加情報：{question[:20]}...",
            "facts": answer,
            "feelings": "",
            "insight": "",
            "scene_details": {
                "weather": "",
                "sound": "",
                "smell": "",
                "objects": []
            },
            "sensitivity_level": "medium"
        }

        # 葛藤・困難に関する質問の場合
        if any(word in question for word in ["心配", "不安", "困難", "大変", "病気"]):
            new_episode["feelings"] = "不安、心配"
            new_episode["sensitivity_level"] = "high"

        # 具体的な情景に関する質問の場合
        if any(word in question for word in ["天気", "音", "匂い", "覚えている"]):
            # 回答から情景を抽出（簡易版）
            if "晴れ" in answer or "雨" in answer or "曇り" in answer:
                new_episode["scene_details"]["weather"] = answer[:50]

        # 内面的な変化に関する質問の場合
        if any(word in question for word in ["変わった", "考え方", "生活"]):
            new_episode["insight"] = answer

        # episodesに追加
        if "episodes" not in materials:
            materials["episodes"] = []
        materials["episodes"].append(new_episode)

    # timelineにも追加（簡易版）
    for qa in answers:
        if "時期" in qa["question"] or "いつ" in qa["question"] or "年" in qa["answer"]:
            new_timeline = {
                "period": "追加情報",
                "event": qa["answer"][:30],
                "place": "不明",
                "people_involved": [],
                "emotion": "",
                "meaning": qa["answer"]
            }
            if "timeline" not in materials:
                materials["timeline"] = []
            materials["timeline"].append(new_timeline)

    sess["materials"] = materials
    # 追加質問に答えたことをマーク（無限ループ防止）
    sess["additional_questions_answered"] = True
    save_session(user_id, sess)

    print(f"✅ Materials updated: {len(materials.get('episodes', []))} episodes, {len(materials.get('timeline', []))} timeline")

    # 追加質問に答えた場合、不足チェックをスキップ（十分とみなす）
    insufficiency_check = {"insufficient": False, "additional_questions": []}

    return {
        "success": True,
        "user_id": user_id,
        "materials_updated": True,
        "still_insufficient": insufficiency_check["insufficient"],
        "remaining_questions": insufficiency_check["additional_questions"] if insufficiency_check["insufficient"] else []
    }

@app.get("/generate_story/{user_id}")
def generate_story(user_id: str):
    """
    materials.json から自分史（小説風）を生成
    UNIVERSAL STORY ENGINE v3.0統合版を使用
    章立てで構成、です・ます調
    """
    sess = load_session(user_id)

    if not sess.get("materials"):
        raise HTTPException(400, "Materials not found. Run /materials/{user_id} first.")

    materials_json = json.dumps(sess["materials"], ensure_ascii=False, indent=2)

    prompt = f"""
# UNIVERSAL STORY ENGINE v3.0 - 自分史生成モード

あなたは「ナラティブ設計AI」として、読者を引き込む感動的な自分史を生成します。

---

## ❌ 禁止事項（これらは脚本を「つまらなく」する）

- 現象羅列（「〜しました。〜しました」の連続）
- 教訓回収（「〜が大切だと学びました」）
- 抽象語連打（「挑戦」「成長」「可能性」「絆」の安易な使用）
- 宣伝臭（自己賛美、「素晴らしい」「感動的な」）
- 感情の直接表現（「嬉しかった」「悲しかった」の連発）
- 説明ばかり（シーンがない、レポートになる）
- 葛藤を避ける（ドラマは葛藤から生まれる）
- 単調な展開（ずっと上昇、ずっと平坦）

## ✅ 優先事項

- **Showing（見せる）**: 感情を行動・表情・環境で表現
- **五感描写**: 各章に最低3つ（視覚・聴覚・嗅覚・触覚・味覚）
- **内的対話**: 心の声、自問自答
- **象徴的なオブジェクト**: 繰り返し登場し、意味が変化する物
- **葛藤・試練**: ここがドラマの核心
- **余韻**: すべてを説明せず、読者に想像させる

---

## 物語構造：N型感情曲線 × 弁証法的展開

**テーゼ→アンチテーゼ→ジンテーゼ**の7段階で構成：

### 第一幕：テーゼ（正）の提示

**1. 導入（序章）**: 初期状態を**具体的なシーンで**提示
- ❌ 悪例：「私は平凡な日々を送っていました」
- ✅ 良例：「朝7時、いつもの通勤電車。窓に映る自分の顔は、どこか遠くを見ているようでした。『これが自分の人生なのか』――そんな問いが、心の奥底で静かに渦を巻いていました」
- **要素**: 時間・場所・感覚・内的独白・象徴的オブジェクト

**2. 上昇（第1章）**: 転機の予兆を**感覚的に**描写
- 五感描写（光・音・匂い・触感）、身体反応
- 例：「心臓が高鳴る」「世界の色が変わったように見えた」

**3. ピーク（第2章）**: 最高点を**シーンで見せる**
- ❌ 悪例：「とても嬉しかったです」
- ✅ 良例：「気づけば声を上げて笑っていました。涙が頬を伝うのも構わず、ただその瞬間を噛み締めていました」

### 第二幕：アンチテーゼ（反）の出現

**4. 下降・葛藤（第3章）**: 内的対話と具体的障害
- 矛盾：「しかし、本当にこれでいいのか？」
- 具体的困難：人間関係、資金、時間、自信喪失
- 内的対話：「〜だと思っていた。でも実際は〜だった」
- 天候・季節で心理を象徴

**5. 谷（第4章）**: 不安・孤独・挫折の**臨場感**
- 孤独：「誰もいない部屋」「鳴らない電話」
- 身体感覚：「胸が締め付けられる」「息が詰まる」
- 時間停滞：「同じ日が繰り返されるような」
- **対立の頂点**: テーゼ↔アンチテーゼが激突

### 第三幕：ジンテーゼ（合）への統合

**6. 再上昇（第5-6章）**: 転換の瞬間を劇的に
- エピファニー（突然の気づき）
- 「AでもBでもなく、Cなのだ」
- きっかけとなる象徴的な出来事・言葉・光景

**7. 新しい日常（終章）**: 高次の理解・新たな価値観
- 冒頭との対比（円環構造）
- ❌ 悪例：「これからも頑張ります」
- ✅ 良例：「朝7時、同じ通勤電車。でも今、窓に映る自分の目は、確かな光を湛えていました」

---

## 文章技法

### 1. Showing vs Telling
- ❌ Telling: 「悲しかった」「嬉しかった」
- ✅ Showing: 「声が震えた」「笑みがこぼれた」

### 2. 五感描写（各章最低3つ）
- 視覚：光の角度、色彩、表情
- 聴覚：遠近の音、沈黙
- 嗅覚：季節・場所の匂い
- 触覚：温度、湿度、質感
- 味覚：食事、口の感覚

### 3. 内的独白
- 「〜だと思っていた」
- 自問自答：「なぜ、私は〜？」

### 4. 象徴的オブジェクト
- 写真、手紙、時計、窓、道など
- 章を超えて意味が変化

### 5. 対話シーン
- ❌ 要約：「〜と言われました」
- ✅ 具体的：「『本当にそれでいいの？』と彼女は静かに尋ねました。私は答えられませんでした」

---

## 章構成（3〜7章、各2000〜4000字）

各章の構造：
1. 冒頭：象徴的シーン（時間・場所・感覚）
2. 展開：出来事と心情を交互に
3. 転換点：次への伏線・問い

---

## 必須要件

✅ です・ます調
✅ 断定過多を避ける（「〜かもしれません」）
✅ 余韻「〜なのです」を適度に
✅ 五感描写（各章最低3つ）
✅ 事実を捏造しない（推定は明示）
✅ 説教口調禁止
✅ 温かい距離感
✅ 明確な感情起伏
✅ 葛藤・試練を描く
✅ 弁証法的展開

---

## 出力形式

```json
{{
  "title": "物語のタイトル",
  "subtitle": "サブタイトル",
  "author": "著者名",
  "chapters": [
    {{
      "chapter_number": 1,
      "title": "章タイトル（象徴的・詩的な表現）",
      "body": "本文（2000〜4000字、です・ます調）"
    }}
  ]
}}
```

---

materials:
{materials_json}
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    # Structured Outputsで生成
    response_text = call_ai(messages, json_schema=STORY_SCHEMA, temperature=0.7)

    try:
        parsed = json.loads(response_text)
        sess["story"] = parsed
        save_session(user_id, sess)
        return parsed
    except json.JSONDecodeError as e:
        raise HTTPException(500, f"Failed to parse story JSON: {str(e)}\nRaw output: {response_text[:500]}")

@app.get("/generate_picturebook/{user_id}")
def generate_picturebook(user_id: str, page_count: int = 36, genre: str = "auto"):
    """
    materials.json から自分史絵本を生成
    ページ割（短文） + 挿絵指示を含む（画像生成なし）

    Parameters:
    - page_count: ページ数（12〜48）
    - genre: ジャンル（auto, pet, kids, family, business, ending）
    """
    sess = load_session(user_id)

    if not sess.get("materials"):
        raise HTTPException(400, "Materials not found. Run /materials/{user_id} first.")

    if page_count < 12 or page_count > 48:
        raise HTTPException(400, "page_count must be between 12 and 48")

    materials_json = json.dumps(sess["materials"], ensure_ascii=False, indent=2)

    # ジャンル自動判定
    if genre == "auto":
        materials = sess["materials"]
        # ペット名（犬・猫）が登場 → ペット絵本
        people = materials.get("people", [])
        people_text = " ".join([p.get("name", "") + p.get("relation", "") for p in people])
        if "犬" in people_text or "猫" in people_text or "ペット" in people_text:
            genre = "pet"
        # 子供の年齢が10歳以下 → 子供向け
        elif any("歳" in p.get("relation", "") and "子" in p.get("relation", "") for p in people):
            genre = "kids"
        # デフォルトは家族向け
        else:
            genre = "family"

    # ジャンル別の文体定義
    genre_styles = {
        "pet": {
            "tone": "ほっこり、温かい、優しい",
            "style": """
**ペット絵本の文体**:
- 語尾：「〜ですね」「〜なんです」「〜でした」（優しく語りかける）
- 擬音語・擬態語を積極的に使用：「ぴょんぴょん」「くるくる」「ふわふわ」
- 温かい表現：「愛らしい」「いとおしい」「かわいらしい」
- ペットの視点や気持ちを想像して織り交ぜる：「ポラーは嬉しそうに〜」
- ほっこりする日常の幸せを描く
- 読後に温かい気持ちになる語り口
""",
            "example": "朝の散歩道、ポラーはぴょんぴょんと跳ねながら歩いています。お気に入りの公園が見えると、尻尾をくるくる回して喜びを表現するんです。こんな小さな幸せが、私たちの毎日を温かく照らしてくれますね。"
        },
        "kids": {
            "tone": "楽しい、わくわく、明るい",
            "style": """
**子供向け絵本の文体**:
- 簡単な言葉を使う（漢字は少なめ、ふりがな想定）
- リズム感のある文章：「〜だね」「〜だよ」「〜しようね」
- 楽しい擬音語：「わんわん」「にこにこ」「きらきら」
- ワクワク感を演出：「さあ、どうなるかな？」「すごいね！」
- 子供の目線で世界を描く
- 明るく、前向きな語り口
""",
            "example": "あさになったよ！ポラーはしっぽをぶんぶんふって、おさんぽにいきたいっていってるんだ。そとにでると、きもちいいかぜがふいてきたよ。ポラーもうれしそうだね！"
        },
        "family": {
            "tone": "温かい、穏やか、懐かしい",
            "style": """
**家族向け自分史の文体**:
- です・ます調、丁寧だが親しみやすい
- 思い出を振り返る語り口：「あの日は〜でした」
- 家族の絆を感じさせる表現
- 懐かしさと温かさのバランス
- 日常の中の特別な瞬間を描く
""",
            "example": "あの朝、家族みんなで散歩に出かけました。ポラーは嬉しそうに先を歩き、時々振り返っては私たちを確認します。こんな何気ない時間が、実はかけがえのない思い出になっていくのですね。"
        },
        "business": {
            "tone": "真面目、丁寧、記録的",
            "style": """
**ビジネス・企業向けの文体**:
- フォーマルな語り口：「〜いたしました」「〜でございます」
- 事実を正確に記録する姿勢
- 客観的な描写を心がける
- 時系列を明確に
- 成長や変化を丁寧に追う
""",
            "example": "2018年4月、当社は新たな挑戦を開始いたしました。市場環境の変化に対応し、お客様のニーズに寄り添うサービスを模索する日々が続きました。社員一同、試行錯誤を重ねながら前進してまいりました。"
        },
        "ending": {
            "tone": "穏やか、回顧的、余韻",
            "style": """
**エンディング・高齢者向けの文体**:
- 落ち着いた語り口：「〜でしたね」「〜だったのです」
- 回顧的、人生を振り返る視点
- 静かな感謝と受容
- 人生の意味を静かに問いかける
- 余韻を大切に、説教臭くない
""",
            "example": "あの日々を思い返すと、心が温かくなります。ポラーと過ごした8年間は、私にとって人生の宝物でした。小さな命との触れ合いが、こんなにも多くのことを教えてくれるとは、思いもしませんでしたね。"
        }
    }

    genre_info = genre_styles.get(genre, genre_styles["family"])

    prompt = f"""
# UNIVERSAL STORY ENGINE v3.0 - 絵本生成モード

以下のmaterialsをもとに、感動的な自分史絵本を作成してください。

## 🎯 今回のジャンル: {genre.upper()}

**文体の方向性**: {genre_info["tone"]}

{genre_info["style"]}

**文体の例**:
{genre_info["example"]}

---

## ❌ 禁止事項（これらは脚本を「つまらなく」する）

- 現象羅列（「〜しました。〜しました」）
- 教訓回収（「〜が大切です」）
- 抽象語連打（「挑戦」「成長」「絆」の安易な使用）
- 感情の直接表現のみ（「嬉しかった」の連発）
- 葛藤を避ける
- 単調な展開（ずっと上昇、ずっと平坦）

## ✅ 優先事項

- **Showing（見せる）**: 感情を行動・表情で表現
  - ❌ Telling: 「嬉しかったです」
  - ✅ Showing: 「ポラーの尻尾が激しく揺れ、私の顔を何度も舐めてきました」
- **具体的な情景**: 時間・場所・五感
  - ❌ 抽象: 「散歩に行きました」
  - ✅ 具体: 「朝7時、まだ冷たい空気の中、ポラーのリードを引くと小さく鳴いて喜びました」
- **内的独白**: 心の声を織り交ぜる
  - 「本当にこれでよかったのか、ふと不安がよぎりました」
- **象徴的なオブジェクト**: 繰り返し登場する物
  - 例：お気に入りのおもちゃ、散歩コース、特定の場所
- **葛藤**: ドラマの核心
  - 単なるハッピーストーリーではなく、不安・迷い・困難を描く
- **余韻**: すべてを説明しない
  - 最後は余韻を残す終わり方（「〜なのかもしれません」）

---

# 感情曲線（N型）× 弁証法構造【必須】

物語は**テーゼ→アンチテーゼ→ジンテーゼ**の弁証法的展開を意識し、以下の7段階で構成してください：

## 第一幕：テーゼ（正）の提示
1. **導入（10%）**: 主人公の初期状態・価値観・世界観を提示。
   - 例：「バスケは過去のもの」「日常は平凡」

2. **上昇（20%）**: 転機1。テーゼが揺らぐ予兆。期待・希望・ワクワク感。
   - 例：「篠山竜青との再会」「忘れていた情熱が蘇る」

3. **ピーク（30%）**: テーゼの仮の肯定。最高点。喜び・達成感・興奮。
   - 例：「絵本プロジェクトを思いつく」「これが答えだ！」

## 第二幕：アンチテーゼ（反）の出現
4. **下降・葛藤（40%）**: テーゼへの疑問。「しかし本当にそうか？」「このままでいいのか？」
   - **矛盾の明示化**：初期の信念と現実のズレ
   - 例：「絵本を作りたいが、本当にそれが正解なのか？」「情熱だけで進めていいのか？」

5. **谷（50%）**: アンチテーゼの最大化。不安・孤独・挫折感。
   - **対立の頂点**：テーゼとアンチテーゼが激しく衝突
   - 例：「やっぱり自分には無理だ」「過去の情熱は幻想だったのかもしれない」

## 第三幕：ジンテーゼ（合）への統合
6. **再上昇（60-80%）**: テーゼとアンチテーゼの対話。新しい視点の発見。
   - **統合の兆し**：「AでもBでもなく、Cなのだ」
   - 例：「バスケへの情熱（テーゼ）と現実の困難（アンチテーゼ）を統合し、ファンがいるIPを活用する新しい形（ジンテーゼ）を見出す」

7. **新しい日常（90-100%）**: ジンテーゼの完成。より高次の理解・新たな価値観。
   - 例：「バスケと絵本を統合した新しい挑戦」「過去の自分でも現在の自分でもない、統合された新しい自分」

## 弁証法的対話の例
- テーゼ：「〜だと思っていた」
- アンチテーゼ：「しかし実際は〜だった。本当に〜でいいのか？」
- ジンテーゼ：「だからこそ〜なのだ。〜と〜は矛盾するのではなく、〜として統合できる」

# ページ配分の目安（{page_count}ページの場合）
- 導入: 1-{int(page_count*0.1)}ページ
- 上昇: {int(page_count*0.1)+1}-{int(page_count*0.3)}ページ
- ピーク: {int(page_count*0.3)+1}-{int(page_count*0.35)}ページ
- 下降・葛藤: {int(page_count*0.35)+1}-{int(page_count*0.5)}ページ
- 谷: {int(page_count*0.5)+1}-{int(page_count*0.55)}ページ
- 再上昇: {int(page_count*0.55)+1}-{int(page_count*0.85)}ページ
- 新しい日常: {int(page_count*0.85)+1}-{page_count}ページ

# 必須要件（厳守）
1. ページ数は{page_count}ページ
2. **【重要】1ページの文章は最低200字、推奨300字以上**
   - 必ず以下を含める：
     * 具体的な情景描写（時間、場所、天候、周囲の様子）
     * 五感描写（視覚、聴覚、嗅覚、触覚から2〜3つ）
     * 主人公の内的独白や心情
     * Showing技法（感情を行動・表情で表現）
   - 1〜2文で終わらせない。4〜6文で構成する
3. **文体は必ず上記「{genre.upper()}」ジャンルの指示に従う**
4. 断定過多を避け、{genre_info["tone"]}な語り口
5. **各ページの感情温度を明確に**（喜び→不安→葛藤→決意など）
6. **Showing技法を活用**：説明ではなく、具体的なシーンで見せる
7. **五感描写を含める**：視覚、聴覚、嗅覚、触覚、味覚のうち2〜3つ
8. 各ページに挿絵用のプロンプト（英語）を付ける
9. 挿絵プロンプトは具体的な情景描写＋感情を反映（表情、光、色彩、天候など）
10. 事実を捏造しない。不足部分は「想像」「〜かもしれません」で補う
11. 説教口調禁止
12. **葛藤・試練を明確に描写する**（これが物語の深みを作る）

# 禁止事項
- **1ページが200字未満**（絶対に避ける。最低200字、推奨300字以上）
- **1〜2文で終わる**（必ず4〜6文で構成）
- 単調な展開（ずっと上昇、ずっと平坦）
- 感情の起伏がない文章
- 葛藤を避ける（葛藤こそがドラマ）
- 教訓的な締めくくり
- **説明だけで終わる**（Showing技法を使わない）
- **抽象的な表現のみ**（「散歩に行きました」ではなく、具体的なシーンを描く）
- **テーゼを提示しない**（読者が初期状態を理解できない）
- **アンチテーゼが弱い**（矛盾・疑問が曖昧）
- **ジンテーゼが安易**（「頑張ります」で終わる。統合された新しい答えを示す）
- **弁証法的飛躍がない**（AとBを並べるだけで、Cに昇華しない）

materials:
{materials_json}
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    # Structured Outputsで生成（temperature高めで創造性向上）
    response_text = call_ai(messages, json_schema=PICTUREBOOK_SCHEMA, temperature=0.85)

    try:
        parsed = json.loads(response_text)
        sess["picturebook"] = parsed
        save_session(user_id, sess)
        return parsed
    except json.JSONDecodeError as e:
        raise HTTPException(500, f"Failed to parse picturebook JSON: {str(e)}\nRaw output: {response_text[:500]}")

@app.get("/generate_picturebook_with_images/{user_id}")
def generate_picturebook_with_images(
    user_id: str,
    page_count: int = 36,
    max_images: int = 10
):
    """
    materials.json から自分史絵本を生成し、AI画像も生成

    Parameters:
    - page_count: ページ数（12〜48）
    - max_images: 生成する画像の最大数（コスト削減のため。0=すべて生成）

    Note: DALL-E 3は1枚約$0.04かかるため、max_imagesで制限可能
    """
    # まず絵本データを生成
    picturebook_data = generate_picturebook(user_id, page_count)

    # 画像生成数を決定
    pages = picturebook_data.get("pages", [])
    total_pages = len(pages)

    if max_images == 0:
        max_images = total_pages

    images_to_generate = min(max_images, total_pages)

    # 均等に分散して画像生成（例：36ページで10枚なら、3.6ページごと）
    if images_to_generate < total_pages:
        step = total_pages / images_to_generate
        page_indices = [int(i * step) for i in range(images_to_generate)]
    else:
        page_indices = list(range(total_pages))

    # 画像生成
    generated_images = []
    for idx in page_indices:
        page = pages[idx]
        page_number = page.get("page_number", idx + 1)
        prompt = page.get("illustration_prompt", "")

        if not prompt:
            continue

        print(f"🎨 Generating image for page {page_number}...")
        image_path = generate_image(prompt, user_id, page_number)

        if image_path:
            page["image_path"] = image_path
            generated_images.append({
                "page_number": page_number,
                "image_path": image_path,
                "prompt": prompt
            })
            print(f"✅ Page {page_number} image saved: {image_path}")
        else:
            print(f"❌ Page {page_number} image generation failed")

    # 更新されたデータを保存
    sess = load_session(user_id)
    sess["picturebook"] = picturebook_data
    save_session(user_id, sess)

    return {
        "picturebook": picturebook_data,
        "generated_images": generated_images,
        "total_pages": total_pages,
        "images_generated": len(generated_images),
        "cost_estimate_usd": len(generated_images) * 0.04
    }

@app.get("/export/{user_id}")
def export_content(
    user_id: str,
    type: Literal["materials", "story", "picturebook"] = "story",
    format: Literal["json"] = "json"
):
    """
    生成済みコンテンツのエクスポート
    将来的にPDF出力などに拡張可能
    """
    sess = load_session(user_id)

    if type not in sess or sess[type] is None:
        raise HTTPException(404, f"{type} has not been generated yet.")

    payload = sess[type]

    if format == "json":
        return payload

    # 将来的にPDF等の対応を追加
    raise HTTPException(400, f"Format {format} is not supported yet.")

@app.post("/complete_story_generation/{user_id}")
def complete_story_generation(
    user_id: str,
    generate_type: Literal["story", "picturebook", "both"] = "both",
    page_count: int = 24,
    with_images: bool = False,
    max_images: int = 7
):
    """
    インタビュー完了後の統合フロー
    materials → story/picturebook を自動生成

    Parameters:
    - generate_type: 生成タイプ（story, picturebook, both）
    - page_count: 絵本のページ数
    - with_images: 画像生成するか
    - max_images: 最大画像数
    """
    sess = load_session(user_id)

    if not sess.get("messages"):
        raise HTTPException(400, "No interview session found. Start an interview first.")

    result = {
        "user_id": user_id,
        "steps_completed": [],
        "materials": None,
        "story": None,
        "picturebook": None,
        "images": None
    }

    # Step 1: materials生成（追加質問回答後は既存materialsを使用）
    if sess.get("materials") and sess.get("additional_questions_answered"):
        print(f"📦 Step 1/4: Using existing materials (additional questions answered)...")
        materials = sess["materials"]
        result["materials"] = materials
        result["steps_completed"].append("materials")
        print(f"✅ Using existing materials: {len(materials.get('episodes', []))} episodes, {len(materials.get('timeline', []))} timeline")
    else:
        print(f"📦 Step 1/4: Generating materials for {user_id}...")
        try:
            materials = get_materials(user_id)
            result["materials"] = materials
            result["steps_completed"].append("materials")
            print("✅ Materials generated")
        except Exception as e:
            raise HTTPException(500, f"Materials generation failed: {str(e)}")

    # Step 1.5: 不足検知（追加質問に既に答えている場合はスキップ）
    if sess.get("additional_questions_answered"):
        print(f"✅ Additional questions already answered, skipping insufficiency check")
    else:
        print(f"🔍 Checking materials insufficiency...")
        insufficiency_check = check_materials_insufficiency(materials)

        if insufficiency_check["insufficient"]:
            print(f"⚠️ Materials insufficient: {', '.join(insufficiency_check['missing_elements'])}")
            # 不足があれば、追加質問を返して中断
            return {
                "success": False,
                "user_id": user_id,
                "requires_additional_info": True,
                "missing_elements": insufficiency_check["missing_elements"],
                "additional_questions": insufficiency_check["additional_questions"],
                "reasoning": insufficiency_check["reasoning"],
                "message": "物語の深みを出すために、追加の情報が必要です。以下の質問にお答えください。"
            }

        print(f"✅ Materials sufficient, proceeding to story generation")

    # Step 2: story生成
    if generate_type in ["story", "both"]:
        print(f"📖 Step 2/4: Generating story for {user_id}...")
        try:
            story = generate_story(user_id)
            result["story"] = story
            result["steps_completed"].append("story")
            print("✅ Story generated")
        except Exception as e:
            print(f"⚠️ Story generation failed: {str(e)}")
            result["story"] = {"error": str(e)}

    # Step 3: picturebook生成
    if generate_type in ["picturebook", "both"]:
        print(f"📚 Step 3/4: Generating picturebook for {user_id}...")
        try:
            if with_images:
                picturebook_result = generate_picturebook_with_images(user_id, page_count, max_images)
                result["picturebook"] = picturebook_result["picturebook"]
                result["images"] = picturebook_result["generated_images"]
                result["steps_completed"].append("picturebook_with_images")
                print(f"✅ Picturebook with {len(result['images'])} images generated")
            else:
                picturebook = generate_picturebook(user_id, page_count)
                result["picturebook"] = picturebook
                result["steps_completed"].append("picturebook")
                print("✅ Picturebook generated")
        except Exception as e:
            print(f"⚠️ Picturebook generation failed: {str(e)}")
            result["picturebook"] = {"error": str(e)}

    print(f"🎉 Complete! Steps completed: {', '.join(result['steps_completed'])}")

    return {
        "success": True,
        "user_id": user_id,
        "steps_completed": result["steps_completed"],
        "materials_summary": {
            "timeline_count": len(result["materials"].get("timeline", [])),
            "people_count": len(result["materials"].get("people", [])),
            "episodes_count": len(result["materials"].get("episodes", []))
        } if result["materials"] else None,
        "story_summary": {
            "title": result["story"].get("title"),
            "chapters": len(result["story"].get("chapters", []))
        } if result.get("story") and not result["story"].get("error") else None,
        "picturebook_summary": {
            "title": result["picturebook"].get("title"),
            "pages": result["picturebook"].get("total_pages"),
            "images_generated": len(result.get("images") or [])
        } if result.get("picturebook") and not result["picturebook"].get("error") else None,
        "output_paths": {
            "session": f"sessions/{user_id}.json",
            "images": f"../output/picturebook_images/{user_id}/" if result.get("images") else None
        }
    }

@app.delete("/session/{user_id}")
def delete_session(user_id: str):
    """セッションの削除（デバッグ用）"""
    fp = DATA_DIR / f"{user_id}.json"
    if fp.exists():
        fp.unlink()
        return {"message": f"Session for {user_id} deleted."}
    else:
        raise HTTPException(404, "Session not found.")

@app.get("/sessions")
def list_sessions():
    """全セッション一覧（デバッグ用）"""
    sessions = [f.stem for f in DATA_DIR.glob("*.json")]
    return {"sessions": sessions, "count": len(sessions)}


# ---- Run Server ----
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Memoir Editor AI API...")
    print(f"📁 Session data directory: {DATA_DIR.absolute()}")
    print(f"🤖 Using model: {MODEL_NAME}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
