"""Custom MCP server (FastMCP) for Homework 5.

Exposes the contents of ``lorem-ipsum.md`` two ways:

* a **resource** — read-only, URI-addressed — registered under two URIs:
    - ``resource://lorem``                 → the default (30) words
    - ``resource://lorem/{word_count}``    → exactly ``word_count`` words
* a **tool** named ``read`` (model-invoked, name-addressed) with an optional ``word_count``.

Design / best-practice notes (see ../BEST_PRACTICES.md for sources):
* The source file is FIXED (``lorem-ipsum.md``) and there is **no path parameter**, so this
  server is immune by construction to path-traversal / symlink-escape attacks — there is no
  user-controlled path to canonicalize.
* ``word_count`` is validated and bounded (``ge=1``) so negative/zero/garbage values are
  rejected before any work runs.
* Errors intended for the caller are raised as ``ResourceError`` so the message survives
  ``mask_error_details=True``; unexpected internals are masked.
* Nothing is ever written to **stdout** (that would corrupt the stdio JSON-RPC stream);
  FastMCP routes its logging to stderr.
"""

from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError
from mcp.types import ToolAnnotations
from pydantic import Field

mcp = FastMCP(
    name="LoremServer",
    instructions=(
        "Serves lorem ipsum text. Use the `read` tool, or read the resource "
        "`resource://lorem` (default 30 words) / `resource://lorem/{word_count}` "
        "(exactly word_count words)."
    ),
    mask_error_details=True,
)

# Source file lives next to this script, regardless of the launch working directory.
LOREM_PATH = Path(__file__).parent / "lorem-ipsum.md"
DEFAULT_WORD_COUNT = 30
MAX_WORD_COUNT = 100_000  # generous DoS bound; the file is far smaller


def _read_words(word_count: int) -> str:
    """Return exactly ``word_count`` whitespace-separated words from lorem-ipsum.md.

    Raises ``ResourceError`` on an out-of-range count so the message reaches the caller
    even with error masking on.
    """
    if word_count < 1 or word_count > MAX_WORD_COUNT:
        raise ResourceError(f"word_count must be between 1 and {MAX_WORD_COUNT}")
    try:
        words = LOREM_PATH.read_text(encoding="utf-8").split()
    except FileNotFoundError:  # surface a clean message instead of a raw traceback
        raise ResourceError("lorem source file is missing")
    return " ".join(words[:word_count])


# --- Resource: bare URI returns the default (this is what makes "default 30" reachable) ---
@mcp.resource("resource://lorem", mime_type="text/plain")
def lorem_default() -> str:
    """Return the default (30) words from lorem-ipsum.md."""
    return _read_words(DEFAULT_WORD_COUNT)


# --- Resource: templated URI returns an explicit count ---
@mcp.resource("resource://lorem/{word_count}", mime_type="text/plain")
def lorem_by_count(word_count: int) -> str:
    """Return ``word_count`` words from lorem-ipsum.md (URI param arrives as a string)."""
    return _read_words(int(word_count))


# --- Tool named "read" (read-only, idempotent) ---
@mcp.tool(
    annotations=ToolAnnotations(
        title="Read Lorem Ipsum",
        readOnlyHint=True,
        idempotentHint=True,
    ),
)
def read(
    word_count: Annotated[
        int, Field(description="How many words to return", ge=1, le=MAX_WORD_COUNT)
    ] = DEFAULT_WORD_COUNT,
) -> str:
    """Read ``word_count`` words (default 30) from lorem-ipsum.md and return them."""
    return _read_words(word_count)


if __name__ == "__main__":
    # Default transport is stdio — exactly what Claude Code / Copilot expect.
    mcp.run()
