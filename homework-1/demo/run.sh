#!/usr/bin/env bash
# Start the Banking Transactions API locally.
# Usage: ./demo/run.sh   (run from the homework-1 directory)
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

echo "Installing dependencies..."
./.venv/bin/python -m pip install --quiet --upgrade pip
./.venv/bin/python -m pip install --quiet -r requirements.txt

PORT="${PORT:-3000}"
echo "Starting API on http://localhost:${PORT}  (docs at /docs)"
exec ./.venv/bin/python -m uvicorn src.main:app --host 0.0.0.0 --port "${PORT}"
