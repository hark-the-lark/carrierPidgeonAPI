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

# Remove trailing comma
documents_json=$(echo "$documents_json" | sed '$ s/,$//')
documents_json+="]"

# ---- Processing strategy ----
echo ""
echo "=== Processing Strategy ==="

read -p "Strategy name (e.g. identity): " strategy_name
read -p "Strategy version (e.g. v1): " strategy_version
read -p "lowercase (true/false, optional): " lowercase
read -p "remove punctuation (true/false, optional): " remove_punctuation
read -p "special character regex (optional): " special_char_pattern
read -p "stopword set name (optional): " stopword_set
read -p "tokenizer name (optional): " tokenizer

# ---- Build processing_strategy dynamically ----
processing_json="{"

# required fields
processing_json+="\"name\": \"$strategy_name\","
processing_json+="\"version\": \"$strategy_version\""

# optional fields
if [ -n "$lowercase" ]; then
  processing_json+=", \"lowercase\": $lowercase"
fi

if [ -n "$remove_punctuation" ]; then
  processing_json+=", \"remove_punctuation\": $remove_punctuation"
fi

if [ -n "$special_char_pattern" ]; then
  processing_json+=", \"special_char_pattern\": \"$special_char_pattern\""
fi

if [ -n "$stopword_set" ]; then
  processing_json+=", \"stopword_set\": \"$stopword_set\""
fi

if [ -n "$tokenizer" ]; then
  processing_json+=", \"tokenizer\": \"$tokenizer\""
fi

processing_json+="}"

# ---- Persist flag ----
read -p "Persist corpus? (y/n): " persist_input

if [[ "$persist_input" == "y" || "$persist_input" == "Y" ]]; then
  persist=true
else
  persist=false
fi

# ---- Build final payload ----
payload=$(cat <<EOF
{
  "documents": $documents_json,
  "processing_strategy": $processing_json,
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