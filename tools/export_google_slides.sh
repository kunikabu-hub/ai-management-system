#!/bin/bash
# Google Slidesをテキスト形式でエクスポートするスクリプト

TOKEN=$(cat ~/.config/claude-code/gdrive/token.json | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")

if [ -z "$1" ]; then
  echo "使用方法: $0 <file_id> [output_name]"
  exit 1
fi

FILE_ID=$1
OUTPUT_NAME=${2:-"slide_export"}

echo "================================================================================"
echo "Google Slides エクスポート"
echo "================================================================================"
echo "ファイルID: $FILE_ID"
echo ""

# まずファイル情報を取得
echo "ファイル情報を取得中..."
FILE_INFO=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID?fields=id,name,mimeType")

FILE_NAME=$(echo "$FILE_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('name', 'Unknown'))" 2>/dev/null)
MIME_TYPE=$(echo "$FILE_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('mimeType', 'Unknown'))" 2>/dev/null)

if [ "$MIME_TYPE" == "Unknown" ]; then
  echo "❌ エラー: ファイルが見つからないか、アクセス権限がありません"
  echo "$FILE_INFO"
  exit 1
fi

echo "ファイル名: $FILE_NAME"
echo "タイプ: $MIME_TYPE"
echo ""

# 出力ディレクトリを作成
mkdir -p output/slides

# テキスト形式でエクスポート
echo "テキスト形式でエクスポート中..."
OUTPUT_FILE="output/slides/${OUTPUT_NAME}.txt"

curl -s -H "Authorization: Bearer $TOKEN" \
  "https://www.googleapis.com/drive/v3/files/$FILE_ID/export?mimeType=text/plain" \
  -o "$OUTPUT_FILE"

if [ $? -eq 0 ] && [ -s "$OUTPUT_FILE" ]; then
  echo "✅ エクスポート成功: $OUTPUT_FILE"
  echo ""
  echo "--- ファイルの先頭部分 ---"
  head -50 "$OUTPUT_FILE"
  echo ""
  echo "--- ファイルの先頭部分（終わり） ---"
  echo ""
  echo "ファイルサイズ: $(wc -c < "$OUTPUT_FILE") バイト"
  echo "行数: $(wc -l < "$OUTPUT_FILE") 行"
else
  echo "❌ エクスポート失敗"
  exit 1
fi

echo ""
echo "================================================================================"
echo "✅ 完了"
echo "================================================================================"
