#!/bin/bash
# 朝のリマインドを launchd から動かせる場所へ配置する。
# launchd は ~/Documents を読めない（macOSのTCC保護）ため、実行体を外に置く。
# morning.py を編集したら、このスクリプトを再実行すること。
set -e
DEST="$HOME/Library/Application Support/ehon-cockpit"
mkdir -p "$DEST"
cp "$(dirname "$0")/cockpit/morning.py" "$DEST/morning.py"
echo "配置: $DEST/morning.py"
for L in inc.ehon.morning inc.ehon.morning.catchup; do
  launchctl bootout "gui/$(id -u)/$L" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/$L.plist"
done
echo "登録: inc.ehon.morning（毎日 8:00 / 15:00 / 20:00・曜日指定なし＝土日も動く）"
echo "登録: inc.ehon.morning.catchup（起動時。落ちていて送れなかった分を1通だけ送り直す）"
