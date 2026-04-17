import tempfile
import unittest
from pathlib import Path

from public_data_extractor import extract_directory, safe_url, write_outputs


ROOT = Path(__file__).resolve().parents[1]


class PublicDataExtractorTest(unittest.TestCase):
    def test_extracts_clean_records_and_rejects(self):
        records, rejects = extract_directory(ROOT / "sample_pages", "https://example.com")

        self.assertEqual(len(records), 4)
        self.assertEqual(len(rejects), 2)
        self.assertEqual(records[0].title, "Workflow Audit Sprint")
        self.assertEqual(records[0].url, "https://example.com/services/workflow-audit")
        self.assertEqual(records[0].price_amount, 350.0)
        self.assertTrue(any(reject.reason == "duplicate url" for reject in rejects))
        self.assertTrue(any("missing summary" in reject.reason for reject in rejects))

    def test_writes_outputs(self):
        records, rejects = extract_directory(ROOT / "sample_pages", "https://example.com")

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            write_outputs(records, rejects, out_dir)

            self.assertTrue((out_dir / "records.json").exists())
            self.assertTrue((out_dir / "records.csv").exists())
            self.assertTrue((out_dir / "rejects.csv").exists())
            report = (out_dir / "extraction-report.md").read_text(encoding="utf-8")
            self.assertIn("Clean records: 4", report)
            self.assertIn("Rejected rows: 2", report)

    def test_rejects_unsafe_url_schemes(self):
        self.assertEqual(safe_url("https://example.com", "javascript:alert(1)"), "")
        self.assertEqual(safe_url("https://example.com", "mailto:ops@example.com"), "")


if __name__ == "__main__":
    unittest.main()
