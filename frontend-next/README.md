# WeeklyAI Frontend Next

React + Next.js (App Router) frontend for WeeklyAI.

## Stack
- Next.js App Router
- React 19 + TypeScript
- SWR (client request dedup)
- Zod (API response validation)

## Routes
- `/` Home (dark horses, discovery swipe, trending, leaders)
- `/blog` Blogs and social signals
- `/search` Product search
- `/product/:id` Product detail and related products

## Environment
Copy `.env.example` and set API URLs:

```bash
cp .env.example .env.local
```

Default backend API:
- `http://localhost:5000/api/v1`

## Development
```bash
npm install
npm run dev
```

Default local URL: `http://localhost:3001`

## Quality Checks
```bash
npm run lint
npm run test
npm run build
```

## Migration Notes
This app runs in parallel with legacy `frontend/` (Express + EJS).
Use it as incremental migration target before final cutover.
