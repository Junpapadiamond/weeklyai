# Darkhorse Radar visual identity

## Direction

An independent product publication: a distinctive horse silhouette, radar construction lines, generous reading space, and restrained controls. Product information and sources carry the page. Avoid decorative emoji, sparkle icons, glowing borders, and gradients on navigation or calls to action.

For the Chinese interface, follow [the Chinese UI writing and layout guide](chinese-ui-writing.md). It uses a search-led product directory, native Chinese labels, and compact navigation while retaining this palette and identity. The publication-style introduction remains on the English homepage.

## Existing colors

Keep the colors in `frontend-next/src/styles/tokens.css`:

- Light background: `#fbfaf8`; text: `#1f2937`; accent: `#dc4b5d`.
- Dark background: `#0f1117`; text: `#f8fafc`; accent: `#dd5a68`.
- Keep Plus Jakarta Sans, Noto Sans SC, and JetBrains Mono. Use monospace for small labels, dates, and scores.

## Marks and icons

- `HorseMark` is the theme-aware React brand mark: an angular horse profile and a rose signal dot. Its SVG is decorative when paired with the visible wordmark; the home link supplies its accessible name.
- `RadarEmblem` is the homepage illustration, built from the same silhouette.
- `frontend-next/public/brand/darkhorse-mark.svg` is the transparent vector master for use on light backgrounds.
- `frontend-next/src/app/icon.svg` and `favicon.ico` provide the matching browser icon.
- Interface icons use `@phosphor-icons/react` at its default regular weight. Favorites use a bookmark; assistant controls use a speech bubble. Desktop navigation uses text, while mobile navigation retains icons and labels.
- Product identities still use `SmartLogo`, including their original sources and fallback chain. Never substitute the site mark for a product logo.

## Layout

The homepage pairs its introduction with the radar illustration. Product lists use separated rows; the demo catalog uses two columns on desktop and one on small phones. Desktop discovery places its reading guide beside the swipe deck. Small screens use a single column and a fixed navigation bar, with existing iOS safe areas preserved.

Styles are organized in `brand.css` (shared identity and navigation), `briefing.css` (homepage), and `research.css` (product and secondary page layouts). Respect reduced-motion preferences.

## References reviewed

- [Phosphor Icons](https://phosphoricons.com/) — the implemented icon family.
- [Radix Themes](https://www.radix-ui.com/themes/docs/components) — reviewed for component and accessibility patterns; no Radix dependency was added.
- [Taste Skill](https://www.tasteskill.dev/docs) — the installed `design-taste-frontend` skill informed typography, spacing, and removal of generic ornament.
