#!/bin/bash

API_URL="http://127.0.0.1:8000/corpus/build"

echo "=== Corpus Builder ==="

# ---- Collect document slices ----
documents_json="["

while true; do
  read -p "Enter doc_id (or press ENTER to finish): " doc_id

  if [ -z "$doc_id" ]; then
    break
  fi

  read -p "Start char: " start_char
  read -p "End char: " end_char

  documents_json+=$(cat <<EOF
{
  "doc_id": "$doc_id",
  "start_char": $start_char,
  "end_char": $end_char
},
EOF
)

done

# Remove trailing comma safely
documents_json=$(echo "$documents_json" | sed '$ s/,$//')
documents_json+="]"

# ---- Processing strategy ----
echo ""
echo "=== Processing Strategy ==="

read -p "Strategy name (e.g. identity): " strategy_name
read -p "Strategy version (e.g. v1): " strategy_version

# ---- Persist flag ----
read -p "Persist corpus? (y/n): " persist_input

if [[ "$persist_input" == "y" || "$persist_input" == "Y" ]]; then
  persist=true
else
  persist=false
fi

# ---- Build final JSON ----
payload=$(cat <<EOF
{
  "documents": $documents_json,
  "processing_strategy": {
    "name": "$strategy_name",
    "version": "$strategy_version"
  },
  "persist": $persist
}
EOF
)

echo ""
echo "=== Sending Request ==="
echo "$payload" | jq .

# ---- Execute request ----
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "$payload"

echo ""
echo "=== Done ==="