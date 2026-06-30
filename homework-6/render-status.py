#!/usr/bin/env python3
"""render-status.py [RUN_DIR]

Write ``<RUN_DIR>/pipeline-status.html`` -- a self-contained (no-CDN) status
board for the multi-agent banking pipeline, mirroring the homework-4 board:
the agent flow as linked boxes, a per-transaction table, and links to every
run artifact (results, summary, manifest, audit log, agent sources, PR).

Usage:
    python render-status.py                 # newest run under shared/runs/
    python render-status.py shared/runs/run-2026-06-22T08-52-34Z
    PR_URL=https://github.com/.../pull/6 python render-status.py
"""

from __future__ import annotations

# HTML/CSS template lines are intentionally long; line-length is not meaningful here.
# ruff: noqa: E501
import json
import os
import sys
from html import escape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "shared" / "runs"
RESULTS = ROOT / "shared" / "results"

# stage key | label | one-line role  (order matches manifest.stage_order)
STAGES = [
    ("transaction_validator", "transaction-validator", "schema · currency · amount"),
    ("fraud_detector", "fraud-detector", "risk score · band"),
    ("compliance_checker", "compliance-checker", "AML · sanctions"),
    ("settlement_processor", "settlement-processor", "fees · net amount"),
    ("reporting_agent", "reporting-agent", "finalise · write results"),
]

STATUS_CLASS = {"settled": "settled", "held": "held", "rejected": "rejected"}


def _latest_run() -> Path:
    runs = sorted(p for p in RUNS.glob("run-*") if p.is_dir())
    if not runs:
        sys.exit("no run folders under shared/runs/ -- run: python integrator.py")
    return runs[-1]


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _link(rel: str, label: str, *, base: Path) -> str:
    """Anchor if the target exists, else a dimmed span."""
    exists = (base / rel).exists() if not rel.startswith(("http", "..")) else True
    if exists:
        return f'<a href="{escape(rel)}">{escape(label)}</a>'
    return f'<span class=dim>{escape(label)}</span>'


def main() -> None:
    run = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _latest_run()
    out = run / "pipeline-status.html"
    rel = os.path.relpath(ROOT, run)  # run folder -> homework-6 root
    pr_url = os.environ.get("PR_URL", "")

    manifest = _load(run / "manifest.json")
    summary = _load(RESULTS / "_summary.json")
    by_status = summary.get("by_status", {})
    total = summary.get("total_transactions", 0)
    order = manifest.get("stage_order", [k for k, _, _ in STAGES])

    # ---- agent flow boxes -------------------------------------------------
    boxes = ""
    for i, key in enumerate(order):
        label, role = next(((lab, rol) for k, lab, rol in STAGES if k == key), (key, ""))
        src = f"{rel}/agents/{key}.py"
        boxes += (
            f'<div class="box done"><span class="n">{i + 1}</span> {escape(label)}'
            f'<br><small>{escape(role)} · done</small>'
            f'<div class="links"><a href="{escape(src)}">source</a></div></div>'
        )
        if i != len(order) - 1:
            boxes += '<div class="arrow">▸</div>'

    # ---- per-transaction rows --------------------------------------------
    rows = ""
    for path in sorted(RESULTS.glob("*.json")):
        if path.name.startswith("_"):
            continue
        d = _load(path).get("data", {})
        st = d.get("status", "?")
        risk = d.get("risk_score")
        band = d.get("risk_band", "")
        risk_cell = f"{risk} / {escape(str(band))}" if risk is not None else "—"
        rows += (
            f"<tr><td>{escape(d.get('transaction_id', '?'))}</td>"
            f"<td class=\"{STATUS_CLASS.get(st, '')}\">{escape(st)}</td>"
            f"<td>{escape(d.get('transaction_type', '—'))}</td>"
            f"<td>{escape(d.get('currency', '—'))}</td>"
            f"<td class=num>{escape(str(d.get('amount', '—')))}</td>"
            f"<td>{risk_cell}</td>"
            f"<td>{escape(str(d.get('compliance_decision', '—')))}</td>"
            f"<td>{escape(str(d.get('settlement_status', '—')))}</td>"
            f"<td>{escape(str(d.get('reason', '') or '—'))}</td>"
            f'<td><a href="{escape(rel)}/shared/results/{escape(path.name)}">json</a></td></tr>'
        )

    # ---- summary stat cards ----------------------------------------------
    def card(label: str, value: str, cls: str = "") -> str:
        return f'<div class="card {cls}"><span class="v">{escape(value)}</span><span class="k">{escape(label)}</span></div>'

    cards = card("transactions", str(total))
    cards += card("settled", str(by_status.get("settled", 0)), "settled")
    cards += card("held", str(by_status.get("held", 0)), "held")
    cards += card("rejected", str(by_status.get("rejected", 0)), "rejected")
    for ccy, amt in summary.get("settled_totals_by_currency", {}).items():
        cards += card(f"settled {escape(ccy)}", str(amt))

    # ---- outputs list -----------------------------------------------------
    outputs = (
        f'<li><b>Results:</b> {_link("results", "results/", base=run)} · '
        f'<a href="{rel}/shared/results/_summary.txt">_summary.txt</a> · '
        f'<a href="{rel}/shared/results/_summary.json">_summary.json</a></li>'
        f'<li><b>Run files:</b> {_link("manifest.json", "manifest.json", base=run)} · '
        f'{_link("audit.log", "audit.log (PII-masked)", base=run)}</li>'
        f'<li><b>Agents:</b> '
        + " · ".join(f'<a href="{rel}/agents/{k}.py">{escape(lab)}</a>' for k, lab, _ in STAGES)
        + "</li>"
        f'<li><b>Spec / config:</b> <a href="{rel}/specification.md">specification.md</a> · '
        f'<a href="{rel}/pipeline.config.json">pipeline.config.json</a></li>'
    )
    if pr_url:
        outputs += f'<li><b>Pull request:</b> <a href="{escape(pr_url)}">{escape(pr_url)}</a></li>'

    status = "all processed ✓" if manifest.get("all_processed") else "incomplete"

    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Banking Pipeline status</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0d1117;color:#e6edf3;margin:28px}}
 h1{{font-size:19px;margin:0 0 4px}} .meta{{color:#8b949e;font-size:13px;margin-bottom:6px}}
 a{{color:#58a6ff;text-decoration:none}} a:hover{{text-decoration:underline}} .dim{{color:#6e7681}}
 .cards{{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0 4px}}
 .card{{background:#161b22;border:1px solid #30363d;border-radius:9px;padding:10px 16px;min-width:96px;display:flex;flex-direction:column}}
 .card .v{{font-size:21px;font-weight:700}} .card .k{{font-size:11px;color:#8b949e;margin-top:2px}}
 .card.settled .v{{color:#3fb950}} .card.held .v{{color:#d29922}} .card.rejected .v{{color:#f85149}}
 .flow{{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:18px 0 8px}}
 .box{{border-radius:9px;padding:9px 13px;min-width:150px;font-size:13px;font-weight:600;text-align:center;line-height:1.35;background:#1f7a33;color:#fff}}
 .box small{{font-weight:400;opacity:.9}} .box .n{{opacity:.7;margin-right:4px}}
 .box .links{{margin-top:5px;font-size:11px;font-weight:400}} .box .links a{{color:#cfe8ff}}
 .arrow{{color:#6e7681;font-size:18px}}
 table{{border-collapse:collapse;font-size:13px;margin-top:14px}} td,th{{border:1px solid #30363d;padding:5px 11px;text-align:left}}
 th{{color:#8b949e;font-weight:600}} td.num{{text-align:right;font-variant-numeric:tabular-nums}}
 td.settled{{color:#3fb950}} td.held{{color:#d29922}} td.rejected{{color:#f85149}}
 h2{{font-size:15px;margin:20px 0 6px}} ul.outputs{{font-size:13px;line-height:1.8;margin:0;padding-left:18px}}
 .legend{{margin-top:14px;font-size:12px;color:#8b949e}}
</style></head><body>
 <h1>🏦 Banking Transaction Pipeline — {escape(run.name)}</h1>
 <div class="meta">run status: <b>{escape(status)}</b> &nbsp;·&nbsp; config: {escape(manifest.get("config", "pipeline.config.json"))} &nbsp;·&nbsp; money = Decimal (ROUND_HALF_UP) &nbsp;·&nbsp; PII-masked &nbsp;·&nbsp; fail-closed</div>
 <div class="cards">{cards}</div>
 <div class="flow">{boxes}</div>
 <table><tr><th>txn</th><th>status</th><th>type</th><th>ccy</th><th>amount</th><th>risk (score/band)</th><th>compliance</th><th>settlement</th><th>reason</th><th>result</th></tr>{rows}</table>
 <h2>Outputs (results · run files · agents · spec · PR)</h2><ul class="outputs">{outputs}</ul>
 <div class="legend">● green = settled &nbsp; ● amber = held for review &nbsp; ● red = rejected &nbsp;|&nbsp; click <b>source</b>/<b>json</b> to open each agent and per-transaction result</div>
</body></html>
"""
    out.write_text(html, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
