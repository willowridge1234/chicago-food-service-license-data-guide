# Finding newly licensed Chicago restaurants from public food-service license data

Chicago publishes every business license it issues, including new "Retail Food
Establishment" licenses for restaurants, cafes, food trucks with a fixed premises, and
other places that prepare or serve food. A newly *issued, initial* food-service license
is one of the more reliable local signals that a new restaurant or food business is
about to open, or has just opened, in a specific Chicago neighborhood.

It is a **signal, not proof of a finished business**. A license can be issued weeks
before a place actually opens its doors, some licensed locations never open, and a
license alone doesn't tell you who currently owns the business, whether it's staffed,
or whether it's ready to buy anything from you today.

This guide shows how to pull that signal yourself, directly from the City of Chicago's
own public data, for free — how to read the fields correctly, keep only genuine new
issuances, deduplicate, preserve where every row came from, and use the result without
misrepresenting what a license means.

It is for people who plausibly want a list of newly licensed Chicago food businesses:
restaurant-equipment and smallware suppliers, POS and payments vendors, insurance
brokers, staffing agencies, waste/grease/linen services, signage and menu-board vendors,
and local B2B sales or marketing teams building Chicago-specific outreach lists.

> **Commercial disclosure.** Rook Data Tools maintains this guide and sells a paid Apify
> actor that automates this same workflow — [Food Service License Leads –
> Chicago Restaurant Openings][actor]. It currently covers **Chicago only**, runs on
> pay-per-event pricing, and handles the scheduling, delta/dedup, and dataset-shaped
> export for you. Check the live actor page for current scope, fields, and pricing before
> relying on any number quoted here. The rest of this repository explains how to do the
> underlying work yourself, with or without the actor.

[actor]: https://apify.com/rook-data-tools/new-food-service-license-leads?utm_source=github&utm_medium=referral&utm_campaign=chicago_food_service_license_data_guide

## Quick answer

1. Pull from the City of Chicago's own **Business Licenses** open dataset
   (`data.cityofchicago.org`, dataset id `r5kz-chrr`) — it is public, requires no
   account or API key, and the city updates it daily.
2. Filter to `license_description = "Retail Food Establishment"` (`license_code 1006`)
   **and** `application_type = "ISSUE"` **and** `license_status = "AAI"`. That combination
   is the City's own definition of a newly issued initial food-service license — not a
   renewal, transfer, or pending application.
3. Keep the raw source columns and record when you retrieved the data.
4. Deduplicate by `license_number` — Chicago's own documentation says it is "the license
   number known to the public" and the field most users want.
5. Read `application_created_date`, `license_start_date`, and `date_issued` as three
   different dates with three different meanings (below) — don't collapse them into one
   "opening date."
6. Qualify against your own territory and ideal-customer profile before any outreach, and
   don't treat a licensed address as a verified, currently-operating business.

## Where this data comes from

The source is the City of Chicago's own **Business Licenses** dataset, owned by the
Department of Business Affairs and Consumer Protection (BACP) and published on the
Chicago Data Portal (Socrata):

- Dataset: `https://data.cityofchicago.org/Community-Economic-Development/Business-Licenses/r5kz-chrr`
- Format: public Socrata "SODA" API and CSV/JSON export, no login or API key required
- Coverage: business licenses issued from **January 1, 2002 to the present**
- Update frequency: **daily**, per the dataset's own description
- Attribution: City of Chicago

Nothing about accessing it is secret or unusual — it's a standard, documented open-data
endpoint. You can query the SODA API directly with your own filters (for example, by
`license_description`, `application_type`, `license_status`, and a date range) or pull
the full CSV/JSON export and filter locally; Socrata's own API docs, linked from the
dataset page above, cover the supported query parameters.

A companion dataset, **Business Owners** (`data.cityofchicago.org`, dataset id
`ezma-pppn`), can be joined on `account_number` if you need registered-owner details.
This guide doesn't cover it further; treat owner names with the same caution as any
other public record (see [Responsible use](#responsible-use-of-public-license-data)).

## Reading the fields correctly

These definitions are the City of Chicago's own, from the dataset's published
description and column documentation, not a paraphrase of the actor's marketing copy.

**`application_type`** — what kind of record this row is:

| Value | Meaning |
|---|---|
| `ISSUE` | The record associated with the **initial** license application. |
| `RENEW` | A subsequent renewal record. |
| `C_LOC` | Change of location — the business moved. |
| `C_CAPA` | Change of capacity (only a few license types use this). |
| `C_EXPA` | Change of premises expansion (liquor licenses only). |
| `C_SBA` | Change of business activity — an activity was added or marked expired. |

**`license_status`** — the current state of that license record:

| Value | Meaning |
|---|---|
| `AAI` | The license **was issued**. |
| `AAC` | The license was cancelled during its term. |
| `REV` | The license was revoked. |
| `REA` | The license revocation has been appealed. |

**A newly issued license is `application_type = ISSUE` and `license_status = AAI`
together.** An `ISSUE` row that is `AAC` or `REV` is not a live, newly opened business —
it was issued and then cancelled or revoked. Filtering on `application_type` alone, or
`license_status` alone, will misclassify rows.

**Several dates, several different meanings — don't collapse them into one "opening
date":**

| Field | What it actually records |
|---|---|
| `application_created_date` | When the license application was created. Not populated for `RENEW` records. |
| `license_approved_for_issuance` | When the license was ready for issuance (a license can be held up if the business owes the City debt). |
| `date_issued` | When the license was actually issued. |
| `license_start_date` | The start of the license's term. |
| `expiration_date` | The end of the license's term — typically about two years after `license_start_date` for a Retail Food Establishment license. |

`date_issued` is the field that should drive a "how new is this" filter. Don't substitute
`application_created_date` for it — the gap between application and issuance is often
weeks, and some applications never reach issuance at all.

**License type:** `license_code 1006` corresponds to `license_description "Retail Food
Establishment"` — the license category this guide and the linked actor both track. The
same dataset also carries a `business_activity` field (for example, "Sale of Food
Prepared Onsite With Dining Area" versus "Preparation of Food and Dining on Premises With
Seating") that further describes the kind of food operation, which is useful for
qualifying whether a lead fits a kitchen-equipment offer versus a grab-and-go concept.

## What an issued license does — and doesn't — tell you

Per the City's own retail-food licensing guidance, a Retail Food Establishment license
cannot be issued until the location has passed an on-site health inspection by the
Chicago Department of Public Health (CDPH), and the business must keep at least one
staff member with a valid Food Service Sanitation Certificate on-site whenever it
operates. So an `ISSUE` + `AAI` row means the City has already:

- accepted a complete application for that address, and
- inspected the premises (or approved it for issuance) before issuing the license.

It does **not** mean, and this guide does not claim, that the business:

- has actually opened its doors or started serving customers,
- is currently open, staffed, or operating on any given day you look at it,
- is still under the same ownership named on the license (ownership and location can
  change later via `C_LOC`, `C_SBA`, or a new `ISSUE` record entirely),
- has passed every *subsequent* routine CDPH inspection (those continue on their own
  schedule after issuance and are a separate public dataset — Food Inspections — not this
  one), or
- is ready, willing, or able to buy anything from a vendor today.

Treat a newly issued license as "worth researching," not as a verified, sales-ready
account. Confirm current status through the business's own public presence, or a fresh
pull of this same dataset, before you rely on it for anything time-sensitive.

## A reproducible workflow

### 1. Pull and snapshot

Query the Socrata endpoint above (or the actor) on a schedule, and save each pull as an
immutable, dated file — don't overwrite last week's export:

```text
raw/2026-08-01_chicago_food_licenses.csv
```

Keep the retrieval date next to the data. "Updated daily" describes the City's own
dataset, not a guarantee about when *you* checked it.

### 2. Normalize and flag genuinely new issuances

This repository includes a dependency-free helper that accepts either the raw City
export or the actor's own export columns, auto-detects which one you gave it, and
produces one canonical CSV:

```bash
python3 tools/clean_food_license_export.py \
  examples/fictional_city_portal_export.csv \
  /tmp/cleaned.csv
```

It adds an `is_new_issuance` column (true only for `application_type == ISSUE` and
`license_status == AAI`), a stable `dedupe_key` built from `license_number` (falling back
to a normalized premises+name+date key only when `license_number` is blank), and
`name_key`/`address_key` comparison fields for downstream matching. It keeps the first
occurrence of each `dedupe_key` and drops later duplicates.

Run its tests with:

```bash
python3 -m unittest discover -s tests -v
```

The script only reads and writes CSV files you already have; it does not fetch, request,
or scrape anything, and it does not decide who to contact.

### 3. Deduplicate across pulls, not just within one file

Across weekly snapshots, the same `license_number` can reappear (a `RENEW` years later,
a status change). Match on `license_number` first; only fall back to a
normalized-name-plus-address match when `license_number` is missing, and review those
fallback matches by hand before merging — food halls, strip malls, and shared kitchens
commonly have several licensees at one address.

### 4. Qualify before outreach

Write your ideal-customer profile before you look at the list, for example:

```text
In territory AND is_new_issuance = True AND business_activity fits our offer
AND not an existing account AND relevant before or shortly after opening
```

Then bucket each row as `review_now`, `verify` (plausible fit, missing information), or
`exclude` (out of territory, renewal, cancelled/revoked, existing account, wrong activity
type). A small reviewed queue beats a large unreviewed one.

### 5. Verify before contact

For anything selected for outreach: re-check the license is still `AAI` (not
subsequently `AAC`/`REV`), confirm the address is the licensed premises and not a
registered-agent address, identify the business through its own public presence, check
your suppression list, and record why the offer is relevant now.

## Fictitious example output

Every business name, address, and license number below is invented; none corresponds to
a real Chicago business or license record.

```json
{
  "source_schema": "city_portal",
  "license_number": "9000002",
  "business_name": "Demo Noodle House",
  "legal_name": "DEMO NOODLE HOUSE LLC",
  "address": "22 Fictional Ave",
  "zip_code": "60618",
  "neighborhood": "AVONDALE",
  "application_type": "ISSUE",
  "license_status": "AAI",
  "application_created_date": "2026-05-18",
  "license_start_date": "2026-06-05",
  "date_issued": "2026-06-05",
  "is_new_issuance": "True",
  "name_key": "demo noodle house",
  "address_key": "22 fictional ave 60618",
  "dedupe_key": "license:9000002"
}
```

See [`examples/fictional_city_portal_export.csv`](examples/fictional_city_portal_export.csv)
(raw City-shaped export), [`examples/fictional_actor_export.csv`](examples/fictional_actor_export.csv)
(actor-shaped export), and [`examples/fictional_cleaned_output.csv`](examples/fictional_cleaned_output.csv)
(the tool's output) for a duplicate, a renewal, a cancelled license, and a
missing-license-number row, all clearly fabricated with names like "Sample," "Demo," and
"Placeholder."

## Responsible use of public license data

This is operational guidance, not legal advice; have qualified counsel review any
outreach program.

- **A license is a public record, not marketing consent.** Publication by the City does
  not grant permission for automated calls, texts, or bulk email to any contact
  associated with the license.
- **Don't overclaim the signal.** Do not tell a prospect, in copy or in your CRM, that
  you know their opening date, that they are "confirmed open," or that a license implies
  anything about their current staffing, ownership, or purchase intent.
- **Minimize personal data.** This dataset is about businesses and licenses, not people.
  Prefer business-level facts; don't seek out or republish an individual owner's home
  address, personal phone number, or other sensitive personal fields from a linked
  dataset merely because they're technically accessible.
- **Email:** the US [FTC CAN-SPAM compliance guide][can-spam] applies to commercial
  email, including B2B email — accurate headers, required ad disclosure, a valid postal
  address, a working opt-out, and honoring opt-outs promptly.
- **Calls and texts:** the TCPA and related FCC rules can require consent before
  autodialed or prerecorded calls and texts. A public license record is not that
  consent.
- **State and local rules may be stricter** than federal rules; Illinois- and
  Chicago-specific consumer-protection and privacy rules can apply on top of the above.
- **Keep one durable suppression list** across every tool and representative your team
  uses; a fresh license record does not override an earlier opt-out.

[can-spam]: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business

## Automated option: current verified scope

Rook Data Tools' [Food Service License Leads actor][actor] automates steps 1–2 above for
Chicago. As verified directly against the live, public Apify API on **2026-08-01**, it
was public, covered **Chicago only**, and used pay-per-event pricing of **$0.005 per
actor run start plus $0.005 per saved license lead**. Its public statistics at that time
showed **2 total users**, **1 user in the prior 30 days**, **2 total runs**, and **1
successful public run in the prior 30 days**, with no reviews or rating yet.

Those figures are a dated baseline, not a promise of coverage, freshness, accuracy, or
future pricing — confirm the live actor page before relying on any of them. The actor
returns the same public-record fields described in this guide; using it does not remove
your responsibility to qualify leads and follow the guidance above.

## Measurement

The actor link in this guide uses only conventional UTM parameters:

```text
utm_source=github
utm_medium=referral
utm_campaign=chicago_food_service_license_data_guide
```

These identify the intended referral source; they are not a claim that Apify exposes
campaign-level analytics. The exact publication baseline and a repeatable future check
are in [`MEASUREMENT.md`](MEASUREMENT.md).

## Responsible contributions

Issues and pull requests that improve the public-source documentation, the generic
cleaning tool, or the compliance references are welcome. Please do not submit real
scraped lead rows, personal information, credentials, scraping bypasses, private
collection methods, or unverified claims about the dataset.

## License

Code in `tools/` and `tests/` is licensed under the MIT License. Documentation and
fictitious examples are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
See [`LICENSE`](LICENSE).

## Related

Other free workflows and guides we publish:

- [n8n-ai-lead-scoring](https://github.com/willowridge1234/n8n-ai-lead-scoring) — Free workflow — score scraped leads against your ICP, log to Google Sheets
- [n8n-review-intent-lead-scoring](https://github.com/willowridge1234/n8n-review-intent-lead-scoring) — Free workflow — score G2/Capterra reviewers by switching intent
- [n8n-tradeshow-exhibitor-lead-scoring](https://github.com/willowridge1234/n8n-tradeshow-exhibitor-lead-scoring) — Free workflow — score trade-show exhibitors against your ICP
- [n8n-lead-scoring-guide](https://github.com/willowridge1234/n8n-lead-scoring-guide) — Guide — which signals predict a good lead, and how to tell if scoring works
- [chamber-association-lead-lists](https://github.com/willowridge1234/chamber-association-lead-lists) — Guide — building B2B lead lists from chamber & association directories
- [memberclicks-directory-export-guide](https://github.com/willowridge1234/memberclicks-directory-export-guide) — Guide — exporting a public MemberClicks member directory
- [new-liquor-license-data-guide](https://github.com/willowridge1234/new-liquor-license-data-guide) — Guide + tool — building a lead list from public liquor-licence records
- [wild-apricot-directory-export-guide](https://github.com/willowridge1234/wild-apricot-directory-export-guide) — Guide — exporting a public Wild Apricot member directory
- [membershipworks-member-directory-export-guide](https://github.com/willowridge1234/membershipworks-member-directory-export-guide) — Guide + tool — exporting a public MembershipWorks member directory
- [chambermaster-directory-export-guide](https://github.com/willowridge1234/chambermaster-directory-export-guide) — Guide — exporting a public ChamberMaster or GrowthZone member directory
