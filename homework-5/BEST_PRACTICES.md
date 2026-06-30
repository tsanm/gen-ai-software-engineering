# Homework 5 — MCP Best-Practices Audit & Improvements

Audited the solution against the **official MCP spec** (modelcontextprotocol.io, spec
`2025-11-25`), the **FastMCP** docs (gofastmcp.com), and reputable security research
(Anthropic spec security pages, OWASP MCP Top 10, Trail of Bits, Invariant Labs, the
"EscapeRoute" filesystem CVEs). This file records what was found, what was fixed, and what
remains recommended — with priorities.

**Priority key:** P0 = correctness/security defect, fix now · P1 = idiomatic robustness ·
P2 = optional enhancement.

---

## Applied in this solution

### P0 — Resource "default 30" was unreachable (correctness defect) ✅ fixed
A path placeholder (`resource://lorem/{word_count}`) is a **required** parameter per RFC 6570 /
the MCP resource-template model — so the Python default `30` could never be exercised through
the resource, yet `TASKS.md` requires the resource to "accept a word_count parameter
(default: 30)". The RFC 6570 query form `{?word_count}` would fix it but has open FastMCP bugs
(jlowin/fastmcp #2085, #2322). **Fix:** register the function under **two URIs** —
`resource://lorem` (→ default 30) and `resource://lorem/{word_count}` (explicit count). Proven
by `test_resource_default_reachable`.
*Source: MCP Resources spec (Resource Templates); FastMCP Resources docs.*

### P0 — Input validation / bounding `word_count` ✅ fixed
Unbounded numeric input is a DoS vector and a spec violation ("servers MUST validate all tool
inputs"). **Fix:** `word_count: Annotated[int, Field(ge=1, le=100_000)]` on the tool (pydantic
rejects 0/negative/oversized before the function runs) and an explicit `ResourceError` check on
the resource path (resources don't get `Field` validation). Proven by `test_read_rejects_zero`,
`test_read_rejects_negative`, `test_resource_rejects_zero`.
*Source: MCP Tools spec (Security Considerations); FastMCP Tools docs (Annotated/Field).*

### P1 — Structured error handling ✅ fixed
Raw exceptions leak internals and don't give the model an actionable, safe message. **Fix:**
`FastMCP(..., mask_error_details=True)` + raise `ResourceError` for caller-facing messages
(these survive masking) while unexpected internals are masked.
*Source: FastMCP error-handling docs; MCP Tools spec (isError vs protocol errors).*

### P1 — Tool annotations (read-only / idempotent) ✅ fixed
`read` only reads and is idempotent. **Fix:** `ToolAnnotations(readOnlyHint=True,
idempotentHint=True, title=...)` so clients can skip confirmation prompts. (Note: the spec says
clients MUST treat annotations as untrusted hints — they are UX metadata, not enforcement.)
Proven by `test_read_is_read_only_annotated`.
*Source: MCP Tools spec (annotations); FastMCP `ToolAnnotations`.*

### P1 — Parameter descriptions + server `instructions` + `mime_type` ✅ fixed
Added a `description` to `word_count`, an `instructions=` string on the server (guidance the
client/LLM sees), and `mime_type="text/plain"` on both resource registrations. Proven by
`test_read_param_has_description`.
*Source: MCP Architecture (every property carries a description); Resources spec (mimeType).*

### P1 — stdout hygiene (stdio transport) ✅ verified
On stdio, **anything written to stdout that isn't a valid MCP message corrupts the protocol**.
The server never `print()`s; FastMCP logs to stderr. The `test_server_runs_as_stdio_subprocess`
test would fail if stray stdout output broke the handshake — so this is continuously verified.
*Source: MCP Transports spec (stdio: "MUST NOT write to stdout anything that is not a valid MCP
message"; logging → stderr).*

### Design note — path-traversal class does **not** apply ✅ safe by construction
Much MCP security guidance targets file servers with a user-controlled **path** (the
EscapeRoute CVEs CVE-2025-53109/53110 were `startsWith`/symlink bypasses). This server reads a
**fixed** file with **no path parameter**, so there is nothing to canonicalize and no traversal
vector. Documented in `server.py` rather than adding unnecessary path-sandboxing code.
*Source: EscapeRoute writeups (Cymulate/Snyk); MCP Resources spec (validate URIs).*

### P2 — Context7 as a 5th MCP server ✅ added (optional)
Added `context7` (Upstash) over **remote HTTP** (`https://mcp.context7.com/mcp`). It (a) is a
clean second example of HTTP-transport MCP configuration — directly on-topic for the homework —
and (b) gives Claude Code **live, version-specific FastMCP/MCP docs** (`/jlowin/fastmcp`,
`/modelcontextprotocol/docs`), mitigating stale-API risk while building MCP servers. Keyless
basic tier works; a free `CONTEXT7_API_KEY` (env-expanded, never committed) raises rate limits.
It is docs-retrieval only — a complement to, not a replacement for, the authoritative docs.
*Source: github.com/upstash/context7; context7.com/jlowin/fastmcp.*

---

## Recommended (not yet applied — mostly outside the custom server)

### P1 — GitHub least-privilege credential
The demo uses `gh auth token` (broad `repo` scope). Best practice is a **fine-grained PAT**
scoped to only the specific repo with minimal permissions (Metadata: Read + Contents/Issues/PRs
as needed), and/or the GitHub MCP server's `--read-only` / `--toolsets` narrowing. Documented in
HOWTORUN as the preferred option; the `gh` token is the convenience path.
*Source: GitHub fine-grained PAT docs; github/github-mcp-server README.*

### P1 — Pin the Filesystem server version
`npx -y @modelcontextprotocol/server-filesystem` fetches latest (good), but for reproducibility
pin `>= 2025.7.1` (the EscapeRoute-patched release) and keep the allowed directory **narrow**
(a project dir, never `$HOME` or `/`). Current config points at the repo root — acceptable for
the demo; tighten for real use.
*Source: EscapeRoute CVE advisories; server-filesystem README (allowed dirs / Roots).*

### P2 — `fastmcp.json` project config
FastMCP's `dependencies=` constructor arg is deprecated; the canonical project config is a
`fastmcp.json` (source / environment / deployment sections) that `fastmcp run` auto-detects.
`requirements.txt` already pins `fastmcp>=2.14,<3`, which satisfies the assignment; a
`fastmcp.json` would be the more idiomatic 2.x+ form.
*Source: FastMCP server-configuration docs; jlowin/fastmcp #2177.*

### P2 — Notion least-exposure
Token route (used here, since the key is stored as a secret) works headlessly; the hosted OAuth
route keeps credentials out of config entirely and is the spec-preferred option for remote
servers. Either is fine for the homework.

---

## Reviewer security checklist (status)

| Item | Status |
|------|--------|
| No secret literal in any committed file | ✅ `test_no_secrets_committed` |
| `.mcp.json` secrets via `${VAR}` expansion | ✅ github + context7 |
| `.env`/venv gitignored | ✅ `.gitignore` |
| Custom server: numeric param bounded | ✅ `Field(ge=1, le=…)` |
| Custom server: errors leak no internals | ✅ `mask_error_details=True` |
| Custom server: no path-traversal vector | ✅ fixed file, no path param |
| stdio servers, no stdout pollution | ✅ verified by subprocess test |
| GitHub least-privilege | ⚠️ recommended (fine-grained PAT) |
| Filesystem narrow + pinned | ⚠️ recommended |
| Only first-party / vetted servers | ✅ GitHub, Notion, MCP filesystem, Context7 (Upstash) |

---

## Primary sources
- MCP spec: https://modelcontextprotocol.io/specification (Tools, Resources, Transports, Lifecycle, Security Best Practices)
- FastMCP: https://gofastmcp.com (Tools, Resources, Context, Server, Deployment)
- Security: OWASP MCP Top 10 (https://owasp.org/www-project-mcp-top-10/); Trail of Bits "line jumping"; Invariant Labs tool poisoning; EscapeRoute CVE-2025-53109/53110 (Cymulate/Snyk)
- Context7: https://github.com/upstash/context7
