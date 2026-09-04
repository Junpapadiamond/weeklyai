# WeeklyAI deployment and provider setup

The production app is `frontend-next/` (Next.js). `backend/` is a separate native Flask Vercel project. Both deploy from this repository's `main` branch. The `frontend/` Express app is legacy.

| Setting | Where | Purpose |
| --- | --- | --- |
| `API_BASE_URL_SERVER` | Vercel **weeklyai**, Production and Preview | `https://backend-seven-ecru-62.vercel.app/api/v1` |
| `PERPLEXITY_API_KEY` | Vercel **backend**, Production and Preview | Research chat; the key needs usable Sonar credits |
| `PERPLEXITY_CHAT_MODEL` | Vercel **backend** | `sonar` by default |
| `MONGO_URI` | Vercel **backend** and GitHub Actions secrets | Atlas connection string from the current cluster, with credentials URL-encoded |
| `MONGO_DB_NAME` | Backend environment / Actions repository variable | Defaults to `weeklyai` if the URI has no database |
| `PERPLEXITY_API_KEY` | GitHub Actions secrets | Search and Sonar access for daily global discovery |
| `PERPLEXITY_MODEL` | GitHub Actions secrets, optional | Defaults to `sonar` |
| `ZHIPU_API_KEY` | GitHub Actions secrets, optional | China discovery through GLM; Perplexity is the fallback if absent |
| `GLM_MODEL` | GitHub Actions secrets, optional | Defaults to `glm-4.7` |

Browsers call `/api/v1` on their own origin. API keys belong on the backend or in Actions secrets, never in `NEXT_PUBLIC_*`. The old `NEXT_PUBLIC_API_BASE_URL` remains a server-side compatibility fallback; new setups should use `API_BASE_URL_SERVER`. Redeploy the affected Vercel project after changing its environment.

For local development, start Flask on port 5000 and Next on port 3001. The server API base defaults to `http://127.0.0.1:5000/api/v1`. MongoDB is optional: the committed `backend/data` snapshot supports browsing, search and favorites without credentials.

## Check a new provider key

From the repository root, with the crawler dependencies installed and credentials set in your environment or `.env`:

```sh
python crawler/tools/check_providers.py
python crawler/tools/check_providers.py --live
```

The first command checks configuration. `--live` makes one small request to each configured provider API and checks access, response shape and credits. It logs no key values or raw provider bodies. The daily workflow runs it before discovery and fails if discovery produces no accepted records. Optional enrichment may still fail independently; review its logs. No new products is an actionable pipeline result, not proof of a successful refresh.

## MongoDB repair and sync

If the Atlas SRV hostname returns NXDOMAIN, obtain the connection string from the active Atlas cluster before changing network access. An IP allowlist cannot repair a missing hostname. Confirm the cluster exists and is available.

Add the current computer's IP through Atlas Network Access for local development. Production also needs access from Vercel's outbound network; the computer's IP does not cover Vercel. Use the project's configured static egress addresses or private connectivity as appropriate. Keep credentials out of commits and reports.

```sh
python crawler/tools/sync_to_mongodb.py --blogs
```

This upserts the curated products and news without clearing collections. The same command runs after a successful daily snapshot publication when the Actions `MONGO_URI` secret is configured. Existing numeric links are retained through `product_legacy_ids.json`; new product identifiers are deterministic and URL-safe.

Check `GET /api/v1/health` on the frontend or backend. `storage: "snapshot"` is a working fallback, not a successful Mongo connection. `chat_configured: true` means a key is present; the live provider check is needed to prove access and credits. `product_last_updated` is the newest product discovery, separately from news synchronization.

## Release verification

CI checks the active Next app with lint, TypeScript, Vitest and a production build. Python regression tests cover API behavior, discovery, storage and data handling. Product/news deployment snapshots must match their crawler copies. After release, verify both Vercel production aliases point to the intended Git commit, then exercise search, details, favorites, discovery, news and chat.

The current request limit is per Python process. A strict account-wide spending cap must be set with the provider; multi-instance Vercel limits need shared storage if traffic grows.
