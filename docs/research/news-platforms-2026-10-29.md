# AI news platform integration

- User task: scan current AI discussions and announcements across platforms.
- Input: choose a platform and, optionally, a region.
- First result: dated headlines with original links, fetched for that platform rather than filtered from the mixed preview.
- Evidence: RSS excerpts and platform API records; search-index excerpts have a visible label. Missing dates are excluded, and old items retain their original dates.
- Next action: read the source or switch platforms.

`refresh_news.py` runs RSS endpoints and Hacker News independently with bounded requests and checkpoints each result. X uses the configured Tavily/Exa search; other platforms use search only when direct feeds yield no recent items. Maximum seven basic search requests per run, no model calls. All platforms retain up to 60 dated records for 90 days, so a noisy source cannot evict every other platform. Search provider failures do not reset dates or substitute invented content.

The daily pipeline and dedicated news workflow use the same collector. `news_source_health.json` records direct/search/retained/unavailable states, counts, and sanitized endpoint failures. Public status exposes only state and dates. A retained snapshot is not evidence that the source refreshed successfully.

MongoDB publishes the full feed and health together in `news_snapshots/current`. The API chooses the newest complete database or bundled publication, so old legacy blog upserts cannot hide new platform feeds. Legacy collections remain intact. Reddit uses one combined subreddit RSS request to reduce rate-limit pressure.

Regression checks cover canonical links, missing/future dates, source retention, failed endpoints, indexed evidence and platform-specific queries. Browser checks establish rendering and interactions; first-time user comprehension remains untested.
