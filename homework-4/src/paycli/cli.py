"""paycli command-line entry point: ``python -m paycli <command> ...``."""

from __future__ import annotations

import argparse

from . import transactions
from .report import export_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="paycli", description="Tiny payments/transactions CLI.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_total = sub.add_parser("total", help="sum transaction amounts")
    p_total.add_argument("amounts", type=float, nargs="*")

    p_avg = sub.add_parser("average", help="average transaction amount")
    p_avg.add_argument("amounts", type=float, nargs="*")

    p_limit = sub.add_parser("check-limit", help="check a spend against a daily limit")
    p_limit.add_argument("spent", type=float)
    p_limit.add_argument("amount", type=float)
    p_limit.add_argument("limit", type=float)

    p_export = sub.add_parser("export", help="export a file into report.txt")
    p_export.add_argument("path")

    args = parser.parse_args(argv)

    if args.cmd == "total":
        print(transactions.total(args.amounts))
    elif args.cmd == "average":
        print(transactions.average_transaction(args.amounts))
    elif args.cmd == "check-limit":
        print(transactions.is_within_daily_limit(args.spent, args.amount, args.limit))
    elif args.cmd == "export":
        return export_report(args.path)
    return 0
