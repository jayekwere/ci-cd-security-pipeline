import unittest
from scripts.check_secrets import check


class SecretTests(unittest.TestCase):
    def test_synthetic_nonfunctional_tokens_rejected(self):
        self.assertTrue(check(b'AKIA' + b'0' * 16))
        self.assertTrue(check(b'ghp_' + b'0' * 36))

    def test_clean_passes(self):
        self.assertFalse(check(b'credential = os.environ["TOKEN"]'))
