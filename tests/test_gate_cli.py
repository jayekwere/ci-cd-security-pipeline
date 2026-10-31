"""Exercise process exit contracts rather than only helper return values."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CliTests(unittest.TestCase):
    def test_evidence_states(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'scan.json'
            command = [sys.executable, 'scripts/gate.py', '--report', str(report),
                       '--baseline', 'policy/empty-baseline.json', '--require-target', 'app/server.py']
            for value in [None, '{', json.dumps({'results': [], 'errors': [], 'paths': {'scanned': []}}),
                          json.dumps({'results': [], 'errors': ['scanner failed'],
                                      'paths': {'scanned': ['app/server.py']}})]:
                if value is not None:
                    report.write_text(value)
                self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            report.write_text(json.dumps({'results': [], 'errors': [],
                                          'paths': {'scanned': ['app/server.py']}}))
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
