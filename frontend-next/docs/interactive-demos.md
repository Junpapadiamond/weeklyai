# Product workflow demos

The new `/demo` gallery lists the discovery catalog with search, pagination, dark-horse and ready filters. Product cards and detail pages also offer **交互试用**. No account or prompt is required. Existing experiences open immediately; missing experiences are generated from the canonical product record and cached for everyone.

These are **WeeklyAI workflow simulations**, with sample data and an always-visible unofficial label. They do not connect visitors to the vendor's account, proprietary model or physical device. Image/voice/hardware products explain the decision workflow; they do not produce the vendor's media or operate a device. App-building examples include a working task app. Visitors can change choices, review evidence, adjust a sample calculation, go back, restart and download their choices as a text brief.

### Visual workspaces (September 2026)

Software workflows now use a fixed React workspace alongside the guided steps. The optional, validated `workspace` field selects `video`, `image`, `search`, `document` or `board`, with bounded bilingual `label` and `initial` text. Existing version-2 experiences use the document workspace without regeneration. Hardware keeps its concept flow.

Video/image workspaces include an editable brief, portrait/landscape controls, selectable storyboard shots and local storyboard playback. Choices and the brief persist across steps and appear in the downloaded text brief. This is an interactive visual concept, not a generated MP4 or a replica of the vendor app. No generated HTML, scripts, arbitrary iframe or remote media runs.

Higgsfield has a reviewed instant profile in `backend/data/demo_profiles/higgsfield.json`, based on its official Marketing Studio page reviewed September 26, 2026. Its scenario is a small shop creating a product ad, with assets → direction → storyboard → handoff. The profile is matched by exact official domain, appears in the ready catalog, supersedes old generic cached content and works without a model or generation credit. Additional product-specific profiles can use the same registry and validation.

On-demand generation has a 55-second total budget, at most two calls including one repair/transient retry, and 3,000 output tokens per call. Shorter copy reduces generation load. The UI reports elapsed time and separates cached lookup from new generation. A live Exa-workspace trial completed in 27.42 seconds with the configured Claude relay; this is one trial, not a latency guarantee. The scheduled pre-generation job shares the production MongoDB budget.

## Content and rendering

- Five authored starters: Exa, Helix Digital Infrastructure, Exaforce, Abridge and Lovable.
- A Black Forest Labs workflow was generated with Claude, then reviewed to remove unsupported output claims.
- Published files live in `backend/data/demos/` and matching `crawler/data/demos/` snapshots. `seed_curated_demos.py` rebuilds authored starters; it never changes product scores or descriptions.
- Model output is versioned bilingual JSON. Python and Zod validate 3–6 steps, bounded copy, allowed widgets and safe source links. The model may only cite supplied catalog URLs. Generated HTML/JavaScript is never executed. Arbitrary remote frames and model-provided media are not rendered.
- Schema validation and narrow claim checks do not establish factual accuracy. On-demand workflows are illustrative, based on catalog metadata rather than live vendor documentation retrieval. Reviewed instant profiles link their checked vendor sources. New generated workflows need editorial review before being promoted as detailed product evaluations.
- A cache key includes the product's stable identity plus a fingerprint of capability/source fields. A score change does not invalidate a demo; a capability change does. Bilingual copy shares one generation.

## API

All routes are under `/api/v1/demos`, via the first-party Next proxy:

| Endpoint | Behavior |
| --- | --- |
| GET /catalog?q=&filter=all&page=1 | Catalog and quota; filters: all, ready, dark |
| GET /status | Configuration readiness and quota, not a live provider health check |
| GET /product/:id | Read cached experience; never calls a model |
| POST /generate | Body: `{ "product_id": "..." }`; cache hit is free |

Generation returns 200 (ready), 202 (another request holds the generation lease), 429 (daily cap), or 503 (configuration/provider/storage failure). The browser polls only the free read endpoint when another request is generating. It does not issue repeated generation requests while polling. Closing the player cancels the browser request; already-started server work may still finish and become a cached experience.

## Daily budget

- Default **3 new generations per anonymous browser per UTC day**.
- Default **20 model attempts across the site per UTC day**, including scheduled preparation.
- Cached playback and interactions are free.
- One reservation starts at most two bounded provider calls (one initial call and one repair/transient retry), capped at 3,000 output tokens each within 55 seconds total.
- Failure refunds personal allowance. The global attempt stays counted because a failed/timed-out request may still incur provider cost.
- A signed, HttpOnly, SameSite=Lax cookie identifies an anonymous visitor. Clearing cookies can reset the personal allowance; the shared global cap is the spend boundary. This is not account-based abuse prevention.
- MongoDB stores shared cache, daily counters and generation leases in separate `demo_*` collections. Atomic conditional updates prevent concurrent overspend. Local development uses a persistent SQLite database in ignored `artifacts/`.
- Production fails closed for paid generation when MongoDB or a stable cookie-signing secret is missing. Published starter experiences still work. Do not use serverless `/tmp` as a shared quota database.

## Provider setup

Configure these **only on the Flask backend**, never as `NEXT_PUBLIC_*`:

| Variable | Recommended tested configuration |
| --- | --- |
| DEMO_API_BASE_URL | https://api.intenext.ai/v1 |
| DEMO_MODEL | claude-sonnet-5 |
| DEMO_API_PROTOCOL | anthropic |
| DEMO_API_KEY | Private provider key |
| DEMO_COOKIE_SECRET | Stable random secret, at least 32 characters |
| MONGO_URI | Existing shared database |
| DEMO_DAILY_USER_LIMIT | 3 |
| DEMO_DAILY_GLOBAL_LIMIT | 20 |

`openai` protocol uses `/chat/completions` and Bearer auth; `anthropic` uses `/messages`, `x-api-key` and version `2023-06-01`. Without a dedicated demo provider, existing research-chat providers remain a compatibility fallback. No automatic second paid attempt occurs on failure.

Local private configuration is in ignored `backend/.env.demo.local`. For standard startup, load that file into the process environment first or put the active values in an ignored backend `.env`. No secret values are committed or returned by the API.

## Daily preparation

`python crawler/tools/pregenerate_demos.py --limit 5` prioritizes missing 4–5 score products and exports validated cache entries. `--dry-run` lists candidates without network or writes; `--product NAME` narrows the batch. Existing entries are reused. The pipeline uses the same MongoDB daily budget as online generation.

Both existing daily pipeline files include this step. GitHub Actions needs the provider secret `DEMO_API_KEY`, the existing `MONGO_URI`, and the matching model/protocol/base URL repository variables. Vercel variables are not automatically available to GitHub Actions. These Actions settings were connected on September 26, 2026. CI skips paid preparation if shared MongoDB is missing. The existing daily schedule is retained.

## Verification

Automated checks cover concurrent limits, same-product deduplication, persistence across store instances, UTC reset, failure refunds, cache-free replay, anonymous cookie isolation, configuration failures, both API protocols, source validation and every published bilingual spec.

Live provider trials on 2026-09-14:

- zjapi / gpt-5.6-sol: minimal request succeeded; full first workflow exceeded 32 seconds.
- intenext / gpt-5.6-sol: minimal request succeeded; full workflow exceeded 45 seconds.
- intenext / claude-sonnet-5: minimal request succeeded; a four-step workflow completed in about 22 seconds.

These are individual connectivity trials, not performance benchmarks. Provider identity/model names are as reported by the relay. Local SQLite paths are tested; the production MongoDB path still needs deployment-environment verification.
