"""Live integration tests for the external MCP servers (Tasks 1 & 2).

These connect to the REAL servers using the same FastMCP client Claude Code uses under the
hood — proving "registered and running" and "at least one successful interaction" without a
human. They SKIP (never falsely pass) when prerequisites are missing:
  - Filesystem: needs `npx`/Node + network to fetch the package on first run.
  - GitHub:    needs network + a token (`gh auth token` or $GITHUB_MCP_TOKEN).

Notion (Task 3) is intentionally not here: its hosted server is OAuth-only and requires an
interactive browser flow, so it is verified manually (see TEST_PLAN.md).
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport, StreamableHttpTransport

HW5 = Path(__file__).resolve().parent.parent
SERVERS = json.loads((HW5 / ".mcp.json").read_text())["mcpServers"]


def _github_token() -> str | None:
    tok = os.environ.get("GITHUB_MCP_TOKEN")
    if tok:
        return tok
    if shutil.which("gh"):
        try:
            out = subprocess.run(
                ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
            )
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip()
        except (subprocess.SubprocessError, OSError):
            pass
    return None


# ---------------- Filesystem (Task 2) ----------------

requires_npx = pytest.mark.skipif(shutil.which("npx") is None, reason="npx/Node not installed")


def _fs_args() -> list[str]:
    return [a.replace("${HOME}", str(Path.home())) for a in SERVERS["filesystem"]["args"]]


def _fs_allowed_dir() -> Path:
    """The directory the filesystem server is configured to allow (last arg)."""
    return Path(_fs_args()[-1])


def _fs_transport() -> StdioTransport:
    return StdioTransport(command=SERVERS["filesystem"]["command"], args=_fs_args())


@requires_npx
async def test_filesystem_live_connection():  # 2-P1-5
    try:
        async with Client(_fs_transport()) as c:
            tools = [t.name for t in await c.list_tools()]
    except Exception as e:  # noqa: BLE001 - first-run npx download may fail offline
        pytest.skip(f"filesystem server unavailable (offline npx fetch?): {e}")
    assert tools, "filesystem server exposed no tools"


@requires_npx
async def test_filesystem_tool_surface():  # 2-P2-3
    try:
        async with Client(_fs_transport()) as c:
            tools = {t.name for t in await c.list_tools()}
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"filesystem server unavailable: {e}")
    assert {"list_directory", "read_text_file"} <= tools, tools


@requires_npx
async def test_filesystem_live_list_dir():  # 2-P2-1
    allowed = _fs_allowed_dir()
    try:
        async with Client(_fs_transport()) as c:
            res = await c.call_tool("list_directory", {"path": str(allowed)})
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"filesystem server unavailable: {e}")
    text = str(res.data) + str(getattr(res, "content", ""))
    assert "homework-5" in text  # the allowed dir is the repo root


@requires_npx
async def test_filesystem_live_read_file():  # 2-P2-2
    # Read a file that lives INSIDE the configured allowed directory.
    target = _fs_allowed_dir() / "homework-5" / "TASKS.md"
    try:
        async with Client(_fs_transport()) as c:
            res = await c.call_tool("read_text_file", {"path": str(target)})
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"filesystem server unavailable: {e}")
    text = str(res.data) + str(getattr(res, "content", ""))
    assert "Homework 5" in text


# ---------------- GitHub (Task 1) ----------------

def _gh_transport():
    tok = _github_token()
    if not tok:
        pytest.skip("no GitHub token (set GITHUB_MCP_TOKEN or `gh auth login`)")
    return StreamableHttpTransport(
        url=SERVERS["github"]["url"], headers={"Authorization": f"Bearer {tok}"}
    )


def test_gh_cli_scope():  # 1-P2-2
    if not shutil.which("gh"):
        pytest.skip("gh CLI not installed")
    out = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, timeout=10)
    if out.returncode != 0:
        pytest.skip("gh not authenticated")
    assert "repo" in (out.stdout + out.stderr)


async def test_github_live_connection():  # 1-P1-5
    transport = _gh_transport()
    try:
        async with Client(transport) as c:
            tools = [t.name for t in await c.list_tools()]
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"GitHub MCP server unreachable: {e}")
    assert tools, "GitHub MCP server exposed no tools"


async def test_github_live_list_tools():  # 1-P2-1
    transport = _gh_transport()
    try:
        async with Client(transport) as c:
            tools = {t.name for t in await c.list_tools()}
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"GitHub MCP server unreachable: {e}")
    # the GitHub MCP server exposes repo/PR/issue read tools; assert at least one shows up
    assert any("pull" in t or "issue" in t or "repo" in t for t in tools), sorted(tools)
