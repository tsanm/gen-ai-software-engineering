"""Application service for transactions (Tasks 1, 3, 4-C).

Owns the create use-case end to end -- validation, entity construction, persistence,
compliance review, and audit -- so the route handler stays a thin adapter. Filtering,
lookup, and export are delegated here too for a single, transport-agnostic entry point.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from src.errors import ApiError, ValidationProblem
from src.models import Status, Transaction, TransactionCreate, TxType
from src.models.store import TransactionStore
from src.services import calculations, currencies
from src.services.compliance import AuditLog, CompliancePolicy
from src.services.regions import Region
from src.utils.masking import mask_account
from src.validators import validate_transaction


class TransactionService:
    def __init__(
        self,
        store: TransactionStore,
        region: Region,
        audit: AuditLog,
        policy: CompliancePolicy,
        request_id: str | None = None,
    ) -> None:
        self._store = store
        self._region = region
        self._audit = audit
        self._policy = policy
        self._request_id = request_id

    def create(self, payload: TransactionCreate) -> Transaction:
        details = validate_transaction(payload, self._region)
        if details:
            raise ValidationProblem(details)

        txn = Transaction(
            id=str(uuid.uuid4()),
            fromAccount=payload.fromAccount,
            toAccount=payload.toAccount,
            amount=currencies.quantize(payload.currency, payload.amount),
            currency=payload.currency.upper(),
            type=payload.type,
            timestamp=datetime.now(timezone.utc),
            status=Status.completed,
        )
        self._store.add(txn)

        # Compliance review + audit trail (PII masked).
        flags = self._policy.review(txn.amount)
        meta = {
            "type": txn.type.value,
            "currency": txn.currency,
            "fromAccount": mask_account(txn.fromAccount),
            "toAccount": mask_account(txn.toAccount),
        }
        self._audit.record("transaction.created", txn.id, self._request_id, meta)
        if flags:
            self._audit.record(
                "compliance.flagged", txn.id, self._request_id, {**meta, "flags": flags})

        return txn

    def list(
        self,
        account_id: str | None = None,
        tx_type: TxType | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Transaction]:
        return calculations.filter_transactions(
            self._store.list(), account_id=account_id, tx_type=tx_type,
            date_from=date_from, date_to=date_to)

    def get(self, transaction_id: str) -> Transaction:
        txn = self._store.get(transaction_id)
        if txn is None:
            raise ApiError(404, "Transaction not found")
        return txn

    def export_csv(self) -> str:
        return calculations.transactions_to_csv(self._store.list())
