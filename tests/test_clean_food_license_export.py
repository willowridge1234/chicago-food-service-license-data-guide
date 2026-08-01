import csv
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "clean_food_license_export.py"

sys.path.insert(0, str(ROOT / "tools"))
import clean_food_license_export as tool  # noqa: E402


class DetectSchemaTests(unittest.TestCase):
    def test_detects_city_portal_schema(self):
        fields = tool.CITY_PORTAL_COLUMNS | {"license_code", "license_description"}
        self.assertEqual(tool.detect_schema(fields), "city_portal")

    def test_detects_actor_schema(self):
        self.assertEqual(tool.detect_schema(set(tool.ACTOR_COLUMNS)), "actor")

    def test_unrecognized_schema_raises(self):
        with self.assertRaises(SystemExit):
            tool.detect_schema({"foo", "bar"})


class CanonicalRowTests(unittest.TestCase):
    def test_city_portal_issue_and_aai_is_new(self):
        row = {
            "license_number": "9000001",
            "legal_name": "SAMPLE KITCHEN TEST LLC",
            "doing_business_as_name": "Sample Kitchen Test",
            "address": "1 Example Plaza",
            "zip_code": "60601",
            "neighborhood": "LOOP",
            "application_type": "ISSUE",
            "license_status": "AAI",
            "application_created_date": "2026-06-01",
            "license_start_date": "2026-06-20",
            "date_issued": "2026-06-20",
        }
        canonical = tool.to_canonical_row(row, "city_portal")
        self.assertEqual(canonical["is_new_issuance"], "True")
        self.assertEqual(canonical["business_name"], "Sample Kitchen Test")
        self.assertEqual(canonical["dedupe_key"], "license:9000001")

    def test_city_portal_renewal_is_not_new(self):
        row = {
            "license_number": "9000001",
            "legal_name": "SAMPLE KITCHEN TEST LLC",
            "doing_business_as_name": "",
            "address": "1 Example Plaza",
            "zip_code": "60601",
            "neighborhood": "LOOP",
            "application_type": "RENEW",
            "license_status": "AAI",
            "application_created_date": "",
            "license_start_date": "2028-06-20",
            "date_issued": "2028-06-10",
        }
        canonical = tool.to_canonical_row(row, "city_portal")
        self.assertEqual(canonical["is_new_issuance"], "False")
        # Falls back to legal_name when doing_business_as_name is blank.
        self.assertEqual(canonical["business_name"], "SAMPLE KITCHEN TEST LLC")

    def test_city_portal_cancelled_is_not_new(self):
        row = {
            "license_number": "9000005",
            "legal_name": "CLOSED TEST TAQUERIA LLC",
            "doing_business_as_name": "Closed Test Taqueria",
            "address": "77 Rehearsal Rd",
            "zip_code": "60608",
            "neighborhood": "PILSEN",
            "application_type": "ISSUE",
            "license_status": "AAC",
            "application_created_date": "2026-04-10",
            "license_start_date": "2026-04-30",
            "date_issued": "2026-04-30",
        }
        canonical = tool.to_canonical_row(row, "city_portal")
        self.assertEqual(canonical["is_new_issuance"], "False")

    def test_actor_rows_are_always_new(self):
        row = {
            "recordId": "9000001-20260620",
            "businessName": "Sample Kitchen Test",
            "legalName": "SAMPLE KITCHEN TEST LLC",
            "address": "1 Example Plaza",
            "zip": "60601",
            "neighborhood": "LOOP",
            "licenseNumber": "9000001",
            "issuedDate": "2026-06-20",
            "applicationCreatedDate": "2026-06-01",
            "licenseStartDate": "2026-06-20",
        }
        canonical = tool.to_canonical_row(row, "actor")
        self.assertEqual(canonical["is_new_issuance"], "True")
        self.assertEqual(canonical["application_type"], "ISSUE")
        self.assertEqual(canonical["license_status"], "AAI")
        self.assertEqual(canonical["dedupe_key"], "license:9000001")


class NormalizeRowsTests(unittest.TestCase):
    def test_dedupe_by_license_number(self):
        base = {
            "license_number": "9000001",
            "legal_name": "SAMPLE KITCHEN TEST LLC",
            "doing_business_as_name": "Sample Kitchen Test",
            "address": "1 Example Plaza",
            "zip_code": "60601",
            "neighborhood": "LOOP",
            "application_type": "ISSUE",
            "license_status": "AAI",
            "application_created_date": "2026-06-01",
            "license_start_date": "2026-06-20",
            "date_issued": "2026-06-20",
        }
        rows = [dict(base), dict(base)]
        normalized = tool.normalize_rows(rows, "city_portal")
        self.assertEqual(len(normalized), 1)

    def test_premises_fallback_key_when_license_number_blank(self):
        row = {
            "license_number": "",
            "legal_name": "SAMPLE KITCHEN TEST LLC",
            "doing_business_as_name": "Sample Kitchen Test",
            "address": "1 Example Plaza",
            "zip_code": "60601",
            "neighborhood": "LOOP",
            "application_type": "ISSUE",
            "license_status": "AAI",
            "application_created_date": "2026-06-01",
            "license_start_date": "2026-06-20",
            "date_issued": "2026-06-20",
        }
        canonical = tool.to_canonical_row(row, "city_portal")
        self.assertTrue(canonical["dedupe_key"].startswith("premises:"))


class CliTests(unittest.TestCase):
    def test_cli_end_to_end_on_example_csv(self):
        example = ROOT / "examples" / "fictional_city_portal_export.csv"
        with example.open() as handle:
            input_row_count = sum(1 for _ in csv.DictReader(handle))

        output_path = ROOT / "tests" / "_tmp_output.csv"
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(example), str(output_path)],
                capture_output=True, text=True, check=True,
            )
            self.assertIn("detected city_portal schema", result.stdout)
            with output_path.open() as handle:
                output_rows = list(csv.DictReader(handle))
            self.assertLessEqual(len(output_rows), input_row_count)
            self.assertTrue(all("is_new_issuance" in row for row in output_rows))
        finally:
            output_path.unlink(missing_ok=True)

    def test_cli_rejects_unrecognized_columns(self):
        bad_csv = ROOT / "tests" / "_tmp_bad.csv"
        bad_csv.write_text("foo,bar\n1,2\n", encoding="utf-8")
        output_path = ROOT / "tests" / "_tmp_bad_output.csv"
        try:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(bad_csv), str(output_path)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unrecognized column layout", result.stderr)
        finally:
            bad_csv.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
