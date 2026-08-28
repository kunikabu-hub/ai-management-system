#!/usr/bin/env python3
"""
かんぽ生命PoC：専門家評価Googleフォーム自動作成スクリプト
Google Forms APIを使用して評価フォームを作成
"""

import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 認証情報のパス
TOKEN_PATH = os.path.expanduser('~/.config/claude-code/gdrive/token.json')
CREDENTIALS_PATH = os.path.expanduser('~/.config/claude-code/gdrive/credentials.json')

def create_evaluation_form():
    """専門家評価フォームを作成"""

    try:
        # 認証情報を読み込み
        creds = Credentials.from_authorized_user_file(TOKEN_PATH)

        # Google Forms APIサービスを構築
        service = build('forms', 'v1', credentials=creds)

        # フォームの基本情報
        form = {
            "info": {
                "title": "かんぽ生命 CX通信絵本脚本 専門家評価",
                "documentTitle": "かんぽ生命_専門家評価フォーム"
            }
        }

        # フォームを作成
        print("📝 フォームを作成中...")
        result = service.forms().create(body=form).execute()
        form_id = result['formId']
        form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
        response_url = f"https://docs.google.com/forms/d/{form_id}/viewform"

        print(f"✅ フォームを作成しました")
        print(f"   フォームID: {form_id}")

        # フォームに質問を追加
        print("\n📋 質問を追加中...")

        requests = []

        # セクション1: 基本情報
        requests.extend([
            # 質問1: 評価者名
            {
                "createItem": {
                    "item": {
                        "title": "お名前を入力してください",
                        "questionItem": {
                            "question": {
                                "required": True,
                                "textQuestion": {
                                    "paragraph": False
                                }
                            }
                        }
                    },
                    "location": {"index": 0}
                }
            },
            # 質問2: 評価日
            {
                "createItem": {
                    "item": {
                        "title": "評価日",
                        "questionItem": {
                            "question": {
                                "required": True,
                                "dateQuestion": {}
                            }
                        }
                    },
                    "location": {"index": 1}
                }
            },
            # 質問3: 脚本名
            {
                "createItem": {
                    "item": {
                        "title": "評価する脚本名を入力してください",
                        "description": "例：19-7『机の上の太陽』",
                        "questionItem": {
                            "question": {
                                "required": True,
                                "textQuestion": {
                                    "paragraph": False
                                }
                            }
                        }
                    },
                    "location": {"index": 2}
                }
            },
            # ページ区切り
            {
                "createItem": {
                    "item": {
                        "title": "評価項目（25点満点）",
                        "pageBreakItem": {}
                    },
                    "location": {"index": 3}
                }
            }
        ])

        # 質問4: ①PLG実現度
        requests.append({
            "createItem": {
                "item": {
                    "title": "①PLG実現度（感情曲線のN字型が読者の心を動かすか）",
                    "description": "PLG（プロットライングラフ）= 感情曲線のN字型\n\n評価ポイント：\n・谷（最悪の状況）で読者が「つらい」と感じるか\n・転換点で「おっ！」と心が動くか\n・結末で「よかった」と温かい気持ちになるか",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "6点：N字型が鮮明で、読者が自然に感情移入できる。谷→転換→上昇が感動的"},
                                    {"value": "5点：N字型が効果的。一部のシーンで感情の深みがもう一段ほしい"},
                                    {"value": "4点：N字型は見えるが、感情の動きが心を動かす力は普通"},
                                    {"value": "3点：感情曲線の構造はあるが、理屈で理解できても心が動かない"},
                                    {"value": "2点：N字型が不明瞭。感情の起伏が弱い"},
                                    {"value": "1点：感情曲線が平坦、または不自然"}
                                ]
                            }
                        }
                    }
                },
                "location": {"index": 4}
            }
        })

        # 質問5: ①のコメント
        requests.append({
            "createItem": {
                "item": {
                    "title": "①PLG実現度のコメント・改善点",
                    "questionItem": {
                        "question": {
                            "required": False,
                            "textQuestion": {
                                "paragraph": True
                            }
                        }
                    }
                },
                "location": {"index": 5}
            }
        })

        # 質問6: ②弁証法的構造
        requests.append({
            "createItem": {
                "item": {
                    "title": "②弁証法的構造の完成度（正→反→合の展開の説得力）",
                    "description": "弁証法 = 正（テーゼ）→ 反（アンチテーゼ）→ 合（ジンテーゼ）\n\n評価ポイント：\n・正（初期状態・準備）が明確か\n・反（矛盾・挫折）が深刻で説得力があるか\n・合（統合・成長）が感動的か",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "6点：正→反→合の展開が明確で説得力がある。矛盾が深く、統合が感動的"},
                                    {"value": "5点：弁証法的展開が良好。一部の要素がやや弱い"},
                                    {"value": "4点：標準的。三段階は見えるが、深みに欠ける"},
                                    {"value": "3点：弁証法的展開が不明瞭。どこかの段階が弱い"},
                                    {"value": "2点：正→反→合の構造が崩れている"},
                                    {"value": "1点：弁証法的展開がない。単なる時系列の羅列"}
                                ]
                            }
                        }
                    }
                },
                "location": {"index": 6}
            }
        })

        # 質問7: ②のコメント
        requests.append({
            "createItem": {
                "item": {
                    "title": "②弁証法的構造のコメント・改善点",
                    "questionItem": {
                        "question": {
                            "required": False,
                            "textQuestion": {
                                "paragraph": True
                            }
                        }
                    }
                },
                "location": {"index": 7}
            }
        })

        # 質問8: ③創造性バランス
        requests.append({
            "createItem": {
                "item": {
                    "title": "③創造性バランス（新規性・意外性 vs 諒解可能性）",
                    "description": "創造性 = 新規性 + 意外性 + 諒解可能性\n\n評価ポイント：\n・他にない独自の展開があるか（新規性）\n・「そう来たか！」と驚く要素があるか（意外性）\n・読者が理解できるか（諒解可能性）\n・バランスが適切か",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "5点：新規性・意外性と諒解可能性が絶妙にバランス。驚かせつつ、理解できる"},
                                    {"value": "4点：バランスが良好。一部のバランスが偏っている"},
                                    {"value": "3点：標準的。新規性か諒解可能性のどちらかに偏っている"},
                                    {"value": "2点：バランスが悪い。突飛すぎるか、ありふれている"},
                                    {"value": "1点：創造性が感じられない、または理解不能"}
                                ]
                            }
                        }
                    }
                },
                "location": {"index": 8}
            }
        })

        # 質問9: ③のコメント
        requests.append({
            "createItem": {
                "item": {
                    "title": "③創造性バランスのコメント・改善点",
                    "questionItem": {
                        "question": {
                            "required": False,
                            "textQuestion": {
                                "paragraph": True
                            }
                        }
                    }
                },
                "location": {"index": 9}
            }
        })

        # 質問10: ④CX通信の活用度
        requests.append({
            "createItem": {
                "item": {
                    "title": "④CX通信の活用度（元データの効果的な物語化）",
                    "description": "評価ポイント：\n・CX通信の核心的な出来事を含んでいるか\n・営業担当者の気づき・変化が再現されているか\n・創作部分が元データと調和しているか",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "4点：CX通信の核心を的確に捉え、エピソードを効果的に物語化。忠実かつ魅力的"},
                                    {"value": "3点：元データを適切に活用。標準的な再現"},
                                    {"value": "2点：元データとの乖離が目立つ。重要な要素が欠落"},
                                    {"value": "1点：CX通信との関連性が薄い。別のストーリーになっている"}
                                ]
                            }
                        }
                    }
                },
                "location": {"index": 10}
            }
        })

        # 質問11: ④のコメント
        requests.append({
            "createItem": {
                "item": {
                    "title": "④CX通信の活用度のコメント・改善点",
                    "questionItem": {
                        "question": {
                            "required": False,
                            "textQuestion": {
                                "paragraph": True
                            }
                        }
                    }
                },
                "location": {"index": 11}
            }
        })

        # 質問12: ⑤営業活用可能性
        requests.append({
            "createItem": {
                "item": {
                    "title": "⑤営業活用可能性（かんぽ生命のビジネス価値）",
                    "description": "評価ポイント：\n・かんぽらしさ（お客様第一、信頼、温もり）があるか\n・営業担当者が誇りを持って見せられるか\n・顧客ロイヤリティ向上に寄与するか",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "4点：提案資料として即戦力。かんぽらしさが明確で、営業シーンで効果的に使える"},
                                    {"value": "3点：営業ツールとして十分使える。標準的"},
                                    {"value": "2点：営業ツールとしては弱い。用途が限定的"},
                                    {"value": "1点：営業活用が困難。ビジネス目的と合致しない"}
                                ]
                            }
                        }
                    }
                },
                "location": {"index": 12}
            }
        })

        # 質問13: ⑤のコメント
        requests.append({
            "createItem": {
                "item": {
                    "title": "⑤営業活用可能性のコメント・改善点",
                    "questionItem": {
                        "question": {
                            "required": False,
                            "textQuestion": {
                                "paragraph": True
                            }
                        }
                    }
                },
                "location": {"index": 13}
            }
        })

        # ページ区切り（総評）
        requests.append({
            "createItem": {
                "item": {
                    "title": "総評",
                    "pageBreakItem": {}
                },
                "location": {"index": 14}
            }
        })

        # 質問14: 強み
        requests.append({
            "createItem": {
                "item": {
                    "title": "この脚本の強み",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {
                                "paragraph": True
                            }
                        }
                    }
                },
                "location": {"index": 15}
            }
        })

        # 質問15: 改善点
        requests.append({
            "createItem": {
                "item": {
                    "title": "改善が必要な点",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {
                                "paragraph": True
                            }
                        }
                    }
                },
                "location": {"index": 16}
            }
        })

        # 質問16: 次のアクション
        requests.append({
            "createItem": {
                "item": {
                    "title": "推奨する次のアクション",
                    "questionItem": {
                        "question": {
                            "required": False,
                            "textQuestion": {
                                "paragraph": True
                            }
                        }
                    }
                },
                "location": {"index": 17}
            }
        })

        # バッチ更新を実行
        service.forms().batchUpdate(
            formId=form_id,
            body={'requests': requests}
        ).execute()

        print("✅ 質問を追加しました")

        # 設定を更新
        print("\n⚙️  設定を更新中...")
        settings_requests = [
            {
                "updateSettings": {
                    "settings": {
                        "quizSettings": {
                            "isQuiz": False
                        }
                    },
                    "updateMask": "quizSettings.isQuiz"
                }
            }
        ]

        service.forms().batchUpdate(
            formId=form_id,
            body={'requests': settings_requests}
        ).execute()

        print("✅ 設定を更新しました")

        print("\n" + "="*60)
        print("🎉 フォーム作成完了！")
        print("="*60)
        print(f"\n📝 編集用URL:")
        print(f"   {form_url}")
        print(f"\n📋 回答用URL:")
        print(f"   {response_url}")
        print(f"\n💡 次のステップ:")
        print(f"   1. 編集用URLで最終確認")
        print(f"   2. 回答先のスプレッドシートを作成")
        print(f"   3. 回答用URLを評価者に共有")
        print("\n")

        return form_id, form_url, response_url

    except HttpError as error:
        print(f"❌ エラーが発生しました: {error}")
        if 'insufficientPermissions' in str(error):
            print("\n💡 Google Forms APIのスコープが不足している可能性があります。")
            print("   以下の手順で追加してください：")
            print("   1. Google Cloud Consoleでプロジェクトを開く")
            print("   2. APIとサービス → 認証情報")
            print("   3. OAuth 2.0 クライアントIDを編集")
            print("   4. スコープに https://www.googleapis.com/auth/forms.body を追加")
        return None, None, None
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return None, None, None

if __name__ == '__main__':
    print("="*60)
    print("かんぽ生命 専門家評価フォーム 自動作成")
    print("="*60)
    print()

    form_id, edit_url, response_url = create_evaluation_form()

    if form_id:
        # 結果をファイルに保存
        output_file = "output/kanpo_form_urls.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"フォームID: {form_id}\n")
            f.write(f"編集用URL: {edit_url}\n")
            f.write(f"回答用URL: {response_url}\n")

        print(f"💾 URLを保存しました: {output_file}")
