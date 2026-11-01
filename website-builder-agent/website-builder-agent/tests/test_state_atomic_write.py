"""Regression: persistent state must remain atomic across separately mounted data paths."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import config
from utils import state


class AtomicStateTests(unittest.TestCase):
    def test_temp_file_is_created_alongside_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory) / "workspace-data"
            file = Path(directory) / "private-mounted-state" / "companies.json"
            with patch.object(config, "DATA_DIR", str(data_dir)), (
                    patch.object(config, "COMPANIES_FILE", str(file))):
                with patch("utils.state.tempfile.mkstemp",
                           wraps=tempfile.mkstemp) as make_temp:
                    state.save_companies({"company": {"name": "Vahvistettu yritys"}})
                    self.assertEqual(
                        Path(make_temp.call_args.kwargs["dir"]).resolve(),
                        file.parent.resolve(),
                    )
                self.assertTrue(file.exists())
                self.assertEqual(json.loads(file.read_text(encoding="utf-8"))["company"]["name"],
                                 "Vahvistettu yritys")
                self.assertEqual(state.load_companies()["company"]["name"], "Vahvistettu yritys")


if __name__ == "__main__":
    unittest.main()
