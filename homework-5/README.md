# Homework 5 — Configure MCP Servers

> Configure three external MCP servers (**GitHub**, **Filesystem**, **Notion**) and build one
> **custom FastMCP server**, with real interactions captured from each.

**Author:** Anton Tsiatsko · `atsiatsko_home_work_5` → `main` · MCP · FastMCP · Python

---

## Servers (all in [`.mcp.json`](.mcp.json))

| # | Server | Type | Transport | Proof |
|---|--------|------|-----------|-------|
| 1 | GitHub | external (official) | HTTP `api.githubcopilot.com/mcp/` | live ✓ |
| 2 | Filesystem | external (official) | stdio `@modelcontextprotocol/server-filesystem` | live ✓ |
| 3 | Notion | external (official) | stdio `@notionhq/notion-mcp-server` (token) | live ✓ |
| 4 | **Lorem** | **custom (FastMCP)** | stdio `python custom-mcp-server/server.py` | live ✓ |
| 5 | Context7 | external (Upstash) — *bonus* | HTTP `mcp.context7.com/mcp` | live ✓ |

## Acceptance (maps to [`TASKS.md`](TASKS.md))

| Task | Deliverable | ✓ |
|------|-------------|---|
| 1 GitHub MCP | configured + `get_me` call | [screenshot](docs/screenshots/github-mcp-result.png) |
| 2 Filesystem MCP | configured + `list_directory`/`read_text_file` | [screenshot](docs/screenshots/filesystem-mcp-result.png) |
| 3 Notion MCP | configured + "last 5" query (page IDs only) | [screenshot](docs/screenshots/jira-or-notion-mcp-result.png) |
| 4 Custom FastMCP | `server.py` with resource + `read` tool | [screenshot](docs/screenshots/custom-mcp-read-tool-result.png) |
| Docs | `README.md` + [`HOWTORUN.md`](HOWTORUN.md) | ✅ |
| Deps | [`requirements.txt`](custom-mcp-server/requirements.txt) incl. `fastmcp` | ✅ |

## Custom server: `lorem`

[`custom-mcp-server/server.py`](custom-mcp-server/server.py) exposes [`lorem-ipsum.md`](custom-mcp-server/lorem-ipsum.md):

- **Resource** (read-only, URI) — `resource://lorem` (default 30 words) and `resource://lorem/{word_count}`.
- **Tool** `read(word_count=30)` (model-invoked) — returns the same word-limited text.

> **Resources** are URIs Claude *reads* for context (files/APIs) — read-only, like `GET`.
> **Tools** are actions Claude *calls* to perform an operation — like `POST`.

Hardened per the MCP spec/FastMCP best practices ([`BEST_PRACTICES.md`](BEST_PRACTICES.md)):
bounded/validated `word_count`, `readOnlyHint`/`idempotentHint`, masked errors, fixed file
(no path-traversal vector), secrets via `${ENV}` only.

## Run / verify

```bash
cd homework-5 && python -m pip install -r tests/requirements-dev.txt && python -m pytest tests   # 65 tests
# regenerate evidence report: export GITHUB_MCP_TOKEN=$(gh auth token); set -a; . .env; set +a; python capture/capture.py
```

## Layout

```
homework-5/
├── README.md  HOWTORUN.md  BEST_PRACTICES.md  TEST_PLAN.md  .mcp.json
├── custom-mcp-server/   server.py · lorem-ipsum.md · requirements.txt
├── capture/capture.py   real request/response → docs/screenshots/evidence.html
├── tests/               65 tests (custom E2E · config/security · live integration)
└── docs/screenshots/    github · filesystem · jira-or-notion · custom-mcp-read · context7
```
