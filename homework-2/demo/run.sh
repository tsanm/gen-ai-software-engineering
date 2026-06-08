#!/usr/bin/env bash
# Start the API locally on http://localhost:3000 (Swagger UI at /docs).
# Usage: ./demo/run.sh   (run from the homework-2 directory)
set -euo pipefail
cd "$(dirname "$0")/.."

PY="./.venv/bin/python"
[ -d ".venv" ] || python3 -m venv .venv
$PY -m pip install --quiet -r requirements.txt

echo "▶ Customer Support API on http://localhost:3000  (docs: /docs)"
exec $PY -m uvicorn src.main:app --host 0.0.0.0 --port 3000
