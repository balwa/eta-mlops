#!/usr/bin/env bash
# One prediction from the running ETA service, without typing the long curl.
#   scripts/predict.sh                     # R0001, 3 items, rain
#   scripts/predict.sh R0042               # another restaurant
#   scripts/predict.sh R0042 5 clear       # restaurant, n_items, weather
#
# Prints the JSON the service returned and then the HTTP status code.
# The order time is fixed, so everyone in the room gets the same numbers.
set -euo pipefail
PORT="${PORT:-8000}"
R="${1:-R0001}"
N="${2:-3}"
W="${3:-rain}"
BODY="{\"order_id\":\"demo-$R\",\"restaurant_id\":\"$R\",\"n_items\":$N,\"weather\":\"$W\",\"placed_at\":\"2025-11-14T19:30:00+00:00\"}"

TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT
CODE=$(curl -s -o "$TMP" -w '%{http_code}' -X POST "localhost:$PORT/predict" \
  -H 'content-type: application/json' -d "$BODY" || true)
if [ "$CODE" = "000" ]; then
  echo "service is not running on :$PORT — start it with: make serve" >&2
  exit 1
fi
python3 -m json.tool "$TMP" 2>/dev/null || cat "$TMP"
echo "HTTP $CODE"
