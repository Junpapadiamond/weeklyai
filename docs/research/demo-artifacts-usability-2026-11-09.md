# Prepared artifact usability — 2026-11-09

## Task contract

The visitor compares a product's prepared input and complete result; the input is a supplied example/preset, the first visible result includes every short list or sequence item, the content remains an independent fictional illustration rather than vendor execution, and the next action is to compare another example, optionally arrange/save notes, or visit the official product.

## Observed problems

1. Clutch Security (`/product/p_16ab841852cd830c`): the default result hides one of two permission categories behind a second selector. The row selection changes only the paragraph being read, while prominent note/download controls resemble the product task.
2. Clutch Security: choosing Code Analysis Agent, then Set Operational Boundaries, then Review Access Logs shows support-ticket logs unrelated to the selected role. This is a content/dependency issue, handled separately from the generic renderer.
3. Higgsfield (opened through `/demo`): only the first of three short storyboard descriptions is visible. Reordering and downloading are presented before visitors can read the whole proposed sequence.

## Change

Show all supplied titles and details together, with visible order for sequences. Keep optional note selection and sequence editing behind a single control. Exports retain the independent-example disclosure and source links; the renderer does not invent new content or claim to run the vendor product.

## Evidence and limits

Current production was inspected through an independent Chrome tab after the in-app browser reported unavailable. Screenshots are stored outside the repository in the current chat's `demo-audit` folder (`01-clutch-before.png`, `02-higgsfield-before.png`). These are agent walkthrough observations, not a first-time human comprehension study.

## Verification

- `demo-presentation.test.ts`: 18 tests passed, including complete list/sequence details, preserved arranged order, and both languages across committed cache branches. Targeted ESLint passed.
- At `localhost:3011`, Higgsfield shows all three prepared shot descriptions on opening. Moving the first shot to second position preserves focus and updates the displayed order.
- The downloaded text was inspected: its order matches the arranged view, with all three descriptions, the independent-fictional-example disclosure, and the product source URL intact.
- At the narrow viewport, text wraps without horizontal overflow and the complete sequence remains available by normal page scrolling. Reordering announcements are visually hidden and retained for assistive technology.
- After screenshots: `03-higgsfield-after.png` and `04-higgsfield-mobile.png` in the same evidence folder. Automated and agent checks do not establish first-time visitor comprehension.
