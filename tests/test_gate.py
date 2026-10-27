import copy
from datetime import date
import hashlib
from pathlib import Path
import tempfile
import unittest

from scripts.gate import assess


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "demo.py").write_text("eval(value)\n")
        self.report = {"results": [{"check_id": "python-dynamic-evaluation", "path": "demo.py",
                                   "start": {"line": 1}, "end": {"line": 1}}], "errors": []}
        self.empty = {"schemaVersion": 1, "findings": []}
        self.entry = {"rule": "python-dynamic-evaluation", "path": "demo.py", "startLine": 1, "endLine": 1,
                      "fileSHA256": hashlib.sha256((self.root / "demo.py").read_bytes()).hexdigest(),
                      "reviewed": "2026-10-27", "expires": "2026-11-26", "reason": "Isolated scanner fixture"}

    def test_clean_scan_passes(self):
        self.assertEqual(assess({"results": [], "errors": []}, self.empty, self.root), set())

    def test_new_finding_fails(self):
        self.assertEqual(len(assess(self.report, self.empty, self.root)), 1)

    def test_exact_reviewed_fixture_passes(self):
        self.assertFalse(assess(self.report, {"schemaVersion": 1, "findings": [self.entry]},
                                self.root, date(2026, 10, 27)))

    def test_changed_source_invalidates_baseline(self):
        (self.root / "demo.py").write_text("eval(untrusted)\n")
        with self.assertRaises(ValueError):
            assess(self.report, {"schemaVersion": 1, "findings": [self.entry]}, self.root, date(2026, 10, 27))

    def test_expired_or_future_review_fails(self):
        for day in [date(2026, 10, 26), date(2026, 11, 27)]:
            with self.assertRaises(ValueError):
                assess(self.report, {"schemaVersion": 1, "findings": [self.entry]}, self.root, day)

    def test_missing_or_error_report_fails(self):
        for report in [{}, {"results": [], "errors": [{"message": "scan failed"}]}]:
            with self.assertRaises(ValueError):
                assess(report, self.empty, self.root)

    def test_path_escape_fails(self):
        report = copy.deepcopy(self.report)
        report["results"][0]["path"] = "../demo.py"
        with self.assertRaises(ValueError):
            assess(report, self.empty, self.root)

    def test_unused_baseline_fails(self):
        with self.assertRaises(ValueError):
            assess({"results": [], "errors": []}, {"schemaVersion": 1, "findings": [self.entry]},
                   self.root, date(2026, 10, 27))


if __name__ == "__main__":
    unittest.main()
