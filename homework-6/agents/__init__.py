"""Multi-agent banking transaction processing pipeline.

This package contains the cooperating agents that make up the pipeline:

* :mod:`agents.transaction_validator` -- structural and value validation.
* :mod:`agents.fraud_detector` -- risk scoring.
* :mod:`agents.compliance_checker` -- regulatory screening.
* :mod:`agents.settlement_processor` -- final settlement and fee calculation.
* :mod:`agents.reporting_agent` -- run summary generation.

Supporting infrastructure lives in :mod:`agents.common`.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "1.0.0"
