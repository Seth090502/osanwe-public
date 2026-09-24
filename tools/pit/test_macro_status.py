"""Offline status-path and missing-data regressions; no refresh or account reads."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import macro_vintages_alfred as macro


class MacroStatusTests(unittest.TestCase):
    def test_default_status_has_same_owning_directory_as_vintage_store(self):
        self.assertEqual(Path(macro._DEFAULT_STATUS_JSON).parent, Path(macro._DEFAULT_VINTAGE_DB).parent)
        self.assertEqual(Path(macro._DEFAULT_FACTORS_DB).parent, Path(macro._DEFAULT_VINTAGE_DB).parent.parent)

    def execute(self, path):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = macro.main(["status", "--status-json", str(path), "--json"])
        return code, json.loads(output.getvalue())

    def test_missing_and_corrupt_metadata_are_explicit_without_raw_trace(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "coverage.json"
            self.assertEqual(self.execute(path)[1]["state"], "unavailable")
            path.write_text('{"counts": {"PRIVATE_CANARY": "private text"}}')
            code, result = self.execute(path)
            self.assertEqual(code, 2)
            self.assertNotIn("PRIVATE_CANARY", json.dumps(result))

    def test_saved_counts_are_observations_not_fresh_data_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "coverage.json"
            counts = {macro.ST_ACTUAL: 2, macro.ST_RECONSTRUCTION: 0, macro.ST_ASSUMED: 1, macro.ST_NO_SAFE_USE: 3}
            path.write_text(json.dumps({"counts": counts}))
            before = path.read_bytes()
            code, result = self.execute(path)
            self.assertEqual(code, 0)
            self.assertEqual(result["state"], "observed")
            self.assertEqual(result["series_count"], 6)
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
