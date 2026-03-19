#!/usr/bin/env bash

set -e

BASE_URL="http://127.0.0.1:8000"

echo "---- Section Builder ----"

read -p "Document ID: " DOCUMENT_ID
read -p "Level names (comma separated e.g. book,chapter,paragraph): " LEVEL_NAMES
read -p "Collection Function ID: " COLLECTION_FUNCTION
read -p "Sectioning Function ID: " SECTIONING_FUNCTION
read -p "Subsectioning Function ID: " SUBSECTIONING_FUNCTION

# Convert comma-separated list to JSON array
LEVEL_NAMES_JSON=$(echo $LEVEL_NAMES | jq -R 'split(",")')

PAYLOAD=$(jq -n \
  --arg collection "$COLLECTION_FUNCTION" \
  --arg section "$SECTIONING_FUNCTION" \
  --arg subsection "$SUBSECTIONING_FUNCTION" \
  --argjson levels "$LEVEL_NAMES_JSON" \
'{
  strategy: {
    level_names: $levels,
    collection_function_id: $collection,
    sectioning_function_id: $section,
    subsectioning_function_id: $subsection,
    params: {}
  }
}')

echo
echo "Sending request..."
echo

curl -X POST "$BASE_URL/documents/$DOCUMENT_ID/sections/build" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD"

echo
echo "Done."