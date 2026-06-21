# HOWTORUN — Homework 5 MCP Servers

All commands assume you are in the `homework-5/` directory and using **Claude Code**.
The shared config is [`.mcp.json`](.mcp.json); Claude Code reads it at startup, so **restart
the session after any edit**.

Verify what's registered at any time with:

```bash
claude mcp list          # ✓ Connected / auth status per server
claude mcp get <name>    # details for one server
```
Inside a session, `/mcp` shows live connection + auth state and re-triggers OAuth.

---

## 1. GitHub MCP (HTTP)

Credentials come from the `GITHUB_MCP_TOKEN` env var (never committed).

```bash
# Option A — reuse the GitHub CLI's token (already has `repo` scope):
export GITHUB_MCP_TOKEN="$(gh auth token)"

# Option B — use a fine-grained PAT with `repo` scope from
#   https://github.com/settings/personal-access-tokens
# export GITHUB_MCP_TOKEN="github_pat_xxx"

claude          # launch Claude Code so it picks up .mcp.json + the env var
```

Test prompt:
> "Use the github server to list my 5 most recent pull requests in the
> tsanm/gen-ai-software-engineering repo and summarize them."

→ screenshot to `docs/screenshots/github-mcp-result.png`.

**Gotchas:** `401` = bad/expired token or missing `repo` scope. HTTP transport needs
Claude Code ≥ 2.1.1.

---

## 2. Filesystem MCP (stdio, npx)

No install needed — `npx -y` fetches the official server on first run. `.mcp.json` points it
at `${HOME}/src/gen-ai-software-engineering` (adjust the path there if your checkout differs).
Requires Node 18+.

Test prompt:
> "Use the filesystem server to list the files in the homework-5 directory and summarize the
> project structure."

→ screenshot to `docs/screenshots/filesystem-mcp-result.png`.

**Gotchas:** first run is slow (npx download) — if it times out, relaunch with
`MCP_TIMEOUT=60000 claude`. "Operation not permitted" = path outside the allowed directory.

---

## 3. Notion MCP (HTTP, OAuth)

The hosted server is OAuth-only — no token to store.

1. Launch `claude`, then run `/mcp`, select **notion**, and complete the browser OAuth flow.
   Approve the workspace + the database you want to expose.
2. Make sure your Notion database has a property identifying bugs (e.g. `Type = Bug`).

Test prompt (the assignment's required request):
> "Using Notion, give me the pages of the last 5 bugs on my project — the 5 most recently
> created items where Type is Bug, sorted by created time descending. List page IDs and links."

→ screenshot the request **and** response to `docs/screenshots/jira-or-notion-mcp-result.png`.
**Show only page IDs / numbers — no sensitive content.**

**Gotchas:** OAuth needs a human in the loop (not headless). The "bug" filter only works if
your database actually has a Bug type/status property.

---

## 4. Custom MCP server: `lorem` (stdio, FastMCP)

### Install dependencies

```bash
cd custom-mcp-server
python -m pip install -r requirements.txt   # installs fastmcp>=2.14,<3
cd ..
```

### Run the server directly (sanity check)

```bash
python custom-mcp-server/server.py          # starts on stdio; Ctrl-C to stop
# or, with the FastMCP CLI:
fastmcp run custom-mcp-server/server.py
# interactive testing in the MCP Inspector UI:
fastmcp dev custom-mcp-server/server.py
```

### Connect to Claude Code

Already registered in `.mcp.json` as `lorem` (`python custom-mcp-server/server.py`). Make sure
`fastmcp` is installed in the **same** Python that runs as `python`, then launch `claude` from
the `homework-5/` directory and confirm with `claude mcp list` / `/mcp`.

### Use / test the `read` tool

Test prompts:
> "Use the lorem server's `read` tool to return the default number of words."   (→ 30 words)
>
> "Call the lorem `read` tool with word_count 10."                              (→ 10 words)
>
> "Read the resource `resource://lorem`."                                       (→ 30 words, default)
>
> "Read the resource `resource://lorem/15`."                                    (→ 15 words)

→ screenshot to `docs/screenshots/custom-mcp-read-tool-result.png`.

**Verify checklist (assignment success criteria):**
- [ ] `python custom-mcp-server/server.py` starts without error.
- [ ] `claude mcp get lorem` shows it connected.
- [ ] `read` (default) returns exactly 30 words; `read(10)` returns 10.
- [ ] `resource://lorem/{n}` returns `n` words.
- [ ] `fastmcp` appears in `custom-mcp-server/requirements.txt`.

---

## 5. Context7 MCP (optional enhancement, HTTP)

A 5th server (Upstash Context7) that gives Claude Code live, version-specific library docs
(incl. FastMCP/MCP). Already registered in `.mcp.json` over HTTP — works keyless on the basic
tier. For higher rate limits, get a free key at https://context7.com/dashboard and:
```bash
export CONTEXT7_API_KEY="ctx7sk_..."   # env-expanded in .mcp.json; never committed
```
Test prompt:
> "Use context7 to fetch the current FastMCP docs for defining a tool."

See [`BEST_PRACTICES.md`](BEST_PRACTICES.md) for why this is on-topic for the assignment.

> **Security note:** for Task 1, a **fine-grained GitHub PAT** scoped to a single repo
> (Metadata: Read + only the permissions you need) is preferred over the broad `gh auth token`;
> the token route is the convenience option. Keep the Filesystem server's allowed directory
> narrow. Details in `BEST_PRACTICES.md`.

## Quick all-up verification

```bash
export GITHUB_MCP_TOKEN="$(gh auth token)"
python -m pip install -r custom-mcp-server/requirements.txt
claude mcp list      # expect: github ✓, filesystem ✓, notion (auth), lorem ✓
```
Then in-session run `/mcp`, authenticate Notion, and run the four test prompts above,
capturing a screenshot for each into `docs/screenshots/`.
