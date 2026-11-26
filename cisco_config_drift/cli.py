""Command-line interface for CiscoConfigDrift."""

from __future__ import annotations

import argparse
from pathlib import Path

from .differ import detect_drift
from .reporter import render_html_report, render_markdown_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cisco-config-drift",
        description="Cisco IOS Golden Config Drift & Change-Management Auditor",
    )
    parser.add_argument("--golden", type=Path, required=True, help="Path to golden baseline config")
    parser.add_argument("--current", type=Path, required=True, help="Path to current running config")
    parser.add_argument("--out-md", type=Path, help="Optional Markdown report output path")
    parser.add_argument("--out-html", type=Path, help="Optional HTML report output path")
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit with code 2 if configuration drift is detected (useful for CI/CD)",
    )
    args = parser.parse_args(argv)

    golden_text = args.golden.read_text(encoding="utf-8")
    current_text = args.current.read_text(encoding="utf-8")

    report = detect_drift(
        golden_text,
        current_text,
        golden_label=args.golden.name,
        current_label=args.current.name,
    )
    md = render_markdown_report(report, args.golden.name, args.current.name)
    print(md)

    if args.out_md:
        args.out_md.write_text(md, encoding="utf-8")
    if args.out_html:
        args.out_html.write_text(
            render_html_report(report, args.golden.name, args.current.name),
            encoding="utf-8",
        )

    if args.fail_on_drift and not report.in_sync:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
