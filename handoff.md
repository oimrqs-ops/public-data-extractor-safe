# Handoff Notes

## Input

Saved or exported HTML files with allowed public listing data:

```text
sample_pages/*.html
```

## Task

Extract listing title, URL, category, price, and summary into reviewable files
without logging in, bypassing access controls, or probing hidden endpoints.

## Deliverable

- `public_data_extractor.py`
- `out/records.json`
- `out/records.csv`
- `out/rejects.csv`
- `out/extraction-report.md`

## Validation Check

```bash
python3 -m unittest discover -s tests
python3 public_data_extractor.py sample_pages --out out --base-url https://example.com
```

Expected sample output:

```text
clean=4 rejected=2
```

## Remaining Risk

For a live client site, confirm permission, robots/terms, rate limits, and
ownership before any network automation. This sample intentionally uses local
HTML exports to keep the extraction boundary clear.
