#!/usr/bin/env python3
"""
ペット写真×AI作品化サービスに関するアンケートフォーム作成スクリプト
Google Forms APIを使用してフォームを自動生成します
"""

import os
import sys
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
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
        except Exception as e:
            print(f"トークン保存エラー: {e}")

    return creds

def create_choice_question(options, required=True, multi_select=False):
    """選択式の質問を作成"""
    question_type = "CHECKBOX" if multi_select else "RADIO"
    return {
        "required": required,
        "choiceQuestion": {
            "type": question_type,
            "options": [{"value": opt} for opt in options]
        }
    }

def create_text_question(paragraph=True, required=False):
    """テキスト入力の質問を作成"""
    return {
        "required": required,
        "textQuestion": {
            "paragraph": paragraph
        }
    }

def create_pet_ai_form():
    """ペット写真×AI作品化サービスのアンケートフォームを作成"""
    print("Google Forms APIに接続中...")
    creds = get_credentials()

    try:
        # Forms APIサービスを構築
        forms_service = build('forms', 'v1', credentials=creds)

        # フォームの基本情報
        form = {
            "info": {
                "title": "ペット写真×AI作品化サービスに関するアンケート",
                "documentTitle": "ペット写真×AI作品化サービスに関するアンケート"
            }
        }

        print("フォームを作成中...")
        # フォームを作成
        result = forms_service.forms().create(body=form).execute()
        form_id = result['formId']

        print(f"✓ フォーム作成完了: {form_id}")

        # フォームに質問を追加
        requests = []
        location_index = 0

        # 説明文
        requests.append({
            "createItem": {
                "item": {
                    "title": "サービス概要",
                    "description": "あなたのペットの写真を、ひとことコメントと一緒に送るだけで、AIが物語付きの作品（デジタル作品や絵本など）に仕上げてくれるサービスがあったら、あなたは利用したいと思いますか？\n率直なご意見をお聞かせください。",
                    "textItem": {}
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問1: 年代
        requests.append({
            "createItem": {
                "item": {
                    "title": "あなたの年代を教えてください",
                    "questionItem": {
                        "question": create_choice_question([
                            "20代以下",
                            "30代",
                            "40代",
                            "50代以上",
                            "回答しない"
                        ], required=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問2: 性別
        requests.append({
            "createItem": {
                "item": {
                    "title": "性別を教えてください",
                    "questionItem": {
                        "question": create_choice_question([
                            "女性",
                            "男性",
                            "その他",
                            "回答しない"
                        ], required=False)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問3: 家族構成
        requests.append({
            "createItem": {
                "item": {
                    "title": "家族構成を教えてください",
                    "questionItem": {
                        "question": create_choice_question([
                            "一人暮らし",
                            "夫婦のみ",
                            "子どもあり",
                            "その他"
                        ], required=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問4: ペットの種類
        requests.append({
            "createItem": {
                "item": {
                    "title": "飼っているペットの種類を教えてください",
                    "questionItem": {
                        "question": create_choice_question([
                            "犬",
                            "猫",
                            "その他"
                        ], required=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問5: ペットの年齢
        requests.append({
            "createItem": {
                "item": {
                    "title": "ペットの年齢を教えてください",
                    "questionItem": {
                        "question": create_choice_question([
                            "1歳未満",
                            "1〜5歳",
                            "6〜10歳",
                            "10歳以上"
                        ], required=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問6: SNS投稿頻度
        requests.append({
            "createItem": {
                "item": {
                    "title": "SNSへの投稿頻度について教えてください",
                    "questionItem": {
                        "question": create_choice_question([
                            "よく投稿する",
                            "たまに投稿する",
                            "ほとんど投稿しない"
                        ], required=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問7: 作品化の方向性
        requests.append({
            "createItem": {
                "item": {
                    "title": "あなたのペットの写真を作品化するとしたら、どの方向性に魅力を感じますか？",
                    "questionItem": {
                        "question": create_choice_question([
                            "思い出をより美しく残す（写真寄り）",
                            "物語の主人公として描く（キャラクター寄り）",
                            "アート作品として飾れる形にする",
                            "コミカルに楽しめるイラスト化",
                            "特にこだわりはない"
                        ], required=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問8: 作品のテイスト（複数選択）
        requests.append({
            "createItem": {
                "item": {
                    "title": "作品のテイストについて、どれが近いですか？（複数選択可）",
                    "questionItem": {
                        "question": create_choice_question([
                            "実写に近い仕上がり",
                            "少しイラスト寄り",
                            "完全にイラスト化",
                            "毎回テイストが変わってもよい",
                            "テイストは重要ではない"
                        ], required=False, multi_select=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問9: 利用用途（複数選択）
        requests.append({
            "createItem": {
                "item": {
                    "title": "このようなサービスを利用するとしたら、主な用途は何ですか？（複数選択可）",
                    "questionItem": {
                        "question": create_choice_question([
                            "SNS投稿",
                            "家族との共有",
                            "思い出として保存",
                            "絵本として残したい",
                            "グッズにしたい",
                            "プレゼントにしたい",
                            "その他"
                        ], required=False, multi_select=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問10: 魅力を感じる理由（複数選択）
        requests.append({
            "createItem": {
                "item": {
                    "title": "このサービスに魅力を感じる理由は何ですか？（複数選択可）",
                    "questionItem": {
                        "question": create_choice_question([
                            "ペットとの思い出を形に残したい",
                            "世界にひとつだけの作品になる",
                            "SNSでシェアしたい",
                            "ペットを主人公にした物語を見てみたい",
                            "特別な記念にしたい",
                            "その他"
                        ], required=False, multi_select=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問11: 月額料金
        requests.append({
            "createItem": {
                "item": {
                    "title": "月額サービスの場合、いくらまでなら利用を検討しますか？",
                    "questionItem": {
                        "question": create_choice_question([
                            "〜500円",
                            "〜1,000円",
                            "〜1,500円",
                            "〜2,000円",
                            "〜3,000円",
                            "3,000円以上",
                            "月額では利用しない"
                        ], required=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問12: 単発購入料金
        requests.append({
            "createItem": {
                "item": {
                    "title": "単発購入の場合、いくらまでなら購入を検討しますか？",
                    "questionItem": {
                        "question": create_choice_question([
                            "〜1,000円",
                            "〜2,000円",
                            "〜3,000円",
                            "〜5,000円",
                            "5,000円以上",
                            "購入しない"
                        ], required=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問13: 物理アイテム（複数選択）
        requests.append({
            "createItem": {
                "item": {
                    "title": "物理アイテムとして欲しいものはありますか？（複数選択可）",
                    "questionItem": {
                        "question": create_choice_question([
                            "絵本（ハードカバー）",
                            "アートフレーム",
                            "トートバッグ",
                            "スマホケース",
                            "ポストカード",
                            "データのみで十分",
                            "その他"
                        ], required=False, multi_select=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問14: 利用意向
        requests.append({
            "createItem": {
                "item": {
                    "title": "このサービスを実際に利用してみたいと思いますか？",
                    "questionItem": {
                        "question": create_choice_question([
                            "ぜひ利用したい",
                            "条件が合えば利用したい",
                            "あまり利用したいと思わない",
                            "利用しないと思う"
                        ], required=True)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 質問15: 自由記述
        requests.append({
            "createItem": {
                "item": {
                    "title": "利用したい／したくない理由を教えてください",
                    "questionItem": {
                        "question": create_text_question(paragraph=True, required=False)
                    }
                },
                "location": {"index": location_index}
            }
        })
        location_index += 1

        # 完了メッセージ
        requests.append({
            "createItem": {
                "item": {
                    "title": "アンケートにご協力いただきありがとうございました。",
                    "textItem": {}
                },
                "location": {"index": location_index}
            }
        })

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

        # URLをファイルに保存
        output_file = "/Users/attadesign/ai-management-system/output/pet_ai_form_urls.txt"
        with open(output_file, 'w') as f:
            f.write(f"ペット写真×AI作品化サービスに関するアンケート\n")
            f.write(f"作成日時: {result.get('createTime', 'N/A')}\n\n")
            f.write(f"フォームID: {form_id}\n\n")
            f.write(f"編集URL:\nhttps://docs.google.com/forms/d/{form_id}/edit\n\n")
            f.write(f"回答URL:\nhttps://docs.google.com/forms/d/{form_id}/viewform\n")

        print(f"\nURLを保存しました: {output_file}")

        return form_id

    except HttpError as error:
        print(f"エラーが発生しました: {error}")
        return None
    except Exception as e:
        print(f"予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    create_pet_ai_form()
