#!/usr/bin/env python3
"""
GitHub Helper
Issue管理、プロジェクト追跡、リポジトリ情報取得
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API_URL = 'https://api.github.com'


def call_github_api(endpoint, method='GET', data=None):
    """GitHub APIを呼び出す"""
    if not GITHUB_TOKEN:
        print("Error: GITHUB_TOKEN not found in environment variables")
        sys.exit(1)

    url = f"{GITHUB_API_URL}/{endpoint}"
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)

        response.raise_for_status()
        return response.json() if response.content else {}

    except requests.exceptions.RequestException as e:
        print(f"Error calling GitHub API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)


def list_issues(repo, state='open', labels=None, assignee=None):
    """Issueの一覧を取得"""
    params = []
    if state:
        params.append(f"state={state}")
    if labels:
        params.append(f"labels={labels}")
    if assignee:
        params.append(f"assignee={assignee}")

    query = '&'.join(params)
    endpoint = f"repos/{repo}/issues"
    if query:
        endpoint += f"?{query}"

    issues = call_github_api(endpoint)

    print(f"\n📋 Issues in {repo} (state: {state})\n")
    for issue in issues:
        labels_str = ', '.join([label['name'] for label in issue.get('labels', [])])
        print(f"#{issue['number']}: {issue['title']}")
        print(f"  State: {issue['state']} | Labels: {labels_str}")
        print(f"  URL: {issue['html_url']}\n")

    return issues


def create_issue(repo, title, body='', labels=None, assignees=None):
    """新しいIssueを作成"""
    data = {
        'title': title,
        'body': body
    }

    if labels:
        data['labels'] = labels if isinstance(labels, list) else [labels]

    if assignees:
        data['assignees'] = assignees if isinstance(assignees, list) else [assignees]

    issue = call_github_api(f"repos/{repo}/issues", method='POST', data=data)

    print(f"\n✅ Issue作成完了:")
    print(f"  #{issue['number']}: {issue['title']}")
    print(f"  URL: {issue['html_url']}\n")

    return issue


def update_issue(repo, issue_number, title=None, body=None, state=None, labels=None):
    """既存のIssueを更新"""
    data = {}

    if title:
        data['title'] = title
    if body:
        data['body'] = body
    if state:
        data['state'] = state
    if labels:
        data['labels'] = labels if isinstance(labels, list) else [labels]

    issue = call_github_api(f"repos/{repo}/issues/{issue_number}", method='PATCH', data=data)

    print(f"\n✅ Issue更新完了:")
    print(f"  #{issue['number']}: {issue['title']}")
    print(f"  State: {issue['state']}")
    print(f"  URL: {issue['html_url']}\n")

    return issue


def add_comment(repo, issue_number, comment):
    """Issueにコメントを追加"""
    data = {'body': comment}

    result = call_github_api(
        f"repos/{repo}/issues/{issue_number}/comments",
        method='POST',
        data=data
    )

    print(f"\n✅ コメント追加完了:")
    print(f"  Issue: #{issue_number}")
    print(f"  Comment URL: {result['html_url']}\n")

    return result


def get_user_info():
    """認証ユーザーの情報を取得"""
    user = call_github_api("user")

    print(f"\n👤 GitHub User Info:")
    print(f"  Username: {user['login']}")
    print(f"  Name: {user.get('name', 'N/A')}")
    print(f"  Email: {user.get('email', 'N/A')}")
    print(f"  Public Repos: {user['public_repos']}")
    print(f"  Profile: {user['html_url']}\n")

    return user


def list_repositories(org=None):
    """リポジトリ一覧を取得"""
    if org:
        endpoint = f"orgs/{org}/repos"
    else:
        endpoint = "user/repos"

    repos = call_github_api(endpoint)

    print(f"\n📦 Repositories ({len(repos)}):\n")
    for repo in repos:
        print(f"{repo['full_name']}")
        print(f"  {repo.get('description', 'No description')}")
        print(f"  ⭐ {repo['stargazers_count']} | 🍴 {repo['forks_count']}")
        print(f"  {repo['html_url']}\n")

    return repos


def search_issues(query, repo=None):
    """Issueを検索"""
    if repo:
        query = f"{query} repo:{repo}"

    endpoint = f"search/issues?q={query}"
    result = call_github_api(endpoint)

    issues = result.get('items', [])

    print(f"\n🔍 Search Results: {result.get('total_count', 0)} issues\n")
    for issue in issues[:10]:  # 最初の10件を表示
        print(f"#{issue['number']}: {issue['title']}")
        print(f"  Repo: {issue['repository_url'].split('/')[-2:]}")
        print(f"  State: {issue['state']}")
        print(f"  URL: {issue['html_url']}\n")

    return issues


def export_issues_to_file(repo, output_file=None):
    """Issueをファイルにエクスポート"""
    issues = call_github_api(f"repos/{repo}/issues?state=all")

    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(__file__).parent.parent / 'output' / 'github'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f'issues_{timestamp}.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(issues, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Issueをエクスポート: {output_file}")
    print(f"   総数: {len(issues)} issues\n")

    return output_file


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python github_helper.py user                           # ユーザー情報")
        print("  python github_helper.py repos [org]                    # リポジトリ一覧")
        print("  python github_helper.py list <owner/repo>              # Issue一覧")
        print("  python github_helper.py create <owner/repo> <title>    # Issue作成")
        print("  python github_helper.py update <owner/repo> <number>   # Issue更新")
        print("  python github_helper.py comment <owner/repo> <number>  # コメント追加")
        print("  python github_helper.py search <query>                 # Issue検索")
        print("  python github_helper.py export <owner/repo>            # Issueエクスポート")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'user':
        get_user_info()

    elif command == 'repos':
        org = sys.argv[2] if len(sys.argv) > 2 else None
        list_repositories(org)

    elif command == 'list' and len(sys.argv) > 2:
        repo = sys.argv[2]
        list_issues(repo)

    elif command == 'create' and len(sys.argv) > 3:
        repo = sys.argv[2]
        title = sys.argv[3]
        body = sys.argv[4] if len(sys.argv) > 4 else ''
        create_issue(repo, title, body)

    elif command == 'update' and len(sys.argv) > 3:
        repo = sys.argv[2]
        issue_number = sys.argv[3]
        # 簡易的な例（実際にはもっと詳細なオプションを追加可能）
        update_issue(repo, issue_number, state='closed')

    elif command == 'comment' and len(sys.argv) > 4:
        repo = sys.argv[2]
        issue_number = sys.argv[3]
        comment = sys.argv[4]
        add_comment(repo, issue_number, comment)

    elif command == 'search' and len(sys.argv) > 2:
        query = ' '.join(sys.argv[2:])
        search_issues(query)

    elif command == 'export' and len(sys.argv) > 2:
        repo = sys.argv[2]
        export_issues_to_file(repo)

    else:
        print("Invalid command or missing arguments")
        sys.exit(1)
