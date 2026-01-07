# Company Product Data

This folder is auto-ingested by `CompanySpider`.

- Add a JSON file per company (e.g., lg.json, tcl.json, asus.json).
- Set `status` to `active` to include the product in the crawl output.
- Keep `status` as `pending` for placeholders.

Importer (optional):
- Create `crawler/data/companies/seeds.json` based on `crawler/data/companies/seeds.sample.json`.
- Run `python3 crawler/tools/import_companies.py --seeds crawler/data/companies/seeds.json --fetch-site`.
- Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` if you want LLM enrichment.

Recommended fields per entry:
- name (required)
- description
- website
- logo_url
- categories (e.g. ["hardware"], ["software"], ["voice"]) 
- brand, press_url, release_year
- rating, weekly_users, trending_score (optional if unknown)

Example:
```
{
  "status": "active",
  "name": "Example AI Device",
  "brand": "Example Labs",
  "description": "Official product summary...",
  "website": "https://example.com",
  "logo_url": "https://logo.clearbit.com/example.com",
  "categories": ["hardware"],
  "release_year": 2026,
  "press_url": "https://example.com/press"
}
```
