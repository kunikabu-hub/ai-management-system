#!/usr/bin/env python3
"""
Google Calendar API 動作確認スクリプト

使用方法:
python3 tools/test_calendar.py
"""

import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# トークンファイルのパス
TOKEN_FILE = os.path.expanduser('~/.config/claude-code/gdrive/token.json')

def test_calendar_api():
    """Google Calendar APIの動作確認"""

    print("=" * 60)
    print("Google Calendar API 動作確認")
    print("=" * 60)

    # トークンファイルの存在確認
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ エラー: トークンファイルが見つかりません")
        print(f"   パス: {TOKEN_FILE}")
        return False

    try:
        # 認証情報を読み込み
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)

        creds = Credentials.from_authorized_user_info(token_data)

        # Google Calendar APIサービスを構築
        print("\n✅ 認証情報を読み込みました")
        print("✅ Google Calendar APIに接続中...\n")

        service = build('calendar', 'v3', credentials=creds)

        # 今日の日付
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        # 今日の予定を取得
        print(f"📅 今日の予定を取得中... ({today.strftime('%Y-%m-%d')})")
        print("-" * 60)

        events_result = service.events().list(
            calendarId='primary',
            timeMin=today.isoformat() + 'Z',
            timeMax=tomorrow.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            print('今日の予定はありません。')
        else:
            print(f'✅ 取得件数: {len(events)} 件\n')
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                summary = event.get('summary', '(タイトルなし)')

                # 時刻の表示を整形
                try:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    time_str = f"{start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}"
                except:
                    time_str = "終日"

                print(f"  {time_str}: {summary}")

                # 場所があれば表示
                if 'location' in event:
                    print(f"    📍 {event['location']}")

                # 説明があれば表示（最初の50文字のみ）
                if 'description' in event:
                    desc = event['description'][:50]
                    if len(event['description']) > 50:
                        desc += '...'
                    print(f"    📝 {desc}")

                print()

        print("-" * 60)
        print("\n✅ Google Calendar API の動作確認が完了しました")
        print("✅ /daily-schedule スキルが使用可能です\n")

        return True

    except HttpError as error:
        print(f'❌ APIエラーが発生しました: {error}')
        return False
    except Exception as e:
        print(f'❌ エラーが発生しました: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_calendar_api()

    if success:
        print("=" * 60)
        print("🎉 セットアップ完了！")
        print("=" * 60)
        print("\n次のコマンドで日次スケジュールを生成できます:")
        print("  /daily-schedule\n")
    else:
        print("\n❌ セットアップに失敗しました")
        print("   エラーメッセージを確認してください\n")
