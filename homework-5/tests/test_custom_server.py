"""Task 4 — Custom FastMCP server: end-to-end behavioural tests.

These exercise the real MCP protocol via the FastMCP in-memory client, plus one test that
launches `server.py` as an actual stdio subprocess (proving the `.mcp.json` startup command
works). No external network or accounts required — this is the fully-provable core.
"""
import sys
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

import server as srv

CUSTOM_DIR = Path(__file__).resolve().parent.parent / "custom-mcp-server"
LOREM_WORDS = (CUSTOM_DIR / "lorem-ipsum.md").read_text(encoding="utf-8").split()


@pytest.fixture
async def client():
    async with Client(srv.mcp) as c:
        yield c


# ---------------- P1 ----------------

def test_server_is_fastmcp():  # 4-P1-1
    from fastmcp import FastMCP
    assert isinstance(srv.mcp, FastMCP)


async def test_read_tool_registered(client):  # 4-P1-2
    names = [t.name for t in await client.list_tools()]
    assert "read" in names, f"expected a tool named 'read', got {names}"


async def test_resource_registered(client):  # 4-P1-3
    templates = [str(t.uriTemplate) for t in await client.list_resource_templates()]
    assert "resource://lorem/{word_count}" in templates, templates


async def test_read_default_30_words(client):  # 4-P1-4
    result = await client.call_tool("read", {})
    assert len(result.data.split()) == 30


async def test_read_matches_source(client):  # 4-P1-5
    result = await client.call_tool("read", {"word_count": 30})
    assert result.data == " ".join(LOREM_WORDS[:30])


async def test_server_runs_as_stdio_subprocess():  # 4-P1-6
    """Launch `python server.py` exactly as .mcp.json does, over real stdio."""
    transport = StdioTransport(command=sys.executable, args=[str(CUSTOM_DIR / "server.py")])
    async with Client(transport) as c:
        names = [t.name for t in await c.list_tools()]
        assert "read" in names
        result = await c.call_tool("read", {"word_count": 7})
        assert len(result.data.split()) == 7


# ---------------- P2 ----------------

@pytest.mark.parametrize("n", [1, 5, 10, 25])
async def test_read_arbitrary_counts(client, n):  # 4-P2-1
    result = await client.call_tool("read", {"word_count": n})
    assert result.data.split() == LOREM_WORDS[:n]


async def test_resource_word_count(client):  # 4-P2-2
    result = await client.read_resource("resource://lorem/15")
    assert len(result[0].text.split()) == 15


async def test_tool_resource_agree(client):  # 4-P2-3
    tool_out = (await client.call_tool("read", {"word_count": 12})).data
    res_out = (await client.read_resource("resource://lorem/12"))[0].text
    assert tool_out == res_out


async def test_read_word_count_optional(client):  # 4-P2-4
    tool = next(t for t in await client.list_tools() if t.name == "read")
    required = tool.inputSchema.get("required", [])
    assert "word_count" not in required, "word_count must be optional"


async def test_read_count_exceeds_file(client):  # 4-P2-5
    result = await client.call_tool("read", {"word_count": 10_000})
    assert result.data.split() == LOREM_WORDS  # all words, no crash


# ---------------- Best-practice hardening (added after MCP best-practices audit) ----------------

async def test_resource_default_reachable(client):  # BP-P0-1: "default 30" via the resource
    """The bare resource URI must return the default (30) words — the templated path
    placeholder alone can never exercise the default, which the assignment requires."""
    result = await client.read_resource("resource://lorem")
    assert len(result[0].text.split()) == 30


async def test_resource_default_lists(client):  # BP-P1-1
    uris = [str(r.uri) for r in await client.list_resources()]
    assert "resource://lorem" in uris


async def test_read_rejects_zero(client):  # BP-P0-2: input validation (word_count >= 1)
    with pytest.raises(Exception):
        await client.call_tool("read", {"word_count": 0})


async def test_read_rejects_negative(client):  # BP-P0-2
    with pytest.raises(Exception):
        await client.call_tool("read", {"word_count": -5})


async def test_resource_rejects_zero(client):  # BP-P1-2
    with pytest.raises(Exception):
        await client.read_resource("resource://lorem/0")


async def test_read_is_read_only_annotated(client):  # BP-P1-3
    tool = next(t for t in await client.list_tools() if t.name == "read")
    ann = tool.annotations
    assert ann is not None and ann.readOnlyHint is True


async def test_read_param_has_description(client):  # BP-P1-4
    tool = next(t for t in await client.list_tools() if t.name == "read")
    prop = tool.inputSchema["properties"]["word_count"]
    assert prop.get("description") and prop.get("minimum") == 1
