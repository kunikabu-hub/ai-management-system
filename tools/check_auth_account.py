#!/usr/bin/env python3
"""
現在認証されているGoogleアカウント情報を確認
"""
import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_FILE = os.path.expanduser('~/.config/claude-code/gdrive/token.json')

with open(TOKEN_FILE, 'r') as f:
    token_data = json.load(f)

creds = Credentials.from_authorized_user_info(token_data)

if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())

service = build('drive', 'v3', credentials=creds)

# ユーザー情報を取得
about = service.about().get(fields="user").execute()
user = about.get('user', {})

print("=" * 80)
print("認証されているGoogleアカウント")
print("=" * 80)
print(f"表示名: {user.get('displayName')}")
print(f"メールアドレス: {user.get('emailAddress')}")
print(f"写真URL: {user.get('photoLink', 'N/A')}")
print("=" * 80)
