# AI news platform integration

- User task: scan current AI discussions and announcements across platforms.
- Input: choose a platform and, optionally, a region.
- First result: dated headlines with original links, fetched for that platform rather than filtered from the mixed preview.
- Evidence: RSS excerpts and platform API records; search-index excerpts have a visible label. Missing dates are excluded, and old items retain their original dates.
- Next action: read the source or switch platforms.

`refresh_news.py` runs RSS endpoints and Hacker News independently with bounded requests and checkpoints each result. X uses the configured Tavily/Exa search with three individual watchlist-account queries (the first account plus two rotating accounts); other platforms use search only when direct feeds yield no qualifying items. Maximum nine basic search requests per run, no model calls. All platforms retain up to 60 dated records for 30 days, so a noisy source cannot evict every other platform. Search provider failures do not reset dates or substitute invented content.

The daily pipeline and dedicated news workflow use the same collector. `news_source_health.json` records direct/search/retained/unavailable states, counts, and sanitized endpoint failures. Public status exposes only state and dates. A retained snapshot is not evidence that the source refreshed successfully.

MongoDB publishes the full feed and health together in `news_snapshots/current`. The API chooses the newest complete database or bundled publication, so old legacy blog upserts cannot hide new platform feeds. Legacy collections remain intact. Reddit uses one combined subreddit RSS request to reduce rate-limit pressure.

Regression checks cover canonical links, missing/future dates, source retention, failed endpoints, indexed evidence and platform-specific queries. Browser checks establish rendering and interactions; first-time user comprehension remains untested.

## Publication quality (2026-10-29)

The visitor's task is to find a relevant release, research result, practical implementation or industry development, then inspect its source. The existing platform controls lead to dated original links; RSS, community posts and indexed excerpts remain distinct evidence types. No quality score or factual-verification badge is shown.

- `utils/news_quality.py` gates both new candidates and retained records. Historical data cannot bypass a tightened policy. Titles and article leads establish AI relevance; video descriptions cannot qualify a video through sponsor text. Generic chips, agents, phone promotions and unrelated footer mentions do not qualify.
- Personal support questions, chatter, promotional titles and community rumor headlines are rejected. Community items need a concrete technical/development signal and either an outbound evidence link or a substantive original description. There is no vote/popularity minimum, preserving early projects. These deterministic rules may still miss good content or admit weak content; they are not semantic fact-checking.
- X search excerpts must have an exact status permalink from the configured account watchlist, a concrete signal with sufficient post-title text, and a date matching the status ID. Only the indexed post title is displayed: search-body fragments can mix replies, quoted posts and login text and are discarded. Link-only and vague promotional posts are rejected. An account's own claim is still a claim; search-index coverage is incomplete and is not full-post verification.
- Missing provenance, malformed permalinks, unknown dates and records older than 30 days are excluded. Exact headline duplicates are collapsed within a platform (across publishers for media); identical Hacker News external article links are also collapsed. Distinct titles/model versions are not fuzzily merged.
- RSS navigation/footer text is removed; actual feed title, author and outbound evidence links are preserved. Each run's source-health artifact includes rejected counts, reason breakdowns and bounded examples, including when rejected direct results trigger search fallback. `quality_policy_version` is persisted with accepted items.

Validation includes real before/after samples (unrelated math clips, general phone/finance news, Reddit help posts and unvetted X summaries), deterministic regression tests and a fresh collection run. Passing these gates establishes provenance and publication eligibility, not the truth of every third-party claim or first-time reader comprehension.
