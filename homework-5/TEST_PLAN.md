# Homework 5 — Test Plan

Derived clause-by-clause from [`TASKS.md`](TASKS.md). Every requirement sentence maps to one or
more test cases. Each task has ≥5 **P1** (must-pass / core correctness) and ≥5 **P2**
(important / edge / secondary) cases.

**Priority:** P1 = blocks the deliverable if it fails; P2 = important robustness/edge/secondary.
**Type:** `AUTO` = executed by the pytest suite in [`tests/`](tests/); `MANUAL` = requires an
interactive Claude Code session / live account / screenshot evidence (cannot be scripted here).

Run the automated portion with:
```bash
cd homework-5
python -m pip install -r tests/requirements-dev.txt
python -m pytest tests -v
```

Legend for the **Auto** column: ▶ test function that covers the row.

---

## Task 1 — GitHub MCP

> "Connect Claude to your GitHub account via the official GitHub MCP server … Install and
> configure the GitHub MCP server; ensure it is registered and running without errors; perform
> at least one interaction … configured with valid credentials; at least one successful
> interaction; screenshot(s) of the MCP call results."

| ID | Requirement clause | Test | Pri | Type |
|----|--------------------|------|-----|------|
| 1-P1-1 | "the official GitHub MCP server" | `.mcp.json` `github.url` == `https://api.githubcopilot.com/mcp/` | P1 | AUTO ▶`test_github_uses_official_server` |
| 1-P1-2 | "Install and configure" | `github` entry present with `type: http` | P1 | AUTO ▶`test_github_transport_http` |
| 1-P1-3 | "configured with valid credentials" | Auth supplied via `Authorization: Bearer …` header | P1 | AUTO ▶`test_github_auth_header_present` |
| 1-P1-4 | "configured with valid credentials" (no leaked secret) | Header uses `${ENV}` expansion, no hardcoded token | P1 | AUTO ▶`test_no_secrets_committed` |
| 1-P1-5 | "registered and running without errors" | Live MCP client connects to the GitHub server with `gh` token and lists ≥1 tool | P1 | AUTO* ▶`test_github_live_connection` (skips w/o token+net) |
| 1-P2-1 | "perform at least one interaction (list PRs…)" | Live client can call a read tool (e.g. list PRs / search repos) | P2 | AUTO* ▶`test_github_live_list_tools` |
| 1-P2-2 | Credential scope | `gh auth token` available and has `repo` scope (precondition) | P2 | AUTO* ▶`test_gh_cli_scope` |
| 1-P2-3 | Transport requirement | HTTP transport entry has both `type` and `url` keys | P2 | AUTO ▶`test_github_entry_shape` |
| 1-P2-4 | "screenshot(s) of the MCP call results" | `docs/screenshots/github-mcp-result.png` exists | P2 | MANUAL (capture) |
| 1-P2-5 | Reproducibility | HOWTORUN documents `export GITHUB_MCP_TOKEN=$(gh auth token)` | P2 | AUTO ▶`test_howto_documents_github_token` |

\* AUTO but skips gracefully when network/token unavailable; the skip is reported, never a false pass.

---

## Task 2 — Filesystem MCP

> "Connect Claude/Copilot to a directory on your machine via the Filesystem MCP server …
> configure the Filesystem MCP server with a path to a directory; ensure it is registered and
> running; perform at least one interaction (list files, read a file, summarize) … configured
> with a valid path; at least one successful interaction; screenshot(s)."

| ID | Requirement clause | Test | Pri | Type |
|----|--------------------|------|-----|------|
| 2-P1-1 | "the Filesystem MCP server" | `filesystem` args reference `@modelcontextprotocol/server-filesystem` | P1 | AUTO ▶`test_filesystem_official_package` |
| 2-P1-2 | "configure … with a path to a directory" | A directory path arg is present in args | P1 | AUTO ▶`test_filesystem_has_path_arg` |
| 2-P1-3 | "configured with a valid path" | The configured directory actually exists on disk | P1 | AUTO ▶`test_filesystem_path_exists` |
| 2-P1-4 | stdio transport | Entry `type: stdio`, `command: npx` | P1 | AUTO ▶`test_filesystem_transport` |
| 2-P1-5 | "registered and running" | Live MCP client launches the server (stdio npx) and lists tools | P1 | AUTO* ▶`test_filesystem_live_connection` (skips w/o node/net) |
| 2-P2-1 | "list files … interaction" | Live client lists the configured directory and returns entries | P2 | AUTO* ▶`test_filesystem_live_list_dir` |
| 2-P2-2 | "read a file … interaction" | Live `read_text_file` returns this repo's `TASKS.md` content | P2 | AUTO* ▶`test_filesystem_live_read_file` |
| 2-P2-3 | Tool surface | Tool set includes `list_directory` and `read_text_file` | P2 | AUTO* ▶`test_filesystem_tool_surface` |
| 2-P2-4 | "screenshot(s)" | `docs/screenshots/filesystem-mcp-result.png` exists | P2 | MANUAL (capture) |
| 2-P2-5 | npx auto-fetch (`-y`) | Args include `-y` so no interactive prompt blocks startup | P2 | AUTO ▶`test_filesystem_npx_yes_flag` |

---

## Task 3 — Notion MCP

> "Connect Claude to … Notion via the corresponding MCP server … with the required
> credentials; ensure it is registered and running; make the following request: 'Give me the
> tickets/pages of the last 5 bugs on a project'. Capture the full response. Avoid sharing
> sensitive information — use only ticket/page numbers … configured and working; the request
> for the last 5 bug tickets/pages returns valid results; screenshots (request and response)."

| ID | Requirement clause | Test | Pri | Type |
|----|--------------------|------|-----|------|
| 3-P1-1 | "Notion … MCP server" | `notion` entry present, `url` host == `mcp.notion.com` | P1 | AUTO ▶`test_notion_official_server` |
| 3-P1-2 | "with the required credentials" | Hosted server uses OAuth (no token committed); HOWTORUN documents the `/mcp` OAuth flow | P1 | AUTO ▶`test_notion_oauth_documented` |
| 3-P1-3 | HTTP transport | Entry `type: http` with `url` | P1 | AUTO ▶`test_notion_transport` |
| 3-P1-4 | "the last 5 bugs on a project" | HOWTORUN contains the exact required query for the last 5 bugs | P1 | AUTO ▶`test_notion_bug_query_documented` |
| 3-P1-5 | "registered and running" / returns valid results | Notion OAuth + DB query returning 5 bug pages | P1 | MANUAL (live OAuth, browser) |
| 3-P2-1 | "use only ticket/page numbers" | README/HOWTORUN instructs redacting to page IDs only | P2 | AUTO ▶`test_notion_redaction_note` |
| 3-P2-2 | "Capture the full response" | Screenshot must show request **and** response | P2 | MANUAL (capture) |
| 3-P2-3 | "screenshots" | `docs/screenshots/jira-or-notion-mcp-result.png` exists | P2 | MANUAL (capture) |
| 3-P2-4 | No leaked secret | No Notion token (`ntn_`/`secret_`) committed | P2 | AUTO ▶`test_no_secrets_committed` |
| 3-P2-5 | Bug-filtering caveat documented | Docs note that "bug" depends on a DB `Type = Bug` property | P2 | AUTO ▶`test_notion_bug_property_note` |

---

## Task 4 — Custom MCP Server (FastMCP)

> "Create the custom MCP server in a separate folder … with server.py implementing FastMCP.
> Add a Resource URI that reads from lorem-ipsum.md, accepts a word_count parameter (default
> 30), and returns exactly that many words. Add a Tool named read … optional word_count …
> returns the content from the resource. … HOWTORUN.md (install, run, connect, test). Verify:
> starting script works; MCP config valid and points to the custom server; fastmcp present in
> dependencies. … resource and read tool both return expected word-limited content."

| ID | Requirement clause | Test | Pri | Type |
|----|--------------------|------|-----|------|
| 4-P1-1 | "server.py implementing FastMCP" in "a separate folder" | `custom-mcp-server/server.py` imports; `mcp` is a `FastMCP` instance | P1 | AUTO ▶`test_server_is_fastmcp` |
| 4-P1-2 | "a Tool named read" | `list_tools()` contains a tool named exactly `read` | P1 | AUTO ▶`test_read_tool_registered` |
| 4-P1-3 | "Resource URI that reads from lorem-ipsum.md" | Resource template `resource://lorem/{word_count}` registered | P1 | AUTO ▶`test_resource_registered` |
| 4-P1-4 | "default 30 … returns exactly that many words" | `read()` (no args) returns exactly 30 words | P1 | AUTO ▶`test_read_default_30_words` |
| 4-P1-5 | "returns … words" matches source | `read(30)` equals first 30 words of `lorem-ipsum.md` | P1 | AUTO ▶`test_read_matches_source` |
| 4-P1-6 | "starting script works" / "MCP config points to custom server" | Launch `python server.py` as a real stdio MCP server and call `read` over the wire | P1 | AUTO ▶`test_server_runs_as_stdio_subprocess` |
| 4-P2-1 | "returns exactly that many words" (tool) | `read(10)` returns exactly 10 words; `read(1)` → `Lorem` | P2 | AUTO ▶`test_read_arbitrary_counts` |
| 4-P2-2 | "Resource … returns exactly that many words" | `resource://lorem/15` returns exactly 15 words | P2 | AUTO ▶`test_resource_word_count` |
| 4-P2-3 | "Tool … returns the content from the resource" | Tool and resource return identical text for the same count | P2 | AUTO ▶`test_tool_resource_agree` |
| 4-P2-4 | "optional word_count" | `read` input schema marks `word_count` optional (has default) | P2 | AUTO ▶`test_read_word_count_optional` |
| 4-P2-5 | Robustness | `read(10_000)` returns all available words without error | P2 | AUTO ▶`test_read_count_exceeds_file` |
| 4-P2-6 | "fastmcp present in dependencies" | `requirements.txt` pins `fastmcp` | P2 | AUTO ▶`test_fastmcp_in_requirements` |
| 4-P2-7 | "explanation … Resources … Tools" | README defines both Resources and Tools | P2 | AUTO ▶`test_readme_explains_resources_and_tools` |
| 4-P2-8 | "HOWTORUN (install, run, connect, test)" | HOWTORUN has all four sections | P2 | AUTO ▶`test_howto_has_all_sections` |

---

## Deliverables & structure (cross-cutting)

> Expected structure: README.md, HOWTORUN.md, custom-mcp-server/{server.py, lorem-ipsum.md,
> requirements.txt}, mcp.json/.mcp.json, docs/screenshots/.

| ID | Requirement | Test | Pri | Type |
|----|-------------|------|-----|------|
| D-P1-1 | All 4 servers registered in one config | `.mcp.json` `mcpServers` has exactly github, filesystem, notion, lorem | P1 | AUTO ▶`test_all_four_servers_registered` |
| D-P1-2 | Required files exist | Every file in the expected structure exists | P1 | AUTO ▶`test_expected_structure_exists` |
| D-P1-3 | README has author name | README contains "Anton Tsiatsko" | P1 | AUTO ▶`test_readme_has_author` |
| D-P2-1 | lorem source usable | `lorem-ipsum.md` has ≥ 30 words | P2 | AUTO ▶`test_lorem_has_enough_words` |
| D-P2-2 | screenshots folder present | `docs/screenshots/` exists | P2 | AUTO ▶`test_screenshots_dir_exists` |
| D-P2-3 | All 4 screenshots captured | 4 named PNGs present | P2 | MANUAL (capture) |

---

## Best-practices hardening (added after the MCP best-practices audit — see BEST_PRACTICES.md)

| ID | Requirement | Test | Pri | Type |
|----|-------------|------|-----|------|
| BP-P0-1 | Resource "default 30" must be reachable (not just via required path placeholder) | `resource://lorem` returns 30 words | P0 | AUTO ▶`test_resource_default_reachable` |
| BP-P0-2 | "validate all tool inputs" — reject out-of-range `word_count` | `read(0)` and `read(-5)` raise | P0 | AUTO ▶`test_read_rejects_zero` / `test_read_rejects_negative` |
| BP-P1-1 | Default resource is discoverable | `resource://lorem` appears in `list_resources()` | P1 | AUTO ▶`test_resource_default_lists` |
| BP-P1-2 | Resource input validation | `resource://lorem/0` raises | P1 | AUTO ▶`test_resource_rejects_zero` |
| BP-P1-3 | Tool annotations (read-only/idempotent) | `read` has `readOnlyHint: true` | P1 | AUTO ▶`test_read_is_read_only_annotated` |
| BP-P1-4 | Parameter self-documentation + bound | `word_count` schema has description + `minimum: 1` | P1 | AUTO ▶`test_read_param_has_description` |
| BP-P1-5 | stdio: no stdout pollution | server completes MCP handshake as a subprocess | P1 | AUTO ▶`test_server_runs_as_stdio_subprocess` |
| BP-P2-1 | Context7 enhancement well-formed (optional 5th server) | `context7` is http + `mcp.context7.com` | P2 | AUTO ▶`test_context7_enhancement_well_formed` |

> Not yet applied (documented in BEST_PRACTICES.md): GitHub fine-grained PAT (P1), pin/narrow
> Filesystem server (P1), `fastmcp.json` project config (P2). These are credential/ops choices
> outside the custom server code.

## Manual evidence checklist (the human-only part)

These cannot be scripted in this environment; capture during an interactive Claude Code session:

- [ ] `github-mcp-result.png` — a GitHub MCP interaction (e.g. list recent PRs).
- [ ] `filesystem-mcp-result.png` — a Filesystem MCP interaction (list/read).
- [ ] `jira-or-notion-mcp-result.png` — the "last 5 bugs" request **and** response (page IDs only).
- [ ] `custom-mcp-read-tool-result.png` — calling the `read` tool from Claude Code.
- [ ] Notion OAuth completed via `/mcp`; database has a `Type = Bug` property.
