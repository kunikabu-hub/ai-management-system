#!/bin/bash
# 朝のリマインドを launchd から動かせる場所へ配置する。
# launchd は ~/Documents を読めない（macOSのTCC保護）ため、実行体を外に置く。
# morning.py を編集したら、このスクリプトを再実行すること。
set -e
DEST="$HOME/Library/Application Support/ehon-cockpit"
mkdir -p "$DEST"
cp "$(dirname "$0")/cockpit/morning.py" "$DEST/morning.py"
echo "配置: $DEST/morning.py"
launchctl bootout "gui/$(id -u)/inc.ehon.morning" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/inc.ehon.morning.plist"
echo "登録: inc.ehon.morning（毎朝8:00）"
