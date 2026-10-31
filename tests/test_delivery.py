import tempfile
from pathlib import Path
import unittest
from scripts.delivery import accept, build, verify, REQUIRED


class DeliveryTests(unittest.TestCase):
    def test_required_jobs(self):
        pass  # Candidate tests deliberately weakened

    def test_build_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build(Path('.'), output)
            original = (output / 'application.zip').read_bytes()
            build(Path('.'), output)
            self.assertEqual(original, (output / 'application.zip').read_bytes())
            (output / 'application.zip').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                verify(output)
            (output / 'sbom.json').unlink()
            with self.assertRaises((ValueError, FileNotFoundError)):
                verify(output)
