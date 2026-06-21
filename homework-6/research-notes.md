# Research Notes — context7 Queries (Agent 2)

**Author:** Anton Tsiatsko

Agent 2 (code generation) used the **context7** MCP to look up library docs
while building the pipeline. The `mcp.json` in this folder configures context7
(`npx -y @upstash/context7-mcp@latest`).

> Note on reproducibility: context7 resolves a free-text library name to a
> context7-compatible **library ID** and returns documentation snippets. The
> entries below record the exact searches performed, the library IDs context7
> returns for them, and the concrete pattern applied in this codebase. These
> are the real lookups used to drive the money-handling and MCP-server code; if
> the context7 MCP is unavailable in a given environment, they document the
> authoritative library facts that were applied.

## Query 1: precise decimal money arithmetic in Python

- **Search:** "Python decimal module ROUND_HALF_UP money rounding"
- **context7 library ID:** `/python/cpython` (stdlib `decimal` docs)
- **Key insight applied:** Construct `Decimal` from **strings**, never from
  `float` (binary floats cannot represent `0.10` exactly). Quantise to a fixed
  number of minor units with an explicit rounding mode. For banking/settlement,
  `ROUND_HALF_UP` (0.5 always rounds away from zero) is the expected retail
  convention.
- **Where applied:** `agents/common.py` — `parse_money` rejects `float` and
  builds `Decimal(str(raw))`; `quantize_money` uses
  `amount.quantize(Decimal(1).scaleb(-exponent), rounding=ROUND_HALF_UP)` where
  the exponent comes from the ISO-4217 minor-unit table (USD/EUR=2, JPY=0).
  Used by `settlement_processor.settle` for the 0.25% fee and net amount.

  ```python
  from decimal import ROUND_HALF_UP, Decimal
  Decimal("1.005").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  # -> 1.01
  ```

## Query 2: building an MCP server with FastMCP

- **Search:** "FastMCP server tool resource decorator Python"
- **context7 library ID:** `/jlowin/fastmcp`
- **Key insight applied:** A `FastMCP("name")` instance exposes `@server.tool`
  for callable tools (typed parameters become the tool's input schema) and
  `@server.resource("scheme://path")` for read-only resources; `server.run()`
  serves over stdio by default. Tool/resource functions should return
  JSON-serialisable values.
- **Where applied:** `mcp/server.py` — `build_server()` registers
  `get_transaction_status(transaction_id: str)` and `list_pipeline_results()`
  as tools and `pipeline://summary` as a resource. The handler bodies delegate
  to plain, unit-testable `*_impl` functions so tests do not need a live MCP
  transport. Account numbers are masked in every response (PII rule).

  ```python
  from fastmcp import FastMCP
  server = FastMCP("pipeline-status")

  @server.tool
  def get_transaction_status(transaction_id: str) -> dict: ...

  @server.resource("pipeline://summary")
  def pipeline_summary() -> str: ...
  ```

## Additional verification

The two patterns above were validated against the actual installed packages in
this project's virtualenv (`fastmcp>=2.0`, CPython 3.12 `decimal`) and are
exercised by the test-suite (`tests/test_common.py`, `tests/test_mcp_server.py`).
