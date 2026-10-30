# Vercel deployment footprint

Production uses two projects in JunHsu's projects, both on `main`:
`weeklyai` has Root Directory `frontend-next`; `backend` has Root Directory `backend`.

## Build scope

Each project's `vercel.json` compares its own directory and the root
`.vercelignore` against `VERCEL_GIT_PREVIOUS_SHA`, the previous successful
deployment. This includes changes across multiple commits, so an intervening
crawler-only commit cannot hide an earlier application change.

- A frontend change builds the frontend.
- A backend code or bundled snapshot change builds the backend.
- Crawler-only, documentation and tooling changes skip both builds.
- The first deployment, an unavailable comparison commit or a Git error builds
  conservatively. Set `VERCEL_FORCE_BUILD=1` for an intentional rebuild without
  source changes (for example after changing environment variables).

The Ignored Build Step saves build work, **not deployment quota**: Vercel still
counts canceled builds toward deployment and concurrency limits. Batch related
edits into one push when that quota is the bottleneck. Native unaffected-project
skipping requires a JavaScript workspace; this mixed Next.js/Flask repository
does not introduce one just for deployment.

## Upload scope

The root `.vercelignore` excludes agent tool copies, audit output, crawler code,
the legacy frontend, mobile sources and local dependencies from root CLI uploads.
Both projects use this single root file: project-level ignore files would take
precedence and could omit these shared exclusions. Keep deploying the two
existing projects with their respective root directories.

All frontend `public/logos` files, the generated logo manifest, backend data
snapshots and generated demos remain included. The crawler retains its optional
MySQL dependency; the Flask API does not use MySQL and no longer installs its
connector.

On the 2026-10-30 local tracked-file inventory, the root upload selection changed
from 1,648 files / 48,859,304 bytes to about 9.3 MB before adding
these configuration files. This is an upload-selection estimate, not a measured
reduction in a Vercel Function bundle or Git history.

References:
- https://vercel.com/docs/project-configuration/project-settings#ignored-build-step
- https://vercel.com/docs/deployments/vercel-ignore
- https://vercel.com/docs/monorepos
