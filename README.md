# CiscoConfigDrift — Golden Config Drift & Change-Management Auditor

**CiscoConfigDrift** is a zero-dependency Python CLI tool that compares a device's current Cisco IOS running configuration against an approved **Golden Baseline**, detects unauthorized or accidental changes, classifies each change by security severity (`CRITICAL`, `HIGH`, `MEDIUM`, `INFO`), and generates Markdown/HTML audit reports.

## Key Features

- **Noise-Free Normalization (`cisco_config_drift/differ.py`):** Ignores volatile IOS headers and timestamps (`! Last configuration change...`, `Current configuration : ...`) so only real configuration changes are flagged.
- **Risk-Aware Classification:** Automatically tags high-risk regressions such as enabling `ip http server`, allowing `transport input telnet` on VTY lines, removing `service password-encryption`, or altering ACLs and HSRP priorities.
- **CI/CD & Automation Ready (`--fail-on-drift`):** Returns exit code `2` when drift is detected for automated compliance pipelines.
- **Markdown & HTML Reporting (`cisco_config_drift/reporter.py`):** Produces clear summary tables and unified diffs.

## Project Structure

```text
cisco-config-drift/
├── main.py
├── cisco_config_drift/
│   ├── __init__.py
│   ├── cli.py
│   ├── differ.py
│   └── reporter.py
├── samples/
│   ├── golden_core_sw1.cfg
│   └── drifted_core_sw1.cfg
├── tests/
│   └── test_drift.py
├── LICENSE
└── README.md
```

## Quick Start

Requires **Python 3.10+** (pure standard library — zero external dependencies).

```bash
python3 main.py \
  --golden samples/golden_core_sw1.cfg \
  --current samples/drifted_core_sw1.cfg \
  --out-md drift_report.md \
  --out-html drift_report.html
```

## Running Tests

```bash
python3 -m unittest discover -s tests -v
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
