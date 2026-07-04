from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCANNER_PATH = ROOT / "tools" / "logcat_scanner.py"

spec = importlib.util.spec_from_file_location("logcat_scanner", SCANNER_PATH)
scanner = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules["logcat_scanner"] = scanner
spec.loader.exec_module(scanner)


class LogcatScannerTest(unittest.TestCase):
    def test_crashrecovery_noise_is_not_signal(self) -> None:
        line = "07-03 07:00:44.453 I AconfigPackage: com.android.crashrecovery.flags is mapped to com.android.crashrecovery"
        self.assertFalse(scanner.is_crash_signal(line))

    def test_uiautomator_androidruntime_noise_is_not_signal(self) -> None:
        line = "07-03 07:00:44.453 E AndroidRuntime: Process: com.android.commands.uiautomator, PID: 1234"
        self.assertFalse(scanner.is_crash_signal(line))

    def test_monkey_androidruntime_noise_is_not_signal(self) -> None:
        line = "07-03 07:00:44.453 E AndroidRuntime: Process: com.android.commands.monkey, PID: 1234"
        self.assertFalse(scanner.is_crash_signal(line))

    def test_skipi_fatal_exception_is_signal(self) -> None:
        line = "07-03 07:00:44.453 E AndroidRuntime: FATAL EXCEPTION: main Process: app.skipi.seafarer, PID: 1234"
        self.assertTrue(scanner.is_crash_signal(line))

    def test_anr_is_signal(self) -> None:
        line = "07-03 07:00:44.453 E ActivityManager: ANR in app.skipi.crewing.mobile"
        self.assertTrue(scanner.is_crash_signal(line))

    def test_file_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "logcat.txt"
            path.write_text(
                "\n".join(
                    [
                        "I AconfigPackage: com.android.crashrecovery.flags is mapped to com.android.crashrecovery",
                        "E AndroidRuntime: FATAL EXCEPTION: main Process: app.skipi.broker, PID: 9",
                    ]
                ),
                encoding="utf-8",
            )
            matches = scanner.scan_file(path)
        self.assertEqual(len(matches), 1)

    def test_missing_path_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = pathlib.Path(tmp) / "missing-logcat.txt"
            self.assertEqual(scanner.main([str(missing)]), 2)


if __name__ == "__main__":
    unittest.main()
