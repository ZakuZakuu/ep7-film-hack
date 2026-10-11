"""Synthetic environment/HTTP tests: no serial, network or OEM bytes needed."""
import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import ep7_firmware_fetch as fetch


class Reply(io.BytesIO):
    url = 'https://fw01.om-digitalsolutions.net/synthetic.bin'


class TestSerialEnvironment(unittest.TestCase):
    def test_missing_empty_or_invalid_serial_stops_before_prompt_or_network(self):
        for value in (None, '', ' ', 'x' * 61):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as td:
                errors = io.StringIO()
                with patch.dict(os.environ, {}, clear=True):
                    if value is not None:
                        os.environ['EP7_TEST_SERIAL'] = value
                    with patch('sys.argv', ['fetch', '--serial-env', 'EP7_TEST_SERIAL',
                                            '--output-dir', str(Path(td) / 'not-created')]), \
                         patch.object(fetch.getpass, 'getpass') as prompt, \
                         patch.object(fetch.urllib.request, 'urlopen') as network, \
                         contextlib.redirect_stderr(errors):
                        self.assertEqual(fetch.main(), 2)
                        prompt.assert_not_called()
                        network.assert_not_called()
                self.assertFalse((Path(td) / 'not-created').exists())
                if value and value.strip():
                    self.assertNotIn(value, errors.getvalue())

    def test_injected_serial_used_only_in_mock_request_not_output(self):
        # This string is deliberately invented; never a real camera identity.
        serial = 'SYNTHETIC-SERIAL-FOR-MOCK-ONLY'
        metadata = (b'<response><url>https://fw01.om-digitalsolutions.net/synthetic.bin</url>'
                    b'<file_name>synthetic.bin</file_name></response>')
        payload = b'SYNTHETIC-NON-FIRMWARE' + bytes(1024 * 1024)
        stdout, stderr = io.StringIO(), io.StringIO()
        with tempfile.TemporaryDirectory() as td, \
             patch.dict(os.environ, {'EP7_TEST_SERIAL': serial}), \
             patch('sys.argv', ['fetch', '--serial-env', 'EP7_TEST_SERIAL', '--output-dir', td]), \
             patch.object(fetch.getpass, 'getpass') as prompt, \
             patch.object(fetch.urllib.request, 'urlopen',
                          side_effect=[Reply(metadata), Reply(payload)]) as network, \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(fetch.main(), 0)
            prompt.assert_not_called()
            self.assertEqual(network.call_count, 2)
            self.assertIn(serial.encode(), network.call_args_list[0].args[0].data)
            self.assertEqual((Path(td) / 'E142_EP7_firmware_download.BIN').read_bytes(), payload)
        self.assertNotIn(serial, stdout.getvalue() + stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
