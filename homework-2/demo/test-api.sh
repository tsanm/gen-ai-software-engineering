#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Customer Support API — end-to-end curl smoke test.
#
# Exercises every endpoint (happy + error paths) and asserts the HTTP status
# code of each call. Exits non-zero if any check fails.
#
# Usage:
#   ./demo/test-api.sh                 # boots its own server on :8200, tests, stops it
#   BASE_URL=http://localhost:3000 ./demo/test-api.sh   # test an already-running server
#
# Run from the homework-2 directory (or anywhere — it cd's to the repo root).
# ---------------------------------------------------------------------------
set -uo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8200}"
BASE_URL="${BASE_URL:-}"
SAMPLES="samples"

# Colours (disabled when not a TTY).
if [ -t 1 ]; then
  GREEN=$'\033[32m'; RED=$'\033[31m'; BOLD=$'\033[1m'; DIM=$'\033[2m'; RESET=$'\033[0m'
else
  GREEN=''; RED=''; BOLD=''; DIM=''; RESET=''
fi

PASS=0
FAIL=0
SERVER_PID=""

cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Start a local server unless the caller pointed us at one.
if [ -z "$BASE_URL" ]; then
  BASE_URL="http://127.0.0.1:${PORT}"
  PY="./.venv/bin/python"
  [ -x "$PY" ] || PY="python3"
  echo "${DIM}Starting server on ${BASE_URL} ...${RESET}"
  "$PY" -m uvicorn src.main:app --host 127.0.0.1 --port "$PORT" >/tmp/hw2_test_api.log 2>&1 &
  SERVER_PID=$!
  # Wait for /health to come up (max ~15s).
  for _ in $(seq 1 30); do
    if curl -fs "${BASE_URL}/health" >/dev/null 2>&1; then break; fi
    sleep 0.5
  done
fi

echo "${BOLD}Testing API at ${BASE_URL}${RESET}"
echo

# check <name> <expected_status> <curl args...>
# Runs curl, prints the body, and asserts the HTTP status code.
# Captures the response body into the global $BODY for follow-up extraction.
check() {
  local name="$1" expected="$2"; shift 2
  local raw status
  raw="$(curl -s -w $'\n%{http_code}' "$@")"
  status="${raw##*$'\n'}"
  BODY="${raw%$'\n'*}"
  if [ "$status" = "$expected" ]; then
    printf '%s  %-46s %s(%s)%s\n' "${GREEN}✔${RESET}" "$name" "$DIM" "$status" "$RESET"
    PASS=$((PASS + 1))
  else
    printf '%s  %-46s %sexpected %s, got %s%s\n' "${RED}✘${RESET}" "$name" "$RED" "$expected" "$status" "$RESET"
    printf '     %s%s%s\n' "$DIM" "${BODY}" "$RESET"
    FAIL=$((FAIL + 1))
  fi
}

# Extract a top-level JSON string field from $BODY (no jq dependency).
json_field() {
  printf '%s' "$BODY" | grep -oE "\"$1\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | head -1 | sed -E 's/.*:[[:space:]]*"([^"]*)"/\1/'
}

CREATE_PAYLOAD='{
  "customer_id": "CUST-1",
  "customer_email": "jane@example.com",
  "customer_name": "Jane Doe",
  "subject": "Cannot log in",
  "description": "I cannot access my account after the latest update. This is critical.",
  "metadata": { "source": "web_form", "browser": "Chrome", "device_type": "desktop" }
}'

echo "${BOLD}-- Health & CRUD --${RESET}"
check "GET  /health"                          200 "${BASE_URL}/health"

check "POST /tickets (create)"                201 -X POST "${BASE_URL}/tickets" \
  -H 'Content-Type: application/json' -d "$CREATE_PAYLOAD"
TICKET_ID="$(json_field id)"
echo "     ${DIM}created id=${TICKET_ID}${RESET}"

check "POST /tickets?auto_classify=true"      201 -X POST "${BASE_URL}/tickets?auto_classify=true" \
  -H 'Content-Type: application/json' -d '{
    "customer_id":"CUST-2","customer_email":"bob@example.com","customer_name":"Bob Jones",
    "subject":"App crashes on upload",
    "description":"The app crashes with an error every time I upload a file. Production down.",
    "metadata":{"source":"chat","device_type":"mobile"}}'

check "POST /tickets (validation error)"      400 -X POST "${BASE_URL}/tickets" \
  -H 'Content-Type: application/json' -d '{
    "customer_id":"CUST-3","customer_email":"not-an-email","customer_name":"X",
    "subject":"Hi","description":"short","metadata":{"source":"web_form","device_type":"desktop"}}'

check "GET  /tickets (list all)"              200 "${BASE_URL}/tickets"
check "GET  /tickets/{id}"                    200 "${BASE_URL}/tickets/${TICKET_ID}"
check "GET  /tickets/{missing} -> 404"        404 "${BASE_URL}/tickets/does-not-exist"

check "PUT  /tickets/{id} (resolve)"          200 -X PUT "${BASE_URL}/tickets/${TICKET_ID}" \
  -H 'Content-Type: application/json' -d '{"status":"resolved","assigned_to":"agent-7"}'

check "POST /tickets/{id}/auto-classify"      200 -X POST "${BASE_URL}/tickets/${TICKET_ID}/auto-classify"
check "POST /tickets/{missing}/auto-classify" 404 -X POST "${BASE_URL}/tickets/nope/auto-classify"

echo
echo "${BOLD}-- Filtering --${RESET}"
check "GET  /tickets?category=technical_issue" 200 "${BASE_URL}/tickets?category=technical_issue"
check "GET  /tickets?category=..&priority=.."  200 "${BASE_URL}/tickets?category=billing_question&priority=high"

echo
echo "${BOLD}-- Bulk import --${RESET}"
check "POST /tickets/import (CSV)"            200 -X POST "${BASE_URL}/tickets/import?auto_classify=true" \
  -F "file=@${SAMPLES}/sample_tickets.csv"
check "POST /tickets/import (JSON)"           200 -X POST "${BASE_URL}/tickets/import" \
  -F "file=@${SAMPLES}/sample_tickets.json"
check "POST /tickets/import (XML)"            200 -X POST "${BASE_URL}/tickets/import" \
  -F "file=@${SAMPLES}/sample_tickets.xml"
check "POST /tickets/import (invalid rows)"   200 -X POST "${BASE_URL}/tickets/import" \
  -F "file=@${SAMPLES}/invalid_tickets.csv"
echo "     ${DIM}${BODY}${RESET}"
check "POST /tickets/import (unknown format)" 400 -X POST "${BASE_URL}/tickets/import" \
  -F "file=@requirements.txt"

echo
echo "${BOLD}-- Delete --${RESET}"
check "DELETE /tickets/{id}"                  204 -X DELETE "${BASE_URL}/tickets/${TICKET_ID}"
check "GET    /tickets/{deleted} -> 404"      404 "${BASE_URL}/tickets/${TICKET_ID}"
check "DELETE /tickets/{missing} -> 404"      404 -X DELETE "${BASE_URL}/tickets/does-not-exist"

echo
echo "${BOLD}Result:${RESET} ${GREEN}${PASS} passed${RESET}, $([ "$FAIL" -gt 0 ] && printf '%s' "${RED}${FAIL} failed${RESET}" || printf '%s' "${FAIL} failed")"
[ "$FAIL" -eq 0 ]
