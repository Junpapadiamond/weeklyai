# Clutch access example — 2026-11-09

## Task contract

1. A visitor should understand how task-scoped access lets an AI assistant finish necessary work without receiving every credential or unrestricted production access.
2. The visitor chooses either a test-database troubleshooting task or an assigned customer's billing question, then chooses one of four concrete requests. Only the necessary protected request offers a scoped, simulated authorization.
3. Opening shows a request for non-secret test configuration and the readable configuration it returns. Changing a request immediately shows allowed, authorization required, or denied, with the reason and fictional returned content.
4. This is a deterministic local rules example with fictional data. No company system or Clutch API is connected. Credential use through a connection layer is an illustrative policy, not a verified claim about Clutch's internal implementation. Official pages support the general concepts of contextual guardrails and least privilege only.
5. The visitor can compare a necessary request with an out-of-scope one, revoke the sample grant, switch tasks, and open official product documentation.

## Scope and behavior

- Non-secret environment values and deployment configuration can be necessary; they are not blanket secrets.
- A test-only connection or the assigned customer's payment status needs its own temporary sample grant. Granting it does not permit credential disclosure, production access, full card numbers, or unrelated customer records.
- Switching tasks revokes the sample grant and selects the new task's first request. Language changes preserve task, request, and authorization state.
- No real credentials, accounts, network requests, credits, or vendor output are involved in these local interactions.
- Only the stable Clutch product ID uses this renderer. Other products retain their own activity.

## Evidence and verification

- Current production walkthrough: Abridge has a meaningful source-selection → editable note interaction. Clutch instead switches prepared paragraphs and bookmarks snippets; its code-agent preset claims all environment variables and deployment configuration should be blocked. The interaction does not show a request or a consequence.
- Production Abridge language switching resets selected sources; this is a separate finding and not evidence that the new Clutch activity shares that behavior.
- Sources: https://www.clutch.security/agentic-ai/agent-guardrails and https://www.clutch.security/use-cases/least-privilege-enforcement .
- Unit checks must cover scoped authorization and denial boundaries. Browser checks must cover both tasks, authorization/revocation, language state preservation, narrow layout, and keyboard controls.
- Agent walkthroughs and automated checks do not establish first-time human comprehension or validate Clutch's real behavior.

### Local verification completed

- Browser: `/product/p_16ab841852cd830c?demo=1` at localhost:3011. Initial test configuration is visible, without clicking through setup.
- Necessary test connection: authorization required → scoped grant → fictional port mismatch result. Selecting production with the test grant still returns denied.
- Language switch to English preserves the selected production request and test grant. Switching to the billing task clears the test grant.
- Keyboard ArrowDown moves from assigned bill to payment status; status requires its own grant. Granting shows paid; revoking removes that result and returns to authorization required.
- Narrow viewport override: all controls and result stack vertically. Browser reported 355 px inner width and 341 px document scroll width; no horizontal overflow. Other-customer access returns denied. Temporary viewport override was reset.
- Five behavior tests pass, covering allowed non-secret config, task-specific grants, revocation, forbidden requests after grants, bilingual results, and invalid-request handling. Targeted ESLint passes.
