"""Startup reporting stays useful with missing/unwritable log directories."""
import io
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import startup


class StartupTests(unittest.TestCase):
    def test_log_directory_and_rotation_are_configured(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict(startup.os.environ, {'LOCALAPPDATA': directory}), \
                patch.object(startup.logging, 'basicConfig') as configure:
            path = startup.configure()
            handler = configure.call_args.kwargs['handlers'][0]
            try:
                self.assertTrue(path.is_file())
                self.assertEqual(handler.maxBytes, 250_000)
                self.assertEqual(handler.backupCount, 2)
            finally:
                handler.close()

    def test_unwritable_log_folder_is_nonfatal(self):
        with patch.object(Path, 'mkdir', side_effect=PermissionError('denied')):
            self.assertIsNone(startup.configure())

    def test_failure_contains_traceback_and_user_log_location(self):
        stderr = io.StringIO()
        with patch.object(startup.sys, 'stderr', stderr), \
                patch.object(startup.sys, 'frozen', False, create=True), \
                self.assertLogs(level='ERROR') as logs:
            try:
                raise ImportError('test missing dependency')
            except ImportError:
                startup.report_failure(Path('example/startup.log'))
        self.assertIn('test missing dependency', logs.output[0])
        self.assertIn('startup.log', stderr.getvalue())
