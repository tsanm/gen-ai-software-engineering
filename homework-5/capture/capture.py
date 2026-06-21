"""Capture REAL MCP request/response evidence and render a browser report.

Connects to each configured MCP server via the FastMCP client (the same protocol layer
Claude Code uses), performs representative calls, and writes a self-contained HTML report to
docs/screenshots/evidence.html — one card per server, ready to screenshot.

Run (from homework-5/, inside the venv):
    python capture/capture.py [--no-open]

Notion is intentionally skipped: its hosted server is OAuth-only (interactive browser), so it
is captured manually. Everything shown here is genuine server output — nothing is mocked.
"""
import asyncio
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport, StreamableHttpTransport

HW5 = Path(__file__).resolve().parent.parent
CONFIG = json.loads((HW5 / ".mcp.json").read_text())["mcpServers"]
OUT = HW5 / "docs" / "screenshots" / "evidence.html"

# Which servers to capture headlessly, and which spec screenshot each card maps to.
CARDS = {
    "github": "github-mcp-result.png",
    "filesystem": "filesystem-mcp-result.png",
    "lorem": "custom-mcp-read-tool-result.png",
    "notion": "jira-or-notion-mcp-result.png",
    "context7": "context7-result.png",  # optional enhancement
}


def expand(value: str) -> str:
    """Expand ${VAR} and ${VAR:-default}; special-case the GitHub token via `gh`."""

    def repl(m):
        var, default = m.group(1), m.group(3)
        val = os.environ.get(var)
        if not val and var == "GITHUB_MCP_TOKEN" and shutil.which("gh"):
            out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
            val = out.stdout.strip() if out.returncode == 0 else None
        return val if val else (default or "")

    return re.sub(r"\$\{(\w+)(:-([^}]*))?\}", repl, value)


def make_transport(name: str):
    s = CONFIG[name]
    if s["type"] == "stdio":
        args = [expand(a) for a in s["args"]]
        env = None
        if s.get("env"):
            # stdio subprocesses do NOT inherit the shell env, so pass it explicitly.
            env = {k: expand(v) for k, v in s["env"].items()}
            env["PATH"] = os.environ.get("PATH", "")
            env["HOME"] = os.environ.get("HOME", "")
        return StdioTransport(command=s["command"], args=args, env=env)
    headers = {k: expand(v) for k, v in s.get("headers", {}).items() if expand(v)}
    return StreamableHttpTransport(url=expand(s["url"]), headers=headers)


def _notion_title(page: dict) -> str:
    for v in (page.get("properties") or {}).values():
        if v.get("type") == "title":
            return "".join(t.get("plain_text", "") for t in v.get("title", [])) or "(untitled)"
    return "(untitled)"


def to_text(result) -> str:
    """Best-effort readable rendering of a tool/resource result."""
    data = getattr(result, "data", None)
    if data is not None:
        return data if isinstance(data, str) else json.dumps(data, default=str)
    content = getattr(result, "content", None)
    if content:
        parts = [getattr(c, "text", None) or str(c) for c in content]
        return "\n".join(parts)
    return str(result)


def fs_allowed_dir() -> Path:
    return Path([expand(a) for a in CONFIG["filesystem"]["args"]][-1])


# ---- Per-server demo steps: (request-dict, async call -> response-text) ----

async def demo_lorem(c):
    steps = []
    tools = await c.list_tools()
    steps.append(({"method": "tools/list"}, json.dumps([t.name for t in tools])))
    r = await c.call_tool("read", {"word_count": 10})
    steps.append(({"method": "tools/call", "name": "read", "arguments": {"word_count": 10}}, to_text(r)))
    rr = await c.read_resource("resource://lorem")
    steps.append(({"method": "resources/read", "uri": "resource://lorem"}, rr[0].text))
    rr2 = await c.read_resource("resource://lorem/15")
    steps.append(({"method": "resources/read", "uri": "resource://lorem/15"}, rr2[0].text))
    return steps


async def demo_filesystem(c):
    steps = []
    tools = await c.list_tools()
    steps.append(({"method": "tools/list"}, json.dumps([t.name for t in tools])))
    allowed = str(fs_allowed_dir())
    r = await c.call_tool("list_directory", {"path": allowed})
    steps.append(({"method": "tools/call", "name": "list_directory", "arguments": {"path": allowed}}, to_text(r)[:500]))
    f = str(fs_allowed_dir() / "homework-5" / "TASKS.md")
    r2 = await c.call_tool("read_text_file", {"path": f})
    steps.append(({"method": "tools/call", "name": "read_text_file", "arguments": {"path": f}}, to_text(r2)[:400]))
    return steps


async def demo_github(c):
    steps = []
    tools = await c.list_tools()
    names = [t.name for t in tools]
    steps.append(({"method": "tools/list"}, f"// {len(names)} tools — " + json.dumps(names)[:600] + " …"))
    for tool in ("get_me", "list_pull_requests", "search_repositories"):
        if tool in names:
            try:
                args = {"query": "user:tsanm"} if tool == "search_repositories" else {}
                r = await c.call_tool(tool, args)
                steps.append(({"method": "tools/call", "name": tool, "arguments": args}, to_text(r)[:700]))
                break
            except Exception as e:  # noqa: BLE001
                steps.append(({"method": "tools/call", "name": tool}, f"(skipped: {e})"))
    return steps


async def demo_context7(c):
    steps = []
    tools = await c.list_tools()
    names = [t.name for t in tools]
    steps.append(({"method": "tools/list"}, json.dumps(names)))
    for tool in ("resolve-library-id", "resolve_library_id"):
        if tool in names:
            args = {"libraryName": "fastmcp", "query": "how to define a tool and resource"}
            try:
                r = await c.call_tool(tool, args)
                steps.append(({"method": "tools/call", "name": tool, "arguments": args}, to_text(r)[:700]))
            except Exception as e:  # noqa: BLE001
                steps.append(({"method": "tools/call", "name": tool, "arguments": args}, f"(skipped: {e})"))
            break
    return steps


async def demo_notion(c):
    steps = []
    who = await c.call_tool("API-get-self", {})
    steps.append(({"method": "tools/call", "name": "API-get-self"}, to_text(who)[:300]))
    # "last 5" most-recently-edited pages/tickets the integration can see (page IDs only).
    args = {"sort": {"direction": "descending", "timestamp": "last_edited_time"}, "page_size": 5}
    r = await c.call_tool("API-post-search", args)
    try:
        data = json.loads(to_text(r))
        rows = [
            {"id": p.get("id"), "title": _notion_title(p), "last_edited_time": p.get("last_edited_time")}
            for p in data.get("results", [])
        ]
        resp = json.dumps(rows, indent=2)
    except Exception:  # noqa: BLE001
        resp = to_text(r)[:900]
    steps.append(({"method": "tools/call", "name": "API-post-search", "arguments": args}, resp))
    return steps


DEMOS = {
    "lorem": demo_lorem,
    "filesystem": demo_filesystem,
    "github": demo_github,
    "context7": demo_context7,
    "notion": demo_notion,
}


async def capture_one(name: str) -> dict:
    card = {"name": name, "transport": CONFIG[name]["type"], "shot": CARDS[name]}
    try:
        async with Client(make_transport(name)) as c:
            tools = await c.list_tools()
            card["status"] = f"Connected · {len(tools)} tools"
            card["ok"] = True
            card["steps"] = await DEMOS[name](c)
    except Exception as e:  # noqa: BLE001
        card["status"] = f"FAILED: {e}"
        card["ok"] = False
        card["steps"] = []
    return card


def render(cards: list) -> str:
    css = """
    body{font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:24px;background:#0d1117;color:#c9d1d9}
    h1{font-size:20px}.sub{color:#8b949e;margin-bottom:20px}
    .card{background:#161b22;border:1px solid #30363d;border-radius:10px;margin:0 0 16px;padding:14px;break-inside:avoid}
    .hd{display:flex;align-items:center;gap:10px;margin-bottom:3px}
    .name{font-size:16px;font-weight:600}.tag{font-size:11px;background:#21262d;border:1px solid #30363d;border-radius:20px;padding:2px 10px;color:#8b949e}
    .badge{margin-left:auto;font-size:12px;font-weight:600;padding:3px 10px;border-radius:20px}
    .ok{background:#0f5132;color:#3fb950}.bad{background:#5c1a1a;color:#f85149}
    .shot{font-size:11px;color:#6e7681;margin:1px 0 8px}
    .step{margin:8px 0}.lbl{font-size:11px;letter-spacing:.3px;color:#58a6ff;margin-bottom:3px}
    .lbl.resp{color:#3fb950;text-transform:uppercase}
    .lbl code{color:#c9d1d9;background:#0d1117;border:1px solid #21262d;border-radius:4px;padding:1px 6px;font:11px/1.4 SFMono-Regular,Consolas,monospace}
    pre{background:#0d1117;border:1px solid #21262d;border-radius:6px;padding:8px;overflow:auto;white-space:pre-wrap;word-break:break-word;margin:0;font:11.5px/1.4 SFMono-Regular,Consolas,monospace}
    """
    rows = []
    for c in cards:
        badge = "ok" if c["ok"] else "bad"
        steps = []
        for req, resp in c["steps"]:
            steps.append(
                f'<div class="step">'
                f'<div class="lbl">▶ Request <code>{html.escape(json.dumps(req))}</code></div>'
                f'<div class="lbl resp">◀ Response</div>'
                f'<pre>{html.escape(resp)}</pre></div>'
            )
        rows.append(
            f'<div class="card"><div class="hd"><span class="name">{html.escape(c["name"])}</span>'
            f'<span class="tag">{c["transport"]}</span>'
            f'<span class="badge {badge}">{html.escape(c["status"])}</span></div>'
            f'<div class="shot">screenshot this card → docs/screenshots/{c["shot"]}</div>'
            f'{"".join(steps)}</div>'
        )
    return (
        f"<!doctype html><meta charset=utf-8><title>HW5 MCP evidence</title>"
        f"<style>{css}</style><h1>Homework 5 — MCP call evidence (real request/response)</h1>"
        f'<div class="sub">Generated by capture/capture.py via the FastMCP client. '
        f"Notion is captured manually (OAuth). Snip each card into the named file.</div>"
        f'{"".join(rows)}'
    )


async def main():
    cards = [await capture_one(n) for n in CARDS]
    OUT.write_text(render(cards), encoding="utf-8")
    print(f"\nReport: {OUT}")
    for c in cards:
        mark = "✓" if c["ok"] else "✗"
        print(f"  {mark} {c['name']:12} {c['status']}")
    if "--no-open" not in sys.argv and shutil.which("open"):
        subprocess.run(["open", str(OUT)])


if __name__ == "__main__":
    asyncio.run(main())
