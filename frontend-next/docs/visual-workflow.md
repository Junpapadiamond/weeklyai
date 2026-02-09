# WeeklyAI Frontend Visual Workflow

## 1) Visual Intent Card
- Pick one vibe only (default: experimental / art-tech).
- Define anti-goals: no perfect symmetry, no gray-on-gray dominance, no generic hero copy.
- Lock palette: 1 loud color + 1 weird accent + neutral support.

## 2) Token-First Rule
- Add/update tokens first in `/src/styles/tokens.css`.
- Do not hardcode colors or spacing directly in components.
- Font contract: display/body/mono must come from token variables.

## 3) Controlled Imbalance Rule
- At least one section offset relation (16-32px) per page.
- At least one micro-imperfection detail (sub-degree tilt or overlap).
- Keep readability and interaction hit areas as hard constraints.

## 4) Motion Rule
- Motion must be user-intent driven (hover/click/enter).
- Remove decorative looping animation unless it conveys state.
- Respect `prefers-reduced-motion`.

## 5) Vercel Performance Gate
- `async-parallel`: independent requests in parallel.
- `bundle-conditional`: lazy load secondary sections/components.
- `server-serialization`: avoid sending full datasets on first paint.
- `rerender-lazy-state-init`: expensive initial state via lazy initializer.

## 6) PR Acceptance
- Required checks:
  - `npm run lint`
  - `npm run test`
  - `npm run build`
- Visual QA snapshots at 375 / 768 / 1440 in both light and dark themes.
- Reject merge if UI looks “overly safe” or generic.
