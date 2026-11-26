"""Markdown and HTML report generator for CiscoConfigDrift."""

from __future__ import annotations

import html
from datetime import datetime, timezone

from .differ import DriftReport


def render_markdown_report(
    report: DriftReport,
    golden_label: str,
    current_label: str,
    title: str = "Cisco Configuration Drift Report",
) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status_label = "IN SYNC" if report.in_sync else f"DRIFT DETECTED ({report.highest_severity})"

    lines = [
        f"# {title}",
        "",
        f"**Generated:** {timestamp}  ",
        f"**Baseline (Golden):** `{golden_label}`  ",
        f"**Target (Current):** `{current_label}`  ",
        f"**Status:** **{status_label}** (+{report.added_count} added / -{report.removed_count} removed)",
        "",
    ]

    if report.changes:
        lines.extend(
            [
                "## Detected Changes & Risk Classification",
                "",
                "| Change | Severity | Configuration Line |",
                "| :--- | :--- | :--- |",
            ]
        )
        for ch in report.changes:
            lines.append(f"| {ch.change_type} | **{ch.severity}** | `{ch.line.strip()}` |")
        lines.extend(["", "## Unified Diff", "", "```diff", *report.unified_diff, "```", ""])
    else:
        lines.append("No configuration drift detected. Device matches the golden baseline.")
        lines.append("")

    return "\n".join(lines)


def render_html_report(
    report: DriftReport,
    golden_label: str,
    current_label: str,
    title: str = "Cisco Configuration Drift Report",
) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status_label = "IN SYNC" if report.in_sync else f"DRIFT DETECTED ({report.highest_severity})"
    status_color = "#16a34a" if report.in_sync else "#dc2626"

    def sev_badge(sev: str) -> str:
        colors = {
            "CRITICAL": "#dc2626",
            "HIGH": "#ea580c",
            "MEDIUM": "#d97706",
            "INFO": "#2563eb",
        }
        bg = colors.get(sev, "#475569")
        return f'<span style="background:{bg};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600;">{html.escape(sev)}</span>'

    rows = "\n".join(
        f"<tr><td><strong>{html.escape(ch.change_type)}</strong></td>"
        f"<td>{sev_badge(ch.severity)}</td>"
        f"<td><code>{html.escape(ch.line)}</code></td></tr>"
        for ch in report.changes
    )

    diff_block = html.escape("\n".join(report.unified_diff)) if report.unified_diff else "No differences."

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 32px; background: #f8fafc; color: #0f172a; }}
  .container {{ max-width: 1100px; margin: 0 auto; background: #fff; padding: 28px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }}
  h1 {{ margin-top: 0; font-size: 24px; }}
  .meta {{ color: #475569; font-size: 14px; margin-bottom: 18px; }}
  .kpis {{ display: flex; gap: 16px; margin-bottom: 24px; }}
  .kpi {{ background: #f1f5f9; padding: 14px 18px; border-radius: 8px; flex: 1; }}
  .kpi strong {{ display: block; font-size: 20px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 14px; }}
  th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid #e2e8f0; }}
  th {{ background: #f1f5f9; font-weight: 600; }}
  code, pre {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 13px; }}
  pre {{ padding: 14px; overflow-x: auto; }}
</style>
</head>
<body>
<div class="container">
  <h1>{html.escape(title)}</h1>
  <div class="meta">Generated: {html.escape(timestamp)} | Golden: <code>{html.escape(golden_label)}</code> | Current: <code>{html.escape(current_label)}</code></div>
  <div class="kpis">
    <div class="kpi"><span>Audit Status</span><strong style="color:{status_color};">{html.escape(status_label)}</strong></div>
    <div class="kpi"><span>Lines Added</span><strong>+{report.added_count}</strong></div>
    <div class="kpi"><span>Lines Removed</span><strong>-{report.removed_count}</strong></div>
  </div>
  <h2>Detected Changes</h2>
  <table>
    <thead><tr><th>Change</th><th>Severity</th><th>Configuration Line</th></tr></thead>
    <tbody>{rows if rows else '<tr><td colspan="3">No drift detected.</td></tr>'}</tbody>
  </table>
  <h2>Unified Diff</h2>
  <pre>{diff_block}</pre>
</div>
</body>
</html>
"""
