# Public Data Extractor Safe

Small Python extraction pass for allowed public or exported HTML pages.

The point is not to bypass anything. The script is structured for jobs where the
client owns the data, provides an export, or confirms that automated public-data
access is allowed. It turns static HTML into reviewable CSV/JSON outputs with a
rejects file and a short handoff report.

## What It Demonstrates

- local-first extraction from saved/exported HTML
- no login, CAPTCHA bypass, hidden API probing, or session reuse
- allowlisted fields and clear validation rules
- clean JSON + CSV output
- rejects file for missing or unsafe rows
- concise Markdown handoff report
- standard-library Python with unit tests

## Files

```text
public_data_extractor.py
sample_pages/source-a.html
sample_pages/source-b.html
tests/test_public_data_extractor.py
handoff.md
```

## Run

```bash
python3 public_data_extractor.py sample_pages --out out --base-url https://example.com
```

Expected sample output:

```text
clean=4 rejected=2
```

## Test

```bash
python3 -m unittest discover -s tests
```

## Output

```text
out/records.json
out/records.csv
out/rejects.csv
out/extraction-report.md
```

## Safe-Use Boundary

Use this style of script only when the target data is public and allowed to be
collected, or when the client provides the export/files directly. For live
websites, check the site terms, robots policy, auth requirements, rate limits,
and permission from the data owner before running any automated access.

## OIMRQS Ops Context

This repo is part of the OIMRQS Ops public proof shelf: focused programming and technical-ops work across web, internal tools, automations, data cleanup, dashboards, APIs, webhooks, QA and handoff.

- Site: https://oimrqs-ops.x9kqz.uk/
- Portfolio: https://oimrqs-ops.x9kqz.uk/portfolio/
- Proof library: https://oimrqs-ops.x9kqz.uk/proof/
