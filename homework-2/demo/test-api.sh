#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Customer Support API — curl walkthrough of every endpoint.
#
# For each call it prints:
#   1. the exact, copy-pasteable curl command  (the REQUEST — method/url/headers/body)
#   2. the full RESPONSE  (status line + headers via -i, then the JSON body, pretty-printed)
#
# Usage:
#   ./demo/test-api.sh                 # boots its own server on :8200, walks through, stops it
#   BASE_URL=http://localhost:3000 ./demo/test-api.sh   # hit an already-running server
#
# Run from anywhere — it cd's to the homework-2 directory.
# ---------------------------------------------------------------------------
set -uo pipefail
cd "$(dirname "$0")/.."

PORT="${PORT:-8200}"
BASE_URL="${BASE_URL:-}"
SAMPLES="samples"

if [ -t 1 ]; then
  CYAN=$'\033[36m'; BOLD=$'\033[1m'; DIM=$'\033[2m'; YELLOW=$'\033[33m'; RESET=$'\033[0m'
else
  CYAN=''; BOLD=''; DIM=''; YELLOW=''; RESET=''
fi

PY="./.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3 || true)"

SERVER_PID=""
cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# Boot a throwaway server unless the caller pointed us at one.
if [ -z "$BASE_URL" ]; then
  BASE_URL="http://127.0.0.1:${PORT}"
  echo "${DIM}# starting throwaway server on ${BASE_URL} ...${RESET}"
  "$PY" -m uvicorn src.main:app --host 127.0.0.1 --port "$PORT" >/tmp/hw2_test_api.log 2>&1 &
  SERVER_PID=$!
  for _ in $(seq 1 30); do
    curl -fs "${BASE_URL}/health" >/dev/null 2>&1 && break
    sleep 0.5
  done
fi

# Single-quote an argument for display if it contains anything shell-special,
# so the printed command line is genuinely copy-pasteable.
qq() {
  case "$1" in
    ''|*[!A-Za-z0-9_./:=@-]*)
      printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")" ;;
    *) printf '%s' "$1" ;;
  esac
}

# req <description> <curl-args...>
# Prints the curl command, then runs `curl -i` and renders the full response.
req() {
  local desc="$1"; shift
  printf '\n%s───────────────────────────────────────────────────────────────%s\n' "$DIM" "$RESET"
  printf '%s# %s%s\n' "$BOLD" "$desc" "$RESET"

  # 1) the request, as a runnable command
  printf '%s$ curl -i%s' "$CYAN" "$RESET"
  local a
  for a in "$@"; do printf ' %s' "$(qq "$a")"; done
  printf '\n\n'

  # 2) the response: status line + headers + (pretty) body
  printf '%s' "${YELLOW}"
  curl -sS -i "$@" | "$PY" -c '
import sys, json, re
raw = sys.stdin.buffer.read().decode("utf-8", "replace")
parts = re.split(r"\r?\n\r?\n", raw, maxsplit=1)
head = parts[0].strip()
body = (parts[1] if len(parts) > 1 else "").strip()
print(head)
if body:
    print()
    try:
        print(json.dumps(json.loads(body), indent=2))
    except Exception:
        print(body)
' 2>/dev/null || true
  printf '%s\n' "${RESET}"
}

# Pull a top-level JSON string field out of a fresh GET (no jq dependency).
field_from() { curl -s "$1" | "$PY" -c "import sys,json;print(json.load(sys.stdin).get('$2',''))" 2>/dev/null; }

echo "${BOLD}Customer Support API — curl walkthrough @ ${BASE_URL}${RESET}"

req "Health check" \
  "${BASE_URL}/health"

req "Create a ticket" \
  -X POST "${BASE_URL}/tickets" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUST-1","customer_email":"jane@example.com","customer_name":"Jane Doe","subject":"Cannot log in","description":"I cannot access my account after the latest update. This is critical.","metadata":{"source":"web_form","browser":"Chrome","device_type":"desktop"}}'

# Grab the id of the ticket we just created for the by-id calls below.
TICKET_ID="$(curl -s -X POST "${BASE_URL}/tickets" \
  -H 'Content-Type: application/json' \
  -d '{"customer_id":"CUST-ID","customer_email":"id@example.com","customer_name":"Id Holder","subject":"Placeholder for id","description":"This ticket exists so the script has a real id to fetch.","metadata":{"source":"api","device_type":"desktop"}}' \
  | "$PY" -c "import sys,json;print(json.load(sys.stdin)['id'])" 2>/dev/null)"

req "Create with auto-classification (?auto_classify=true)" \
  -X POST "${BASE_URL}/tickets?auto_classify=true" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUST-2","customer_email":"bob@example.com","customer_name":"Bob Jones","subject":"App crashes on upload","description":"The app crashes with an error every time I upload a file. Production down.","metadata":{"source":"chat","device_type":"mobile"}}'

req "Create — validation error (bad email, short description) -> 400" \
  -X POST "${BASE_URL}/tickets" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"CUST-3","customer_email":"not-an-email","customer_name":"X","subject":"Hi","description":"short","metadata":{"source":"web_form","device_type":"desktop"}}'

req "List all tickets" \
  "${BASE_URL}/tickets"

req "List filtered by category + priority" \
  "${BASE_URL}/tickets?category=billing_question&priority=high"

req "Get one ticket by id" \
  "${BASE_URL}/tickets/${TICKET_ID}"

req "Get a missing ticket -> 404" \
  "${BASE_URL}/tickets/does-not-exist"

req "Update a ticket (partial) -> resolve" \
  -X PUT "${BASE_URL}/tickets/${TICKET_ID}" \
  -H "Content-Type: application/json" \
  -d '{"status":"resolved","assigned_to":"agent-7"}'

req "Auto-classify an existing ticket" \
  -X POST "${BASE_URL}/tickets/${TICKET_ID}/auto-classify"

req "Bulk import CSV (?auto_classify=true)" \
  -X POST "${BASE_URL}/tickets/import?auto_classify=true" \
  -F "file=@${SAMPLES}/sample_tickets.csv"

req "Bulk import JSON" \
  -X POST "${BASE_URL}/tickets/import" \
  -F "file=@${SAMPLES}/sample_tickets.json"

req "Bulk import XML" \
  -X POST "${BASE_URL}/tickets/import" \
  -F "file=@${SAMPLES}/sample_tickets.xml"

req "Bulk import with invalid rows (per-row error report)" \
  -X POST "${BASE_URL}/tickets/import" \
  -F "file=@${SAMPLES}/invalid_tickets.csv"

req "Bulk import — unsupported format -> 400" \
  -X POST "${BASE_URL}/tickets/import" \
  -F "file=@requirements.txt"

req "Delete a ticket -> 204 (no body)" \
  -X DELETE "${BASE_URL}/tickets/${TICKET_ID}"

req "Get the deleted ticket -> 404" \
  "${BASE_URL}/tickets/${TICKET_ID}"

printf '\n%sDone — every endpoint exercised above with its raw request and response.%s\n' "$BOLD" "$RESET"
