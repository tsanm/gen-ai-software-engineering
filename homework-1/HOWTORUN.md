# ▶️ How to Run the Application

Banking Transactions API — Python 3.10+ / FastAPI. All commands are run from the
`homework-1/` directory.

---

## 1. Prerequisites

- **Python 3.10 or newer** (`python3 --version`)
- macOS / Linux / WSL (a Bash shell for `demo/run.sh`)

---

## 2. Quick start (one command)

```bash
cd homework-1
./demo/run.sh
```

This creates a virtual environment, installs dependencies, and starts the API on
**http://localhost:3000**. Set a different port with `PORT=8080 ./demo/run.sh`.

---

## 3. Manual setup

```bash
cd homework-1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 3000
```

Once running:
- **API base**: http://localhost:3000
- **Interactive docs (Swagger)**: http://localhost:3000/docs
- **Health check**: http://localhost:3000/health

---

## 4. 🔐 Environment configuration (optional)

All settings have sensible defaults; override via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3000` | Port (used by `demo/run.sh`) |
| `REGION` | `DEFAULT` | Active region (`DEFAULT`, `US`, `EU`, `JP`) |
| `RATE_LIMIT_MAX` | `100` | Max requests per window per IP |
| `RATE_LIMIT_WINDOW` | `60` | Rate-limit window in seconds |
| `LARGE_AMOUNT_THRESHOLD` | `10000` | Amount that triggers a compliance flag |
| `LOG_LEVEL` | `INFO` | Logging level |

Example:

```bash
RATE_LIMIT_MAX=5 REGION=JP uvicorn src.main:app --port 3000
```

---

## 5. 🧪 Running the tests

```bash
cd homework-1
source .venv/bin/activate     # if not already active
pytest                        # 28 tests
pytest -v                     # verbose, per-test names
```

Expected: **28 passed**.

---

## 6. Try it out

Sample requests are in [`demo/sample-requests.http`](./demo/sample-requests.http)
(VS Code REST Client) or use curl:

```bash
# Create a transfer
curl -X POST http://localhost:3000/transactions \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-67890","amount":100.50,"currency":"USD","type":"transfer"}'

# List / filter
curl http://localhost:3000/transactions
curl "http://localhost:3000/transactions?accountId=ACC-12345&type=transfer"

# Balance, summary, interest
curl http://localhost:3000/accounts/ACC-12345/balance
curl http://localhost:3000/accounts/ACC-12345/summary
curl "http://localhost:3000/accounts/ACC-12345/interest?rate=0.05&days=30"

# CSV export
curl "http://localhost:3000/transactions/export?format=csv"
```

Sample seed data is available in [`demo/sample-data.json`](./demo/sample-data.json).
