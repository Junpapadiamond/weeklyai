# Exhibition Data

This folder is auto-ingested by `ExhibitionSpider`.

- Add products to the event JSON files (ces.json, mwc.json, ifa.json, gtc.json).
- Set `status` to `active` to include the product in the crawl output.
- Keep `status` as `pending` for placeholders.

Importer (optional):
- Create `crawler/data/exhibitions/sources.json` based on `crawler/data/exhibitions/sources.sample.json`.
- Run `python3 crawler/tools/import_exhibitions.py --sources crawler/data/exhibitions/sources.json --fetch-site`.
- Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` if you want LLM enrichment.

Recommended fields per entry:
- name (required)
- description
- website
- logo_url (press kit or logo.clearbit.com)
- categories (e.g. ["hardware"], ["software"], ["voice"]) 
- event, event_year, booth
- brand, press_url, release_year
- rating, weekly_users, trending_score (optional if unknown)

Example:
```
{
  "status": "active",
  "name": "Example AI Device",
  "brand": "Example Labs",
  "description": "Official exhibitor summary...",
  "website": "https://example.com",
  "logo_url": "https://logo.clearbit.com/example.com",
  "categories": ["hardware"],
  "event": "CES",
  "event_year": 2026,
  "release_year": 2026,
  "press_url": "https://example.com/press"
}
```
