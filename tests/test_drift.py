"""Unit tests for CiscoConfigDrift."""

import unittest

from cisco_config_drift.differ import detect_drift
from cisco_config_drift.reporter import render_html_report, render_markdown_report


class TestConfigDrift(unittest.TestCase):
    def test_in_sync_ignores_volatile_timestamps(self) -> None:
        golden = "! Last configuration change at 08:00:00 UTC\nhostname SW1\nip ssh version 2\n"
        current = "! Last configuration change at 12:30:00 UTC\nhostname SW1\nip ssh version 2\n"
        rep = detect_drift(golden, current)
        self.assertTrue(rep.in_sync)
        self.assertEqual(rep.highest_severity, "NONE")

    def test_critical_drift_detected(self) -> None:
        golden = "service password-encryption\nno ip http server\nline vty 0 4\n transport input ssh\n"
        current = "ip http server\nline vty 0 4\n transport input telnet ssh\n"
        rep = detect_drift(golden, current)
        self.assertFalse(rep.in_sync)
        self.assertEqual(rep.highest_severity, "CRITICAL")
        self.assertGreaterEqual(rep.added_count, 2)
        self.assertGreaterEqual(rep.removed_count, 2)

    def test_reports_render(self) -> None:
        rep = detect_drift("ip ssh version 2\n", "ip ssh version 2\nip http server\n")
        md = render_markdown_report(rep, "golden.cfg", "current.cfg")
        html_out = render_html_report(rep, "golden.cfg", "current.cfg")
        self.assertIn("DRIFT DETECTED (CRITICAL)", md)
        self.assertIn("<!DOCTYPE html>", html_out)


if __name__ == "__main__":
    unittest.main()
