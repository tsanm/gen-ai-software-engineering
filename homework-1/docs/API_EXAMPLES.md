# 📡 API Examples — Banking Transactions API

Real `curl` request → response pairs captured against a running instance
(`./demo/run.sh`, base URL `http://localhost:3000`). Interactive docs: `/docs` (Swagger).

> Each example: a one-line summary, the exact `curl`, and the live response with its HTTP status.

---

## Health & discovery

### Health check

Liveness probe; reports the active region.

```bash
curl "http://localhost:3000/health"
```

**Response** `200`
```json
{
    "status": "ok",
    "region": "DEFAULT"
}
```

---

## Task 1 — Core API

### Create a transfer

Creates a transaction; server assigns `id`, `timestamp`, and `status=completed` (HTTP 201).

```bash
curl -X POST "http://localhost:3000/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"ACC-12345","toAccount":"ACC-67890","amount":100.50,"currency":"USD","type":"transfer"}'
```

**Response** `201`
```json
{
    "id": "5bc0960b-ef7f-4174-af70-4994a340f0a8",
    "fromAccount": "ACC-12345",
    "toAccount": "ACC-67890",
    "amount": 100.5,
    "currency": "USD",
    "type": "transfer",
    "timestamp": "2026-06-07T11:21:03.609105Z",
    "status": "completed"
}
```

### List all transactions

Returns every stored transaction.

```bash
curl "http://localhost:3000/transactions"
```

**Response** `200`
```json
[
    {
        "id": "a994bd9f-8539-45a5-b375-cd871772b149",
        "fromAccount": null,
        "toAccount": "ACC-12345",
        "amount": 1000.0,
        "currency": "USD",
        "type": "deposit",
        "timestamp": "2026-06-07T11:21:03.459549Z",
        "status": "completed"
    },
    {
        "id": "fa673fce-37c5-4542-8935-1cbd799729b6",
        "fromAccount": "ACC-12345",
        "toAccount": null,
        "amount": 150.25,
        "currency": "USD",
        "type": "withdrawal",
        "timestamp": "2026-06-07T11:21:03.476572Z",
        "status": "completed"
    },
    {
        "id": "8b0d8503-a9ca-4142-838f-c864bd3b8e6c",
        "fromAccount": "ACC-12345",
        "toAccount": "ACC-67890",
        "amount": 100.5,
        "currency": "USD",
        "type": "transfer",
        "timestamp": "2026-06-07T11:21:03.493559Z",
        "status": "completed"
    },
    {
        "id": "5bc0960b-ef7f-4174-af70-4994a340f0a8",
        "fromAccount": "ACC-12345",
        "toAccount": "ACC-67890",
        "amount": 100.5,
        "currency": "USD",
        "type": "transfer",
        "timestamp": "2026-06-07T11:21:03.609105Z",
        "status": "completed"
    }
]
```

### Get one transaction by id

Fetch a single transaction (404 if unknown).

```bash
curl "http://localhost:3000/transactions/8b0d8503-a9ca-4142-838f-c864bd3b8e6c"
```

**Response** `200`
```json
{
    "id": "8b0d8503-a9ca-4142-838f-c864bd3b8e6c",
    "fromAccount": "ACC-12345",
    "toAccount": "ACC-67890",
    "amount": 100.5,
    "currency": "USD",
    "type": "transfer",
    "timestamp": "2026-06-07T11:21:03.493559Z",
    "status": "completed"
}
```

### Account balance

Net balance derived from completed transactions.

```bash
curl "http://localhost:3000/accounts/ACC-12345/balance"
```

**Response** `200`
```json
{
    "accountId": "ACC-12345",
    "balance": 648.75
}
```

---

## Task 2 — Validation

### Multiple validation errors

Bad amount + currency + account are reported together in one `{error, details[]}` envelope (HTTP 400).

```bash
curl -X POST "http://localhost:3000/transactions" \
  -H "Content-Type: application/json" \
  -d '{"fromAccount":"bad","amount":-5,"currency":"XYZ","type":"transfer"}'
```

**Response** `400`
```json
{
    "error": "Validation failed",
    "details": [
        {
            "field": "amount",
            "message": "Amount must be a positive number"
        },
        {
            "field": "currency",
            "message": "Invalid currency code"
        },
        {
            "field": "toAccount",
            "message": "Transfer requires a destination account"
        },
        {
            "field": "fromAccount",
            "message": "Account must match format ACC-XXXXX (5 alphanumeric characters)"
        }
    ],
    "requestId": "1626ed94-0bea-4e72-b1c3-40ef4d89ac64"
}
```

### Currency-aware precision

JPY has 0 minor units, so a fractional amount is rejected (USD/EUR/GBP still allow 2 dp).

```bash
curl -X POST "http://localhost:3000/transactions" \
  -H "Content-Type: application/json" \
  -d '{"toAccount":"ACC-12345","amount":100.5,"currency":"JPY","type":"deposit"}'
```

**Response** `400`
```json
{
    "error": "Validation failed",
    "details": [
        {
            "field": "amount",
            "message": "Amount exceeds the maximum 0 decimal place(s) for JPY"
        }
    ],
    "requestId": "474be2ee-08f6-4353-ae13-a4bf10450235"
}
```

---

## Task 3 — Filtering

### Filter by account

Matches transactions where the account is sender OR receiver.

```bash
curl "http://localhost:3000/transactions?accountId=ACC-12345"
```

**Response** `200`
```json
[
    {
        "id": "a994bd9f-8539-45a5-b375-cd871772b149",
        "fromAccount": null,
        "toAccount": "ACC-12345",
        "amount": 1000.0,
        "currency": "USD",
        "type": "deposit",
        "timestamp": "2026-06-07T11:21:03.459549Z",
        "status": "completed"
    },
    {
        "id": "fa673fce-37c5-4542-8935-1cbd799729b6",
        "fromAccount": "ACC-12345",
        "toAccount": null,
        "amount": 150.25,
        "currency": "USD",
        "type": "withdrawal",
        "timestamp": "2026-06-07T11:21:03.476572Z",
        "status": "completed"
    },
    {
        "id": "8b0d8503-a9ca-4142-838f-c864bd3b8e6c",
        "fromAccount": "ACC-12345",
        "toAccount": "ACC-67890",
        "amount": 100.5,
        "currency": "USD",
        "type": "transfer",
        "timestamp": "2026-06-07T11:21:03.493559Z",
        "status": "completed"
    },
    {
        "id": "5bc0960b-ef7f-4174-af70-4994a340f0a8",
        "fromAccount": "ACC-12345",
        "toAccount": "ACC-67890",
        "amount": 100.5,
        "currency": "USD",
        "type": "transfer",
        "timestamp": "2026-06-07T11:21:03.609105Z",
        "status": "completed"
    }
]
```

### Filter by type

Only transfers.

```bash
curl "http://localhost:3000/transactions?type=transfer"
```

**Response** `200`
```json
[
    {
        "id": "8b0d8503-a9ca-4142-838f-c864bd3b8e6c",
        "fromAccount": "ACC-12345",
        "toAccount": "ACC-67890",
        "amount": 100.5,
        "currency": "USD",
        "type": "transfer",
        "timestamp": "2026-06-07T11:21:03.493559Z",
        "status": "completed"
    },
    {
        "id": "5bc0960b-ef7f-4174-af70-4994a340f0a8",
        "fromAccount": "ACC-12345",
        "toAccount": "ACC-67890",
        "amount": 100.5,
        "currency": "USD",
        "type": "transfer",
        "timestamp": "2026-06-07T11:21:03.609105Z",
        "status": "completed"
    }
]
```

### Combined filters

Account + type + date range (AND semantics).

```bash
curl "http://localhost:3000/transactions?accountId=ACC-12345&type=transfer&from=2000-01-01&to=2999-12-31"
```

**Response** `200`
```json
[
    {
        "id": "8b0d8503-a9ca-4142-838f-c864bd3b8e6c",
        "fromAccount": "ACC-12345",
        "toAccount": "ACC-67890",
        "amount": 100.5,
        "currency": "USD",
        "type": "transfer",
        "timestamp": "2026-06-07T11:21:03.493559Z",
        "status": "completed"
    },
    {
        "id": "5bc0960b-ef7f-4174-af70-4994a340f0a8",
        "fromAccount": "ACC-12345",
        "toAccount": "ACC-67890",
        "amount": 100.5,
        "currency": "USD",
        "type": "transfer",
        "timestamp": "2026-06-07T11:21:03.609105Z",
        "status": "completed"
    }
]
```

---

## Task 4 — Additional features

### A · Account summary

Totals, count, and most-recent transaction date.

```bash
curl "http://localhost:3000/accounts/ACC-12345/summary"
```

**Response** `200`
```json
{
    "accountId": "ACC-12345",
    "totalDeposits": 1000.0,
    "totalWithdrawals": 150.25,
    "transactionCount": 4,
    "mostRecentTransactionDate": "2026-06-07T11:21:03.609105+00:00"
}
```

### B · Simple interest

interest = balance × rate × days / 365.

```bash
curl "http://localhost:3000/accounts/ACC-12345/interest?rate=0.05&days=30"
```

**Response** `200`
```json
{
    "accountId": "ACC-12345",
    "balance": 648.75,
    "rate": 0.05,
    "days": 30,
    "interest": 2.666095890410959
}
```

### C · CSV export

All transactions as CSV (`/export` is routed before `/{id}`).

```bash
curl "http://localhost:3000/transactions/export?format=csv"
```

**Response** `200` (`text/csv`)
```
id,fromAccount,toAccount,amount,currency,type,timestamp,status
a994bd9f-8539-45a5-b375-cd871772b149,,ACC-12345,1000.00,USD,deposit,2026-06-07T11:21:03.459549+00:00,completed
fa673fce-37c5-4542-8935-1cbd799729b6,ACC-12345,,150.25,USD,withdrawal,2026-06-07T11:21:03.476572+00:00,completed
8b0d8503-a9ca-4142-838f-c864bd3b8e6c,ACC-12345,ACC-67890,100.50,USD,transfer,2026-06-07T11:21:03.493559+00:00,completed
5bc0960b-ef7f-4174-af70-4994a340f0a8,ACC-12345,ACC-67890,100.50,USD,transfer,2026-06-07T11:21:03.609105+00:00,completed
```


### D · Rate limiting

Each IP is capped (default 100 req/min); exceeding it returns 429 with the standard envelope. Example with a low limit:

```bash
# server started with RATE_LIMIT_MAX=5
for i in $(seq 1 7); do curl -s -o /dev/null -w "%{http_code} " "http://localhost:3000/transactions"; done
```

**Response** sequence: `200 200 200 200 200 429 429`

---

## Reliability — consistent error envelope

### Unknown route

Unknown paths and wrong methods use the same `{error, requestId}` envelope (HTTP 404).

```bash
curl "http://localhost:3000/no-such-endpoint"
```

**Response** `404`
```json
{
    "error": "Not Found",
    "requestId": "41954e81-2ded-4561-9bd5-2b424269633a"
}
```
