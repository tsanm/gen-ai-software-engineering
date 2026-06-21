# Homework 5 — MCP Servers: Research Notes

> Research compiled 2026-06-21 in an isolated git worktree (`atsiatsko_home_work_5` branch)
> while another session works hw4. Nothing here touches the hw4 working tree.
>
> Verified against current docs (June 2026). Sources listed per section.

## TL;DR — recommended path per task

| Task | Recommended choice | Why |
|------|--------------------|-----|
| 1. GitHub MCP | Remote HTTP server `https://api.githubcopilot.com/mcp/` + PAT | No Docker needed; one `claude mcp add` command |
| 2. Filesystem MCP | `@modelcontextprotocol/server-filesystem` via npx | Official, zero-install (npx), point at this repo |
| 3. Jira **or** Notion | **Jira** (Atlassian Remote MCP) | `Bug` is a first-class issue type → query maps 1:1 to the assignment |
| 4. Custom FastMCP | `from fastmcp import FastMCP` (2.x) | Standalone framework; resource template + `read` tool |

---

## Task 1 — GitHub MCP

### Add (remote HTTP, recommended)
```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp/ \
  --header "Authorization: Bearer YOUR_GITHUB_PAT"
```
- PAT: create a fine-grained token at https://github.com/settings/personal-access-tokens with `repo` scope.
- Don't commit the PAT. Use `${GITHUB_MCP_TOKEN}` env expansion in `.mcp.json` and export the var before launching.

### `.mcp.json` entry
```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": { "Authorization": "Bearer ${GITHUB_MCP_TOKEN}" }
    }
  }
}
```

### Local Docker alternative
```bash
claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=YOUR_PAT -- \
  docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server
```

### Demo interaction (screenshot)
> "Use the github server to show me my 10 most recent open pull requests"
or create an issue. Tools: `search_repositories`, `get_pull_request`, `create_issue`.

### Gotchas
- `401` → bad/expired PAT or missing `repo` scope.
- HTTP transport needs Claude Code ≥ 2.1.1; else use Docker.
- `.mcp.json` is read at startup — restart the session after editing.

---

## Task 2 — Filesystem MCP

### Add
```bash
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem /abs/path/to/dir
```
All file ops are restricted to the directories you pass as trailing args (can pass several).

### `.mcp.json` entry
```json
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/abs/path/to/project"]
    }
  }
}
```
Windows: wrap with `cmd /c`.

### Demo interaction (screenshot)
> "Use the filesystem server to list all files in <dir> and summarize the structure"
Tools: `read_text_file`, `list_directory`, `search_files`, `get_file_metadata`, plus write tools.

### Gotchas
- First run is slow (npx downloads). Bump `MCP_TIMEOUT=60000` if it times out.
- "Operation not permitted" → path outside allowed dirs.
- Needs Node 18+.

---

## Task 3 — Jira or Notion MCP

**Recommendation: Jira.** `Bug` is a built-in issue type and there's a real JQL tool, so
`project = KEY AND issuetype = Bug ORDER BY created DESC` is exactly what the assignment asks.
Notion has no native "bug" concept — it only works if you've built a database with a Bug property.

### Jira (Atlassian Remote MCP, OAuth)
```bash
claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp
```
- Use `/v1/mcp` (the `/v1/sse` endpoint is deprecated).
- Authenticate: run `/mcp` → select `atlassian` → browser OAuth. Respects your Jira permissions.
- `.mcp.json`:
```json
{ "mcpServers": { "atlassian": { "type": "http", "url": "https://mcp.atlassian.com/v1/mcp" } } }
```
- Query (tool `searchJiraIssuesUsingJql`):
  > "Using Jira, give me the last 5 bugs in project ABC — JQL `project = ABC AND issuetype = Bug ORDER BY created DESC`, max 5; list key, summary, link."
- Caveats: needs an Atlassian **Cloud** site (Free tier OK); site/org admin can restrict which MCP clients are allowed; Data Center/Server not supported.

### Notion (hosted, OAuth) — fallback
```bash
claude mcp add --transport http notion https://mcp.notion.com/mcp
```
- OAuth-only (no token). Self-hosted npm alt: `@notionhq/notion-mcp-server` with `NOTION_TOKEN` env,
  and you must grant the integration access to the database via **Connections**.
- Query relies on a database having a Type/Status = "Bug" property; tools `retrieve-a-database` + `query-data-source`.

Remember: assignment says screenshot the request + response but **only show ticket/page numbers** — no sensitive data.

---

## Task 4 — Custom MCP Server (FastMCP)

### Install
```bash
pip install fastmcp        # or: uv add fastmcp
```
- Use the **standalone** package: `from fastmcp import FastMCP` (FastMCP 2.x, currently 2.14.x; pin `>=2.14,<3`).
- NOT `from mcp.server.fastmcp import FastMCP` (that's the frozen 1.0 bundled in the SDK — decorators are the same though).
- Python ≥ 3.10.

### Key API facts
- Resource: `@mcp.resource("resource://lorem/{word_count}")` — `{placeholder}` makes it a **template**; the placeholder must be a function param. URI params arrive as **strings** → `int(word_count)`.
- Path placeholders are **required** in the URI; for a truly optional one use query syntax `{?format}`.
- Tool: `@mcp.tool` (parens optional); override name with `@mcp.tool(name="read")`. Type hints required.
- A tool can read a resource via injected `ctx: Context` + `await ctx.read_resource(uri)`, but for this homework it's simpler/robust to factor a plain helper and call it from both.
- `mcp.run()` defaults to **stdio** — exactly what Claude Code needs.

### Reference `server.py` (verified pattern)
```python
# server.py
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP(name="LoremServer")

LOREM_PATH = Path(__file__).parent / "lorem-ipsum.md"
DEFAULT_WORD_COUNT = 30


def _read_words(word_count: int = DEFAULT_WORD_COUNT) -> str:
    """Return exactly `word_count` whitespace-separated words from lorem-ipsum.md."""
    words = LOREM_PATH.read_text(encoding="utf-8").split()
    return " ".join(words[:word_count])


@mcp.resource("resource://lorem/{word_count}")
def lorem_resource(word_count: int = DEFAULT_WORD_COUNT) -> str:
    """Return `word_count` words from lorem-ipsum.md."""
    return _read_words(int(word_count))


@mcp.tool(name="read")
def read(word_count: int = DEFAULT_WORD_COUNT) -> str:
    """Read `word_count` words (default 30) from lorem-ipsum.md and return them."""
    return _read_words(word_count)


if __name__ == "__main__":
    mcp.run()  # stdio
```

### Run
```bash
python server.py
fastmcp run server.py          # CLI, auto-discovers `mcp`
fastmcp dev server.py          # MCP Inspector UI for testing
```

### Connect to Claude Code — `.mcp.json`
```json
{
  "mcpServers": {
    "lorem": {
      "command": "uv",
      "args": ["run", "--with", "fastmcp", "fastmcp", "run", "/abs/path/to/server.py"]
    }
  }
}
```
or, if fastmcp is installed in the active interpreter: `{"command": "python", "args": ["server.py"]}`.
Or let FastMCP write it: `fastmcp install claude-code server.py`.

### Dependency declaration
`requirements.txt`: `fastmcp>=2.14,<3` — or pyproject `dependencies = ["fastmcp>=2.14,<3"]`.

### Resources vs Tools (for the docs explanation)
- **Resource** = application-controlled, read-only, URI-addressed data source (like GET). Exposes context to read; should be idempotent / side-effect-free.
- **Tool** = model-controlled, name-addressed callable with a typed arg schema (like POST). The LLM decides to invoke it to perform an action that may have side effects.
- This homework intentionally exposes the same lorem text both ways because some hosts (incl. typical Claude Code flow) drive everything through **tool calls**, so the `read` tool guarantees the model can reach the content.

---

## Suggested build order when you start hw5
1. Scaffold `custom-mcp-server/` (server.py + lorem-ipsum.md + requirements.txt) — fully self-contained, no external accounts.
2. Add `.mcp.json` with all 4 servers.
3. Wire + screenshot GitHub and Filesystem (quick, no accounts beyond a PAT).
4. Wire + screenshot Jira (or Notion) — needs a real project.
5. Write README.md (author name) + HOWTORUN.md.

## Open questions to confirm with you
- Do you have a Jira Cloud site (and is MCP allowed by your admin), or should we plan for Notion?
- GitHub PAT available, or generate fine-grained one?
- `uv` vs plain `python`/`pip` for the custom server config.

## Sources
- Claude Code MCP docs: https://code.claude.com/docs/en/mcp
- GitHub MCP: https://github.com/github/github-mcp-server
- Filesystem MCP: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- FastMCP: https://github.com/jlowin/fastmcp
- Atlassian Remote MCP: https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/
- Notion MCP: https://developers.notion.com/guides/mcp/get-started-with-mcp
