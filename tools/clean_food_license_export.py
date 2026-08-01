#!/usr/bin/env python3
"""Normalize a Chicago food-service license CSV export and flag genuine new issuances.

Accepts either of two known column layouts, auto-detected by header:

  city_portal  - the raw City of Chicago "Business Licenses" open-data export
                 (license_number, legal_name, doing_business_as_name, address,
                 zip_code, neighborhood, application_type, license_status,
                 application_created_date, license_start_date, date_issued)

  actor        - the rook-data-tools "Food Service License Leads" Apify actor's
                 dataset export (recordId, businessName, legalName, address,
                 zip, neighborhood, licenseNumber, issuedDate,
                 applicationCreatedDate, licenseStartDate)

The actor's export already only ever contains initial ("ISSUE") retail food
establishment licenses in issued ("AAI") status, so rows in that layout are
always flagged as a new issuance. Rows from the raw city_portal export are
flagged only when application_type == "ISSUE" and license_status == "AAI",
mirroring the City of Chicago's own field definitions for those two columns.

This script does not fetch, request, or scrape anything. It only reads a CSV
you already have on disk.
"""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from pathlib import Path

CITY_PORTAL_COLUMNS = {
    "license_number", "legal_name", "doing_business_as_name", "address",
    "zip_code", "neighborhood", "application_type", "license_status",
    "application_created_date", "license_start_date", "date_issued",
}

ACTOR_COLUMNS = {
    "recordId", "businessName", "legalName", "address", "zip", "neighborhood",
    "licenseNumber", "issuedDate", "applicationCreatedDate", "licenseStartDate",
}

CANONICAL_FIELDS = [
    "source_schema", "license_number", "business_name", "legal_name", "address",
    "zip_code", "neighborhood", "application_type", "license_status",
    "application_created_date", "license_start_date", "date_issued",
    "is_new_issuance", "name_key", "address_key", "dedupe_key",
]


def detect_schema(fieldnames: set[str]) -> str:
    if CITY_PORTAL_COLUMNS <= fieldnames:
        return "city_portal"
    if ACTOR_COLUMNS <= fieldnames:
        return "actor"
    missing_city = sorted(CITY_PORTAL_COLUMNS - fieldnames)
    missing_actor = sorted(ACTOR_COLUMNS - fieldnames)
    raise SystemExit(
        "unrecognized column layout.\n"
        f"  missing for city_portal schema: {', '.join(missing_city)}\n"
        f"  missing for actor schema: {', '.join(missing_actor)}"
    )


def comparison_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").casefold()
    return " ".join(re.sub(r"[^\w]+", " ", value).split())


def identifier_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKC", value or "").casefold())


def to_canonical_row(row: dict[str, str], schema: str) -> dict[str, str]:
    if schema == "city_portal":
        business_name = row.get("doing_business_as_name") or row.get("legal_name") or ""
        canonical = {
            "source_schema": "city_portal",
            "license_number": row.get("license_number", ""),
            "business_name": business_name,
            "legal_name": row.get("legal_name", ""),
            "address": row.get("address", ""),
            "zip_code": row.get("zip_code", ""),
            "neighborhood": row.get("neighborhood", ""),
            "application_type": row.get("application_type", ""),
            "license_status": row.get("license_status", ""),
            "application_created_date": row.get("application_created_date", ""),
            "license_start_date": row.get("license_start_date", ""),
            "date_issued": row.get("date_issued", ""),
        }
        canonical["is_new_issuance"] = str(
            canonical["application_type"].strip().upper() == "ISSUE"
            and canonical["license_status"].strip().upper() == "AAI"
        )
    else:
        canonical = {
            "source_schema": "actor",
            "license_number": row.get("licenseNumber", ""),
            "business_name": row.get("businessName", ""),
            "legal_name": row.get("legalName", ""),
            "address": row.get("address", ""),
            "zip_code": row.get("zip", ""),
            "neighborhood": row.get("neighborhood", ""),
            "application_type": "ISSUE",
            "license_status": "AAI",
            "application_created_date": row.get("applicationCreatedDate", ""),
            "license_start_date": row.get("licenseStartDate", ""),
            "date_issued": row.get("issuedDate", ""),
            "is_new_issuance": "True",
        }

    canonical["name_key"] = comparison_key(canonical["business_name"] or canonical["legal_name"])
    canonical["address_key"] = comparison_key(
        " ".join([canonical["address"], canonical["zip_code"]])
    )
    license_id = identifier_key(canonical["license_number"])
    if license_id:
        canonical["dedupe_key"] = f"license:{license_id}"
    else:
        canonical["dedupe_key"] = (
            f"premises:{canonical['name_key']}:{canonical['address_key']}:"
            f"{canonical['date_issued']}"
        )
    return canonical


def normalize_rows(rows: list[dict[str, str]], schema: str) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        canonical = to_canonical_row(row, schema)
        if canonical["dedupe_key"] in seen:
            continue
        seen.add(canonical["dedupe_key"])
        output.append(canonical)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()

    with args.input_csv.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        schema = detect_schema(set(reader.fieldnames or []))
        rows = list(reader)

    normalized = normalize_rows(rows, schema)
    new_count = sum(1 for row in normalized if row["is_new_issuance"] == "True")

    with args.output_csv.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=CANONICAL_FIELDS)
        writer.writeheader()
        writer.writerows(normalized)

    print(
        f"detected {schema} schema; wrote {len(normalized)} unique rows "
        f"({new_count} flagged is_new_issuance) from {len(rows)} input rows"
    )


if __name__ == "__main__":
    main()
