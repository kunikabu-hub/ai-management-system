#!/bin/bash
cd "$(dirname "$0")"
python3 -u cockpit/server.py &
SERVER_PID=$!
sleep 2
open "http://127.0.0.1:8765"
echo ""
echo "  終わるときは、このウィンドウを閉じてください。"
echo ""
wait $SERVER_PID
