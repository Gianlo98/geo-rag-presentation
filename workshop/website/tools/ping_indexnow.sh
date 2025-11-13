#!/bin/bash
# Usage: ./tools/ping_indexnow.sh YOUR_KEY https://geo-italian.recipes/updated-url/
set -euo pipefail
KEY="$1"
URL="$2"
ENDPOINT="https://api.indexnow.org/indexnow"
JSON=$(cat <<EOF
{
  "host": "geo-italian.recipes",
  "key": "$KEY",
  "urlList": ["$URL"]
}
EOF
)
curl -s -X POST -H "Content-Type: application/json" -d "$JSON" "$ENDPOINT"
echo "\nPing submitted for $URL"
