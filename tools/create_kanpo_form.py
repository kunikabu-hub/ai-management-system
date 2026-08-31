#!/usr/bin/env python3
"""
かんぽCX通信 絵本PoC評価アンケートフォーム作成スクリプト
Google Forms APIを使用してフォームを自動生成します
"""

import os
import sys
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import json

# 必要なスコープ
SCOPES = [
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/drive'
]

# 認証情報の保存場所
TOKEN_DIR = os.path.expanduser('~/.config/claude-code/gdrive')
TOKEN_PATH = os.path.join(TOKEN_DIR, 'token.json')
CREDENTIALS_PATH = os.path.join(TOKEN_DIR, 'credentials.json')

def get_credentials():
    """Google API認証情報を取得"""
    creds = None

    # トークンファイルが存在する場合は読み込み
    if os.path.exists(TOKEN_PATH):
        try:
            with open(TOKEN_PATH, 'r') as token:
                token_data = json.load(token)
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"既存のトークン読み込みエラー: {e}")

    # 認証情報が無効または存在しない場合
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("トークンを更新中...")
                creds.refresh(Request())
            except Exception as e:
                print(f"トークン更新エラー: {e}")
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"エラー: 認証情報ファイルが見つかりません: {CREDENTIALS_PATH}")
                print("Google Cloud Consoleで認証情報を作成し、ファイルを配置してください。")
                sys.exit(1)

            try:
                print("新規認証を開始します...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print(f"認証エラー: {e}")
                sys.exit(1)

        # トークンを保存
        try:
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
            print(f"トークンを保存しました: {TOKEN_PATH}")
        except Exception as e:
            print(f"トークン保存エラー: {e}")

    return creds

def create_linear_scale_question(low_label="全くそう思わない", high_label="強くそう思う",
                                 low=1, high=5, required=True):
    """5段階評価の質問を作成"""
    return {
        "required": required,
        "scaleQuestion": {
            "low": low,
            "high": high,
            "lowLabel": low_label,
            "highLabel": high_label
        }
    }

def create_text_question(paragraph=False, required=False):
    """テキスト入力の質問を作成"""
    return {
        "required": required,
        "textQuestion": {
            "paragraph": paragraph
        }
    }

def create_choice_question(options, required=True):
    """選択式の質問を作成"""
    return {
        "required": required,
        "choiceQuestion": {
            "type": "RADIO",
            "options": [{"value": opt} for opt in options]
        }
    }

def create_kanpo_form():
    """かんぽCX通信アンケートフォームを作成"""
    print("Google Forms APIに接続中...")
    creds = get_credentials()

    try:
        # Forms APIサービスを構築
        forms_service = build('forms', 'v1', credentials=creds)

        # フォームの基本情報
        form = {
            "info": {
                "title": "かんぽCX通信 絵本PoC評価アンケート",
                "documentTitle": "かんぽCX通信 絵本PoC評価アンケート（目的：行動変容の可能性検証）"
            }
        }

        print("フォームを作成中...")
        # フォームを作成
        result = forms_service.forms().create(body=form).execute()
        form_id = result['formId']
        form_url = f"https://docs.google.com/forms/d/{form_id}/edit"

        print(f"✓ フォーム作成完了: {form_id}")
        print(f"  編集URL: {form_url}")

        # フォームに質問を追加
        requests = []
        location_index = 0

        # 冒頭説明文（テキストアイテムとして追加）
        requests.append({
            "createItem": {
                "item": {
                    "title": "アンケートについて",
                    "description": "本アンケートは、物語コンテンツが営業現場での「行動変容」に寄与する可能性を検証するためのものです。物語の完成度ではなく、ご自身の業務への影響という観点でご回答ください。\n\n所要時間：約5分",
                    "textItem": {}
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # ========================================
        # 基本情報セクション
        # ========================================
        requests.append({
            "createItem": {
                "item": {
                    "title": "■ 基本情報",
                    "pageBreakItem": {}
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 所属部署（任意）
        requests.append({
            "createItem": {
                "item": {
                    "title": "所属部署（任意）",
                    "questionItem": {
                        "question": create_text_question(paragraph=False, required=False)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 職種
        requests.append({
            "createItem": {
                "item": {
                    "title": "職種",
                    "questionItem": {
                        "question": create_choice_question(
                            ["営業", "管理職", "CX推進", "その他"],
                            required=True
                        )
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # ========================================
        # 第1セクション：全体を通しての評価
        # ========================================
        requests.append({
            "createItem": {
                "item": {
                    "title": "■ 第1セクション：全体を通しての評価",
                    "pageBreakItem": {}
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        section1_questions = [
            "あなたにとってこの物語は感動や気づきを得られるものでしたか？",
            "話の流れは納得できるものでしたか？",
            "この物語を他の人にも読んでほしいと思いますか？"
        ]

        for q in section1_questions:
            requests.append({
                "createItem": {
                    "item": {
                        "title": q,
                        "questionItem": {
                            "question": create_linear_scale_question()
                        }
                    },
                    "location": {"index": location_index}
                }
            })
            location_index += 1

        # ========================================
        # 第2セクション：物語への没入度と共感
        # ========================================
        requests.append({
            "createItem": {
                "item": {
                    "title": "■ 第2セクション：物語への没入度と共感",
                    "pageBreakItem": {}
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        section2_questions = [
            "物語の登場人物の判断や行動に、共感できる部分はありましたか？",
            "物語の状況は自分の日常の営業現場でもあることだと思いましたか？"
        ]

        for q in section2_questions:
            requests.append({
                "createItem": {
                    "item": {
                        "title": q,
                        "questionItem": {
                            "question": create_linear_scale_question()
                        }
                    },
                    "location": {"index": location_index}
                }
            })
            location_index += 1

        # ========================================
        # 第3セクション：接客に対する「気づき」と自己客観視
        # ========================================
        requests.append({
            "createItem": {
                "item": {
                    "title": "■ 第3セクション：接客に対する「気づき」と自己客観視",
                    "pageBreakItem": {}
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        section3_questions = [
            "物語は、これまでの自分の接客スタイルを振り返るきっかけになりましたか？",
            "登場人物が示した「接客の本質」には共感しましたか？"
        ]

        for q in section3_questions:
            requests.append({
                "createItem": {
                    "item": {
                        "title": q,
                        "questionItem": {
                            "question": create_linear_scale_question()
                        }
                    },
                    "location": {"index": location_index}
                }
            })
            location_index += 1

        # ========================================
        # 第4セクション：行動変容への意志
        # ========================================
        requests.append({
            "createItem": {
                "item": {
                    "title": "■ 第4セクション：行動変容への意志",
                    "pageBreakItem": {}
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        section4_questions = [
            "物語の教訓を活かして自分の接客を具体的に「変えてみたい」と思いましたか？",
            "物語の教訓について、これからも自分の接客を「自信を持って継続しよう」と思いましたか？"
        ]

        for q in section4_questions:
            requests.append({
                "createItem": {
                    "item": {
                        "title": q,
                        "questionItem": {
                            "question": create_linear_scale_question()
                        }
                    },
                    "location": {"index": location_index}
                }
            })
            location_index += 1

        # 具体的な行動変容（自由記述）
        requests.append({
            "createItem": {
                "item": {
                    "title": "具体的にどのような行動を変えようと思いましたか？",
                    "questionItem": {
                        "question": create_text_question(paragraph=True, required=False)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # ========================================
        # 第5セクション：導入推奨度
        # ========================================
        requests.append({
            "createItem": {
                "item": {
                    "title": "■ 第5セクション：導入推奨度",
                    "pageBreakItem": {}
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        requests.append({
            "createItem": {
                "item": {
                    "title": "この取り組みを営業現場に導入すべきだと思いますか？",
                    "questionItem": {
                        "question": create_linear_scale_question(
                            low_label="全く推奨しない",
                            high_label="強く推奨する",
                            low=0,
                            high=10
                        )
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # ========================================
        # 第6セクション：行動変容の阻害要因
        # ========================================
        requests.append({
            "createItem": {
                "item": {
                    "title": "■ 第6セクション：行動変容の阻害要因",
                    "pageBreakItem": {}
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        section6_questions = [
            "物語で得た気づきを実践するにあたって、障壁になりそうなことはありますか？",
            "物語の教訓は自分の業務には当てはまらないと思いましたか？"
        ]

        for q in section6_questions:
            requests.append({
                "createItem": {
                    "item": {
                        "title": q,
                        "questionItem": {
                            "question": create_linear_scale_question()
                        }
                    },
                    "location": {"index": location_index}
                }
            })
            location_index += 1

        # ========================================
        # 自由記述セクション
        # ========================================
        requests.append({
            "createItem": {
                "item": {
                    "title": "■ 自由記述",
                    "pageBreakItem": {}
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        free_text_questions = [
            "物語で「なるほど」と思った箇所、不自然だと感じた箇所があれば教えてください。",
            "気づきを実践する際に障害がある場合、何が障害になりそうか具体的に教えてください。",
            "物語で語られているような接客で重要なことは、ほかにどのようなものがあるか教えてください。（任意）"
        ]

        for q in free_text_questions:
            requests.append({
                "createItem": {
                    "item": {
                        "title": q,
                        "questionItem": {
                            "question": create_text_question(paragraph=True, required=False)
                        }
                    },
                    "location": {"index": location_index}
                }
            })
            location_index += 1

        # すべての質問を一括で追加
        print(f"質問を追加中... ({len(requests)}項目)")
        forms_service.forms().batchUpdate(
            formId=form_id,
            body={"requests": requests}
        ).execute()

        print("\n" + "="*60)
        print("✓ フォーム作成が完了しました！")
        print("="*60)
        print(f"\nフォームID: {form_id}")
        print(f"\n編集URL: https://docs.google.com/forms/d/{form_id}/edit")
        print(f"回答URL: https://docs.google.com/forms/d/{form_id}/viewform")
        print("\n※ フォームの共有設定は、Google Formsの画面で調整してください。")

        # URLをファイルに保存
        output_file = "/Users/attadesign/ai-management-system/output/kanpo_form_urls.txt"
        with open(output_file, 'w') as f:
            f.write(f"かんぽCX通信 絵本PoC評価アンケート\n")
            f.write(f"作成日時: {result.get('createTime', 'N/A')}\n\n")
            f.write(f"フォームID: {form_id}\n\n")
            f.write(f"編集URL:\nhttps://docs.google.com/forms/d/{form_id}/edit\n\n")
            f.write(f"回答URL:\nhttps://docs.google.com/forms/d/{form_id}/viewform\n")

        print(f"\nURLを保存しました: {output_file}")

        return form_id

    except HttpError as error:
        print(f"エラーが発生しました: {error}")
        if "PERMISSION_DENIED" in str(error):
            print("\n認証スコープが不足している可能性があります。")
            print("Google Cloud ConsoleでForms APIを有効化してください。")
        return None
    except Exception as e:
        print(f"予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    create_kanpo_form()
