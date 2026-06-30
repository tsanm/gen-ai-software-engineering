"""Shared infrastructure for the multi-agent banking pipeline.

This module centralises the cross-cutting concerns every agent relies on:

* **Money** -- monetary amounts are parsed and rounded with
  :class:`decimal.Decimal` using ``ROUND_HALF_UP``. ``float`` is never used
  for money anywhere in the pipeline.
* **ISO 4217** -- a curated set of supported currency codes plus their
  minor-unit (decimal-place) exponents, used for correct quantisation.
* **Message protocol** -- the file-based JSON envelope agents exchange through
  the ``shared/`` directories, with helpers to build, read and write them.
* **Audit logging** -- structured, PII-safe audit lines carrying an ISO-8601
  timestamp, the agent name, the transaction id and an outcome.
* **PII masking** -- account numbers and free-text descriptions are masked
  before they ever reach a log line.

Keeping all of this in one place means the agents stay small and the
invariants (money precision, no plaintext PII) are enforced consistently.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "SUPPORTED_CURRENCIES",
    "AgentError",
    "Message",
    "PipelinePaths",
    "configure_audit_logger",
    "iso_now",
    "load_config",
    "mask_account",
    "mask_text",
    "new_message_id",
    "parse_money",
    "quantize_money",
]

# --- Errors ---------------------------------------------------------------


class AgentError(Exception):
    """Raised when an agent cannot process a message it received."""


# --- Config (single source of runtime numbers) ----------------------------

#: Default location of the declarative pipeline config, relative to the repo
#: root (the parent of this ``agents/`` package).
DEFAULT_CONFIG_PATH: Path = Path(__file__).resolve().parent.parent / "pipeline.config.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load the declarative pipeline config (``pipeline.config.json``).

    Thresholds, the fee rate, the currency allow-list, the agent order and the
    coverage floor all live in this file so behaviour can be tuned without code
    changes. The agents and the integrator read from the returned mapping; this
    function is the only place that knows the on-disk shape.
    """

    config_path = path or DEFAULT_CONFIG_PATH
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AgentError("pipeline.config.json must contain a JSON object")
    return data


# --- ISO 4217 -------------------------------------------------------------

#: Supported ISO 4217 currency codes mapped to their minor-unit exponent
#: (the number of decimal places the currency uses), sourced from
#: ``pipeline.config.json`` so the allow-list is config-driven. ``XYZ`` is
#: intentionally absent so the validator rejects it.
SUPPORTED_CURRENCIES: dict[str, int] = load_config()["currencies"]


# --- Time helpers ---------------------------------------------------------


def iso_now() -> str:
    """Return the current UTC time as an ISO-8601 string with a ``Z`` suffix."""

    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_message_id() -> str:
    """Return a fresh UUID4 string for use as a message identifier."""

    return str(uuid.uuid4())


# --- Money handling -------------------------------------------------------


def parse_money(raw: Any) -> Decimal:
    """Parse a raw amount into a :class:`~decimal.Decimal`.

    The amount is always read from a string (or int) to avoid binary
    floating-point error. Passing a ``float`` is rejected outright because it
    would silently introduce imprecision before we ever reach this function.

    Raises:
        AgentError: if the value is a ``float`` or cannot be parsed.
    """

    if isinstance(raw, float):
        raise AgentError("monetary amounts must not be provided as float")
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:  # pragma: no cover - thin
        raise AgentError(f"invalid monetary amount: {raw!r}") from exc


def quantize_money(amount: Decimal, currency: str) -> Decimal:
    """Quantise ``amount`` to the minor units of ``currency``.

    Uses ``ROUND_HALF_UP`` -- the rounding convention expected for retail and
    settlement money math, where 0.5 always rounds away from zero.
    """

    exponent = SUPPORTED_CURRENCIES.get(currency, 2)
    quantum = Decimal(1).scaleb(-exponent)
    return amount.quantize(quantum, rounding=ROUND_HALF_UP)


# --- PII masking ----------------------------------------------------------


def mask_account(account: str) -> str:
    """Mask an account identifier, keeping only the last two characters.

    ``"ACC-1001"`` becomes ``"****01"``. Empty input yields ``"****"``.
    """

    if not account:
        return "****"
    tail = account[-2:]
    return f"****{tail}"


def mask_text(text: str, keep: int = 4) -> str:
    """Mask free-text (e.g. a description) that may contain sensitive detail."""

    if not text:
        return ""
    visible = text[:keep]
    return f"{visible}{'*' * max(len(text) - keep, 0)}"


# --- Audit logging --------------------------------------------------------


def configure_audit_logger(log_path: Path | None = None) -> logging.Logger:
    """Configure and return the shared ``pipeline.audit`` logger.

    Each audit line is ``<iso-timestamp> <agent> <txn-id> <outcome> ...`` and
    is, by contract, free of plaintext PII (callers must pass masked values).
    The logger is idempotent: repeated calls do not stack handlers.
    """

    logger = logging.getLogger("pipeline.audit")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter("%(message)s")
    has_stream = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    if not has_stream:
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        logger.addHandler(stream)

    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        already = any(
            isinstance(h, logging.FileHandler)
            and Path(getattr(h, "baseFilename", "")) == log_path.resolve()
            for h in logger.handlers
        )
        if not already:
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def audit(
    logger: logging.Logger,
    agent: str,
    transaction_id: str,
    outcome: str,
    detail: str = "",
) -> None:
    """Emit a single structured, PII-safe audit line."""

    line = f"{iso_now()} agent={agent} txn={transaction_id} outcome={outcome}"
    if detail:
        line = f"{line} detail={detail}"
    logger.info(line)


# --- Pipeline directory layout -------------------------------------------


@dataclass(frozen=True)
class PipelinePaths:
    """Resolved locations of the file-based message-bus directories."""

    root: Path
    input: Path
    processing: Path
    output: Path
    results: Path

    @classmethod
    def create(cls, root: Path) -> PipelinePaths:
        """Create (and return) all ``shared/`` sub-directories under ``root``."""

        paths = cls(
            root=root,
            input=root / "input",
            processing=root / "processing",
            output=root / "output",
            results=root / "results",
        )
        for directory in (paths.input, paths.processing, paths.output, paths.results):
            directory.mkdir(parents=True, exist_ok=True)
        return paths


# --- Message envelope -----------------------------------------------------


@dataclass
class Message:
    """The standard JSON envelope agents exchange via the shared directories.

    The wire format matches the specification exactly::

        {
          "message_id": "uuid4-string",
          "timestamp": "2026-03-16T10:00:00Z",
          "source_agent": "transaction_validator",
          "target_agent": "fraud_detector",
          "message_type": "transaction",
          "data": { ... }
        }
    """

    source_agent: str
    target_agent: str
    message_type: str
    data: dict[str, Any]
    message_id: str = field(default_factory=new_message_id)
    timestamp: str = field(default_factory=iso_now)

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical dictionary form of the envelope."""

        return {
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "message_type": self.message_type,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Message:
        """Build a :class:`Message` from a parsed envelope dictionary."""

        required = {
            "message_id",
            "timestamp",
            "source_agent",
            "target_agent",
            "message_type",
            "data",
        }
        missing = required - payload.keys()
        if missing:
            raise AgentError(f"message missing fields: {sorted(missing)}")
        return cls(
            message_id=str(payload["message_id"]),
            timestamp=str(payload["timestamp"]),
            source_agent=str(payload["source_agent"]),
            target_agent=str(payload["target_agent"]),
            message_type=str(payload["message_type"]),
            data=dict(payload["data"]),
        )

    def write(self, directory: Path, name: str | None = None) -> Path:
        """Serialise the envelope to ``directory`` and return the file path."""

        directory.mkdir(parents=True, exist_ok=True)
        filename = name or f"{self.data.get('transaction_id', self.message_id)}.json"
        target = directory / filename
        target.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=False),
            encoding="utf-8",
        )
        return target


def read_message(path: Path) -> Message:
    """Read and parse a :class:`Message` from ``path``."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    return Message.from_dict(payload)
