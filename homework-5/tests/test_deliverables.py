"""Static / config correctness across all four tasks + deliverables.

These are real, runnable assertions over the committed files: structure, .mcp.json shape,
documentation content, and a secret-leak scan. No network required.
"""
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest

HW5 = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    return (HW5 / rel).read_text(encoding="utf-8")


# ============ Deliverables & structure ============

EXPECTED_FILES = [
    "README.md",
    "HOWTORUN.md",
    ".mcp.json",
    "custom-mcp-server/server.py",
    "custom-mcp-server/lorem-ipsum.md",
    "custom-mcp-server/requirements.txt",
]


@pytest.mark.parametrize("rel", EXPECTED_FILES)
def test_expected_structure_exists(rel):  # D-P1-2
    assert (HW5 / rel).is_file(), f"missing required file: {rel}"


def test_screenshots_dir_exists():  # D-P2-2
    assert (HW5 / "docs" / "screenshots").is_dir()


# Exact screenshot filenames from the TASKS.md "Expected Project Structure" block.
EXPECTED_SCREENSHOTS = [
    "github-mcp-result.png",
    "filesystem-mcp-result.png",
    "jira-or-notion-mcp-result.png",
    "custom-mcp-read-tool-result.png",
]


def test_screenshot_names_match_spec():  # D-P2-3 (naming half — automatable)
    """The placeholder doc must reference EXACTLY the spec's four screenshot names."""
    gitkeep = read("docs/screenshots/.gitkeep")
    for name in EXPECTED_SCREENSHOTS:
        assert name in gitkeep, f"spec screenshot name not documented: {name}"
    # the off-spec name must only ever appear as a substring of the jira-or-notion spec name
    assert gitkeep.count("notion-mcp-result.png") == gitkeep.count(
        "jira-or-notion-mcp-result.png"
    )


# Optional bonus screenshots (enhancements beyond the required four).
ALLOWED_BONUS_SCREENSHOTS = ["context7-result.png"]


def test_no_offspec_screenshot_files():  # guards future captures
    allowed = set(EXPECTED_SCREENSHOTS) | set(ALLOWED_BONUS_SCREENSHOTS)
    pngs = [p.name for p in (HW5 / "docs" / "screenshots").glob("*.png")]
    bad = [n for n in pngs if n not in allowed]
    assert not bad, f"off-spec screenshot filenames: {bad}"


def test_required_screenshots_present():  # the captured evidence actually exists
    shots = HW5 / "docs" / "screenshots"
    # Notion is captured manually/separately; assert the three headless-captured ones exist.
    for name in ("github-mcp-result.png", "filesystem-mcp-result.png", "custom-mcp-read-tool-result.png"):
        assert (shots / name).is_file(), f"missing screenshot: {name}"


def test_tasks_spec_screenshot_names_are_authoritative():
    """Cross-check our EXPECTED_SCREENSHOTS against the actual TASKS.md spec text."""
    tasks = read("TASKS.md")
    for name in EXPECTED_SCREENSHOTS:
        assert name in tasks, f"{name} not found in TASKS.md spec"


REQUIRED_SERVERS = {"github", "filesystem", "notion", "lorem"}


def test_all_four_servers_registered(servers):  # D-P1-1
    # the four required servers must be present; extras (e.g. context7) are allowed
    assert REQUIRED_SERVERS <= set(servers), f"missing: {REQUIRED_SERVERS - set(servers)}"


def test_context7_enhancement_well_formed(servers):  # BP-P2-1 (optional 5th server)
    if "context7" not in servers:
        pytest.skip("context7 enhancement not configured")
    c7 = servers["context7"]
    assert c7["type"] == "http"
    assert urlparse(c7["url"]).hostname == "mcp.context7.com"


def test_readme_has_author():  # D-P1-3
    assert "Anton Tsiatsko" in read("README.md")


def test_lorem_has_enough_words():  # D-P2-1
    assert len(read("custom-mcp-server/lorem-ipsum.md").split()) >= 30


# ============ Task 1 — GitHub ============

def test_github_uses_official_server(servers):  # 1-P1-1
    assert servers["github"]["url"] == "https://api.githubcopilot.com/mcp/"


def test_github_transport_http(servers):  # 1-P1-2
    assert servers["github"]["type"] == "http"


def test_github_auth_header_present(servers):  # 1-P1-3
    auth = servers["github"]["headers"]["Authorization"]
    assert auth.startswith("Bearer ")


def test_github_entry_shape(servers):  # 1-P2-3
    assert {"type", "url", "headers"} <= set(servers["github"])


def test_howto_documents_github_token():  # 1-P2-5
    assert "gh auth token" in read("HOWTORUN.md")
    assert "GITHUB_MCP_TOKEN" in read("HOWTORUN.md")


# ============ Task 2 — Filesystem ============

def test_filesystem_official_package(servers):  # 2-P1-1
    assert "@modelcontextprotocol/server-filesystem" in servers["filesystem"]["args"]


def test_filesystem_has_path_arg(servers):  # 2-P1-2
    args = servers["filesystem"]["args"]
    # last arg(s) after the package name are directory paths
    idx = args.index("@modelcontextprotocol/server-filesystem")
    assert len(args) > idx + 1, "no directory path configured"


def test_filesystem_path_exists(servers):  # 2-P1-3
    args = servers["filesystem"]["args"]
    idx = args.index("@modelcontextprotocol/server-filesystem")
    path = Path(args[idx + 1].replace("${HOME}", str(Path.home())))
    assert path.is_dir(), f"configured filesystem path does not exist: {path}"


def test_filesystem_transport(servers):  # 2-P1-4
    fs = servers["filesystem"]
    assert fs["type"] == "stdio" and fs["command"] == "npx"


def test_filesystem_npx_yes_flag(servers):  # 2-P2-5
    assert "-y" in servers["filesystem"]["args"]


# ============ Task 3 — Notion ============

def test_notion_official_server(servers):  # 3-P1-1
    assert "@notionhq/notion-mcp-server" in servers["notion"]["args"]


def test_notion_transport(servers):  # 3-P1-3
    n = servers["notion"]
    assert n["type"] == "stdio" and n["command"] == "npx"


def test_notion_token_via_env(servers):  # 3-P1-2 (credentials, no literal secret)
    assert servers["notion"]["env"]["NOTION_TOKEN"].startswith("${")


def test_notion_oauth_documented():  # 3-P1-2
    howto = read("HOWTORUN.md").lower()
    assert "oauth" in howto and "/mcp" in read("HOWTORUN.md")


def test_notion_bug_query_documented():  # 3-P1-4
    howto = read("HOWTORUN.md").lower()
    assert "last 5 bugs" in howto


def test_notion_redaction_note():  # 3-P2-1
    text = (read("HOWTORUN.md") + read("README.md")).lower()
    assert "page id" in text and "sensitive" in text


def test_notion_bug_property_note():  # 3-P2-5
    text = (read("HOWTORUN.md") + read("README.md")).lower()
    assert "type = bug" in text or "type is bug" in text or "bug property" in text


# ============ Task 4 — docs/deps (behaviour tested in test_custom_server.py) ============

def test_fastmcp_in_requirements():  # 4-P2-6
    assert re.search(r"fastmcp", read("custom-mcp-server/requirements.txt"))


def test_readme_explains_resources_and_tools():  # 4-P2-7
    rd = read("README.md")
    assert "Resources" in rd and "Tools" in rd
    # both must actually be defined, not just mentioned
    assert re.search(r"Resources.*read", rd, re.S)
    assert re.search(r"Tools.*(action|call|invoke)", rd, re.S | re.I)


def test_howto_has_all_sections():  # 4-P2-8
    howto = read("HOWTORUN.md").lower()
    for section in ("install", "run", "connect", "test"):
        assert section in howto, f"HOWTORUN missing '{section}'"


def test_lorem_entry_points_to_custom_server(servers):  # 4-P1-6 (config half)
    lorem = servers["lorem"]
    assert lorem["command"] == "python"
    assert any("server.py" in a for a in lorem["args"])


# ============ Security: no committed secrets (1-P1-4, 3-P2-4) ============

SECRET_PATTERNS = [
    r"ghp_[A-Za-z0-9]{20,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"gho_[A-Za-z0-9]{20,}",
    r"ntn_[A-Za-z0-9]{20,}",
    r"secret_[A-Za-z0-9]{20,}",
]


def test_no_secrets_committed():
    offenders = []
    for path in HW5.rglob("*"):
        # .env holds the local token but is gitignored (never committed) — skip it.
        if (
            not path.is_file()
            or ".venv" in path.parts
            or path.name == ".env"
            or path.suffix in {".png", ".pyc"}
        ):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pat in SECRET_PATTERNS:
            if re.search(pat, content):
                offenders.append((str(path.relative_to(HW5)), pat))
    assert not offenders, f"possible committed secrets: {offenders}"
