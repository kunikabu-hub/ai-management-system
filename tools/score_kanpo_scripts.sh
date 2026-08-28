#!/bin/bash
# かんぽ脚本AI自動採点システム - 実行スクリプト

echo "=========================================="
echo "かんぽ脚本AI自動採点システム"
echo "=========================================="
echo ""

# ANTHROPIC_API_KEYの確認
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ エラー: ANTHROPIC_API_KEY が設定されていません"
    echo ""
    echo "以下のコマンドで設定してください:"
    echo "  export ANTHROPIC_API_KEY='your-api-key'"
    echo ""
    exit 1
fi

# スクリプトのディレクトリに移動
cd "$(dirname "$0")/.."

# Pythonスクリプトを実行
python3 << 'PYTHON_SCRIPT'
import sys
import os

# カレントディレクトリをPythonパスに追加
sys.path.insert(0, os.getcwd())

from tools.auto_score_scripts import main

# 脚本ファイルのパスを設定
# TODO: 実際のファイルパスに置き換えてください
script_files = [
    ('19-6_提出版', 'path/to/生成プロット_CX通信19_6_提出版.txt'),
    ('19-7_提出版', 'path/to/生成プロット_CX通信19_7_提出版.txt'),
    ('19-15_提出版', 'path/to/生成プロット_CX通信19_15_提出版.txt'),
]

print("\n📝 採点対象:")
for name, path in script_files:
    print(f"  - {name}")
print()

# 実行
main(script_files)

PYTHON_SCRIPT

echo ""
echo "✅ 完了"
