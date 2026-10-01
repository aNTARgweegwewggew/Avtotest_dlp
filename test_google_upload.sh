#!/bin/bash

set -u

TOKEN_FILE="/home/user/mail-dlp-automation/google_drive_token.json"

FILE="/home/user/test_yandex/123.txt"

FOLDER_ID="1vMMfei1N_NLJ53Hc0MkGmSEpAuHrbXdL"

echo "========================================"
echo "Google Drive resumable upload test"
echo "========================================"
echo

# --------------------------------------------------
# Проверяем файлы
# --------------------------------------------------

if [ ! -f "$TOKEN_FILE" ]; then
    echo "ERROR: token file not found:"
    echo "$TOKEN_FILE"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo "ERROR: test file not found:"
    echo "$FILE"
    exit 1
fi

# --------------------------------------------------
# Получаем access token из google_drive_token.json
# --------------------------------------------------

GOOGLE_TOKEN=$(python3 -c "
import json

with open('$TOKEN_FILE') as f:
    data = json.load(f)

token = data.get('token')

if not token:
    raise SystemExit('token field not found')

print(token)
")

if [ -z "$GOOGLE_TOKEN" ]; then
    echo "ERROR: Google token is empty"
    exit 1
fi

echo "Token: loaded"
echo

# --------------------------------------------------
# Информация о файле
# --------------------------------------------------

FILE_NAME=$(basename "$FILE")
FILE_SIZE=$(stat -c%s "$FILE")

echo "File:"
echo "  $FILE_NAME"

echo "Size:"
echo "  $FILE_SIZE bytes"

echo "Folder:"
echo "  $FOLDER_ID"

echo

# --------------------------------------------------
# STEP 1
# Создание resumable upload session
# --------------------------------------------------

echo "========================================"
echo "STEP 1: CREATE UPLOAD SESSION"
echo "========================================"
echo

rm -f /tmp/google_headers.txt
rm -f /tmp/google_body.txt

curl -k -sS \
    -D /tmp/google_headers.txt \
    -o /tmp/google_body.txt \
    -X POST \
    "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable" \
    -H "Authorization: Bearer $GOOGLE_TOKEN" \
    -H "Content-Type: application/json; charset=UTF-8" \
    -H "X-Upload-Content-Type: application/octet-stream" \
    -H "X-Upload-Content-Length: $FILE_SIZE" \
    --data "{
        \"name\": \"$FILE_NAME\",
        \"parents\": [
            \"$FOLDER_ID\"
        ]
    }"

POST_RESULT=$?

echo
echo "--- GOOGLE RESPONSE HEADERS ---"
cat /tmp/google_headers.txt

echo
echo "--- GOOGLE RESPONSE BODY ---"
cat /tmp/google_body.txt

echo

if [ "$POST_RESULT" -ne 0 ]; then
    echo "ERROR: curl POST failed"
    exit 1
fi

# --------------------------------------------------
# Получаем Location
# --------------------------------------------------

UPLOAD_URL=$(
    grep -i '^location:' /tmp/google_headers.txt |
    sed 's/^[Ll]ocation:[[:space:]]*//' |
    tr -d '\r'
)

if [ -z "$UPLOAD_URL" ]; then
    echo "ERROR: Google did not return Location"
    exit 1
fi

echo "Upload session created."
echo

# --------------------------------------------------
# STEP 2
# Отправляем содержимое файла
# --------------------------------------------------

echo "========================================"
echo "STEP 2: UPLOAD FILE CONTENT"
echo "========================================"
echo

curl -k -i \
    -X PUT \
    "$UPLOAD_URL" \
    -H "Content-Type: application/octet-stream" \
    -H "Content-Length: $FILE_SIZE" \
    --data-binary "@$FILE"

PUT_RESULT=$?

echo
echo "========================================"

if [ "$PUT_RESULT" -eq 0 ]; then
    echo "UPLOAD REQUEST COMPLETED"
else
    echo "UPLOAD REQUEST FAILED"
fi

echo "========================================"
