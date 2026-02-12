#!/usr/bin/env python3
"""
Google Calendarから今日の予定を取得するスクリプト
"""

import os
import json
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# 認証情報のパス
TOKEN_PATH = os.path.expanduser('~/.config/claude-code/gdrive/token.json')
CREDENTIALS_PATH = os.path.expanduser('~/.config/claude-code/gdrive/credentials.json')

# 必要なスコープ
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/calendar.readonly'
]

def get_credentials():
    """認証情報を取得"""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # トークンが無効または期限切れの場合、リフレッシュ
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        # トークンを保存
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return creds

def get_today_events():
    """今日の予定を取得"""
    try:
        creds = get_credentials()

        if not creds or not creds.valid:
            print("ERROR: 認証情報が無効です。Google Calendar APIのスコープを追加して、トークンを再取得してください。")
            print("実行: python3 tools/get_google_drive_token.py")
            return None

        # Calendar APIクライアントを構築
        service = build('calendar', 'v3', credentials=creds)

        # 今日の0時から23時59分までの範囲を設定
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # イベントを取得
        events_result = service.events().list(
            calendarId='primary',
            timeMin=today_start.isoformat() + 'Z',
            timeMax=today_end.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        if not events:
            print(f'今日（{today_start.strftime("%Y-%m-%d")}）の予定はありません。')
            return []

        print(f'今日の予定 ({today_start.strftime("%Y-%m-%d")}):')
        result = []

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            summary = event.get('summary', '(タイトルなし)')
            location = event.get('location', '')

            # 時刻のフォーマット
            if 'T' in start:  # dateTimeの場合
                start_time = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%H:%M')
                end_time = datetime.fromisoformat(end.replace('Z', '+00:00')).strftime('%H:%M')
                time_str = f"{start_time}-{end_time}"
            else:  # 終日イベントの場合
                time_str = "終日"

            event_info = {
                'time': time_str,
                'summary': summary,
                'location': location,
                'start': start,
                'end': end
            }

            result.append(event_info)

            location_str = f" ({location})" if location else ""
            print(f"- {time_str}: {summary}{location_str}")

        return result

    except Exception as e:
        if 'invalid_scope' in str(e) or 'calendar' in str(e).lower():
            print("ERROR: Google Calendar APIのスコープが設定されていません。")
            print("以下の手順で設定してください：")
            print("1. tools/get_google_drive_token.py を編集し、SCOPESにcalendar.readonlyを追加")
            print("2. python3 tools/get_google_drive_token.py を実行してトークンを再取得")
            return None
        else:
            print(f"ERROR: {str(e)}")
            return None

if __name__ == '__main__':
    get_today_events()
