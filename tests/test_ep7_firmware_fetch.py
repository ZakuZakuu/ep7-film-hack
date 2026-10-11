"""Offline-only tests for private serial injection into the OEM downloader."""
import os
import unittest
from unittest.mock import patch

from tools.ep7_firmware_fetch import get_serial, build_request


class TestNoninteractiveDownload(unittest.TestCase):
    def test_read_serial_from_named_env_without_logging(self):
        with patch.dict(os.environ, {"EP7_SERIAL": "TEST-SERIAL-123"}):
            with patch("getpass.getpass", side_effect=AssertionError("must not prompt")):
                self.assertEqual(get_serial("EP7_SERIAL"), "TEST-SERIAL-123")
                xml = build_request(get_serial("EP7_SERIAL"))
        self.assertIn(b"TEST-SERIAL-123", xml)

    def test_missing_env_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("getpass.getpass", side_effect=AssertionError("must not prompt")):
                self.assertEqual(get_serial("EP7_SERIAL"), "")


if __name__ == "__main__":
    unittest.main()
