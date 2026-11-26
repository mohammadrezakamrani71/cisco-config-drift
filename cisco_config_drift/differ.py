""Cisco IOS configuration normalization, diffing, and risk classification."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field


VOLATILE_PATTERNS = (
    re.compile(r"^Building configuration\.\.\.$"),
    re.compile(r"^Current configuration\s*:\s*\d+\s+bytes$"),
    re.compile(r"^!\s*Last configuration change at\b"),
    re.compile(r"^!\s*NVRAM config last updated at\b"),
    re.compile(r"^ntp clock-period\b"),
)

CRITICAL_PATTERNS = (
    re.compile(r"\btransport\s+input\s+(?:.*telnet|all)\b"),
    re.compile(r"^\s*enable\s+password\b"),
    re.compile(r"^\s*ip\s+http\s+server\b"),
    re.compile(r"^\s*no\s+service\s+password-encryption\b"),
    re.compile(r"^\s*snmp-server\s+community\s+(?:public|private)\b"),
    re.compile(r"^\s*no\s+ip\s+access-group\b"),
)

HIGH_PATTERNS = (
    re.compile(r"\b(?:ip\s+access-list|access-list)\b"),
    re.compile(r"^\s*(?:permit|deny)\s+"),
    re.compile(r"^\s*ip\s+route\b"),
    re.compile(r"^\s*standby\b"),
    re.compile(r"^\s*username\b"),
    re.compile(r"^\s*line\s+vty\b"),
    re.compile(r"^\s*ip\s+ssh\b"),
)

MEDIUM_PATTERNS = (
    re.compile(r"^\s*interface\b"),
    re.compile(r"^\s*ip\s+address\b"),
    re.compile(r"^\s*vlan\b"),
    re.compile(r"^\s*logging\b"),
    re.compile(r"^\s*ntp\b"),
    re.compile(r"^\s*banner\b"),
)

SEVERITY_RANK = {"INFO": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


@dataclass
class DriftChange:
    change_type: str  # "ADDED" | "REMOVED"
    severity: str     # "CRITICAL" | "HIGH" | "MEDIUM" | "INFO"
    line: str


@dataclass
class DriftReport:
    in_sync: bool
    highest_severity: str
    added_count: int
    removed_count: int
    changes: list[DriftChange] = field(default_factory=list)
    unified_diff: list[str] = field(default_factory=list)


def normalize_config(text: str) -> list[str]:
    ""Strip volatile timestamps/headers and trailing whitespace for clean comparison."""
    cleaned: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if any(pat.search(line.strip()) for pat in VOLATILE_PATTERNS):
            continue
        cleaned.append(line)
    return cleaned


def classify_line(line: str) -> str:
    ""Assign a security/operational risk severity to a changed Cisco IOS line.""
    stripped = line.strip()
    if any(p.search(stripped) for p in CRITICAL_PATTERNS):
        return "CRITICAL"
    if any(p.search(stripped) for p in HIGH_PATTERNS):
        return "HIGH"
    if any(p.search(stripped) for p in MEDIUM_PATTERNS):
        return "MEDIUM"
    return "INFO"


def detect_drift(
    golden_text: str,
    current_text: str,
    golden_label: str = "golden.cfg",
    current_label: str = "current.cfg",
) -> DriftReport:
    ""Compare a golden baseline configuration against a current configuration.""
    golden_lines = normalize_config(golden_text)
    current_lines = normalize_config(current_text)

    diff_lines = list(
        difflib.unified_diff(
            golden_lines,
            current_lines,
            fromfile=golden_label,
            tofile=current_label,
            lineterm="",
        )
    )

    changes: list[DriftChange] = []
    highest = "INFO"

    for dline in diff_lines:
        if dline.startswith(("---", "+++", "@@")):
            continue
        if dline.startswith("+"):
            content = dline[1:]
            sev = classify_line(content)
            changes.append(DriftChange(change_type="ADDED", severity=sev, line=content))
            if SEVERITY_RANK[sev] > SEVERITY_RANK[highest]:
                highest = sev
        elif dline.startswith("-"):
            content = dline[1:]
            sev = classify_line(content)
            # Removing a security control (e.g. service password-encryption) is at least HIGH
            if "service password-encryption" in content or "no ip http server" in content:
                sev = "CRITICAL"
            changes.append(DriftChange(change_type="REMOVED", severity=sev, line=content))
            if SEVERITY_RANK[sev] > SEVERITY_RANK[highest]:
                highest = sev

    added_count = sum(1 for c in changes if c.change_type == "ADDED")
    removed_count = sum(1 for c in changes if c.change_type == "REMOVED")
    in_sync = len(changes) == 0

    return DriftReport(
        in_sync=in_sync,
        highest_severity="NONE" if in_sync else highest,
        added_count=added_count,
        removed_count=removed_count,
        changes=changes,
        unified_diff=diff_lines,
    )
