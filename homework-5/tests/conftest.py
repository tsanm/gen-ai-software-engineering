"""Shared fixtures/paths for the Homework 5 test suite."""
import sys
from pathlib import Path

import pytest

HW5_DIR = Path(__file__).resolve().parent.parent
CUSTOM_DIR = HW5_DIR / "custom-mcp-server"

# Make `import server` work regardless of where pytest is invoked from.
sys.path.insert(0, str(CUSTOM_DIR))


@pytest.fixture(scope="session")
def hw5_dir() -> Path:
    return HW5_DIR


@pytest.fixture(scope="session")
def custom_dir() -> Path:
    return CUSTOM_DIR


@pytest.fixture(scope="session")
def mcp_config(hw5_dir) -> dict:
    import json

    return json.loads((hw5_dir / ".mcp.json").read_text())


@pytest.fixture(scope="session")
def servers(mcp_config) -> dict:
    return mcp_config["mcpServers"]
