# Realtime product demos — research and design

Status: research complete, not implemented. Branch `claude/realtime-product-demos-d8axpr`.
Date: 2026-09-06.

Goal as stated: publish ~5 demos per day that render the experience of a selected dark horse
product in real time, so a PM understands what the product does without reading docs, visiting
the vendor site, or setting up an account. Reduce information load; make it interactive and
immersive.

---

## 1. Verdict

The idea is sound and the whitespace is real — nobody builds third-party demos of products they
do not own. But the shape you described ("we get Exa, we render a demo of it") only works for
about **11% of your catalog**, and the naive version of the other 89% is a fabricated UI with a
real company's name on it, which would break the editorial voice this site has spent its
existing code enforcing.

The version worth building is not *a demo of the product*. It is **a playable explanation of the
job the product does** — which covers the whole catalog, is honest, is cheaper, and is something
the vendor structurally cannot publish about itself.

Two findings drive everything below:

1. **Supply.** Measured against `crawler/data/products_featured.json`, only 61 of 567 dark horses
   (4–5分) can host a genuine live sandbox. 45% are physical hardware.
2. **Prior art.** The entire interactive-demo industry (Arcade, Storylane, Supademo, Guideflow,
   Demoboost, Demosmith, Consensus, Rivia, HowdyGo) is **first-party only** — the vendor makes
   the demo of their own product. That is the gap. It is also the reason the gap exists.

---

## 2. The supply problem — measured, not assumed

Classification of all 567 dark horses (`dark_horse_index >= 4`) by whether a demo is even
physically possible. Heuristic keyword pass over name/description/why_matters/categories, so
treat as ±10%, but the shape is unambiguous:

| Tier | What it is | Count | Share | Days of content @5/day |
|---|---|---|---|---|
| **D0** physical | Robots, chips, wearables, vehicles, datacenters, fusion | 255 | 45.0% | — (undemoable) |
| **D2** simulatable SaaS | B2B agents, vertical workflow tools | 196 | 34.6% | 39 |
| **D3** API-sandboxable | Dev tools with public APIs | 61 | 10.8% | **12** |
| **D9** unclear | Needs manual triage | 42 | 7.4% | 8 |
| **D1** deeptech/bio | Protein design, clinical, materials | 13 | 2.3% | — |

Reproduce with the classifier in §11.

### What this means

- **Your Exa example is the best case and the rarest case.** D3 is 61 products total — 12 days of
  content, then the well is dry. New inflow is ~5 dark horses/day of which ~11% are D3, i.e.
  roughly **one genuinely sandboxable product every two days**. You cannot run a 5/day live-sandbox
  pipeline off this catalog.
- **Hardware is your largest single bucket (45%) and your most distinctive one.** It is also where
  "realtime render the product experience" is meaningless. An interactive demo of a humanoid robot
  or a fusion reactor does not exist. Sampled dark horses include Apptronik, Rebellions, WeRide,
  Helical Fusion, Repebble, Orphe, GigaIO, Fairy Devices, XCENA, Kitto AI Cat.
- **The 5/day target is only reachable if the definition of "demo" covers D0.** Which is the
  reframe in §4.

---

## 3. Prior art

### 3a. The interactive-demo category (mature, well funded, first-party)

| Product | What it does | Whose product |
|---|---|---|
| [Arcade](https://www.arcade.software/post/ai-demo-generator) | Screen recording → AI narration, captions, hotspots → interactive walkthrough | Yours |
| [Storylane](https://www.storylane.io/) | Captures screens, builds guided walkthroughs; embeds on homepage/G2 | Yours |
| [Supademo](https://supademo.com/) | Guided demos, sandbox environments, AI demo agents | Yours |
| [Guideflow](https://www.guideflow.com/) | AI auto-adjusts steps, popups, translations, voiceovers, avatars | Yours |
| [Demoboost](https://demoboost.com/) | Demo automation for sales teams | Yours |
| [Demosmith](https://demosmith.ai/) | **Browser agent navigates your UI from a product URL** and records it | Yours |
| [Consensus](https://goconsensus.com/blog/ai-product-demo-assistants) | AI demo assistants for buyer qualification | Yours |
| [Rivia.ai](https://rivia.ai/) | AI-powered product growth / demo platform | Yours |

Every one of these assumes you have credentials to the product. Demosmith is the closest to what
you want technically — point an agent at a URL and it clicks through — but it is sold to the
product's own team, and pointed at a stranger's app it will hit a signup wall on step one.

**Conclusion: this category is not a competitor. It is a supplier.** If you go the partnership
route (§8), the vendors you cover may already have an Arcade or Storylane demo you can embed with
one email.

### 3b. Live-demo directories (adjacent, first-party publishing)

- **Hugging Face Spaces / Replicate / [fal.ai sandbox](https://fal.ai/sandbox)** — the closest
  working analog: browse a catalog, run the thing in-browser, no setup. But the *model author*
  publishes the demo, and it only works because models are stateless functions with a
  standard interface. Your catalog is companies, not models.
- **AI directories** — [There's An AI For That](https://theresanaiforthat.com), Futurepedia,
  [Uneed](https://www.uneed.best/blog/uneed-a-product-hunt-alternative),
  [StartupBase](https://startupbase.io/blog/product-hunt-alternatives), Product Hunt. All static:
  logo, blurb, outbound link. Exactly the information-load problem you are describing. None of
  them render anything.

### 3c. Generative simulation (the closest technical precedent)

[WebSim](https://www.producthunt.com/products/websim) hallucinates entire interactive websites
from a prompt or an imagined URL, generating HTML/CSS/JS on the fly (originally Claude-backed).
This is precisely the technology for your D2 tier — and precisely the risk. WebSim gets away with
it because it is framed as *fiction*. The moment the same output carries a real company's name on
a site that positions itself as a research briefing, it stops being fiction and starts being a
claim.

### 3d. Whitespace

Nobody publishes third-party interactive demos of products they do not own. Two structural
reasons, both solvable but neither free:

1. You need product access → solved by simulation, permission, or public APIs.
2. Trademark and ToS exposure → solved by labeling, framing, and permission (§7, §8).

---

## 4. The reframe

> Do not build a demo of the product. Build a playable explanation of the job the product does.

The difference is not cosmetic:

| "Demo of the product" | "Playable explanation of the job" |
|---|---|
| Recreate their UI | Show the input, the output, and the difference |
| Fails on 45% of catalog | Works on 100% |
| Trade-dress + confusion risk | Nominative fair use, clearly commentary |
| Hallucinated UI details are lies | Illustrative scenarios are honestly labeled |
| Vendor could publish it better | **Vendor structurally cannot publish it** |

The last row is the whole business. A vendor will never show you their tool side by side with two
competitors on the same input. You can. That is the only durable moat here (§9).

For Exa specifically: do not fake Exa's dashboard. Show one query running through keyword search
and through neural search, side by side, with the result sets diffed. A PM learns more about why
Exa exists in 20 seconds from that than from an hour in Exa's docs — and it is a comparison Exa's
own marketing site cannot credibly make.

---

## 5. The four-tier demo ladder

One pipeline, one renderer, four demo kinds. Tier is a field, not a separate product.

### Tier 1 — Live sandbox (`sandbox`)
Real API calls through a server-side proxy with our key. Coverage **~11% (61 products)**.
- **Value:** highest. It is actually the product.
- **Cost:** the only tier with unbounded runtime cost.
- **Risk:** ToS. Many API terms prohibit sublicensing, proxying, or making the service available
  to third parties, and reserve the right to revoke keys for it. **Read the ToS per product; do
  not assume.** Prefer explicit permission (§8).
- **Cost control that matters:** ship *preset queries with cached results* first. Five curated
  queries, responses cached at generation time, rendered with realistic latency. This delivers
  ~95% of the perceived value at ~1% of the cost and is indistinguishable from live for most
  visitors. "Run your own query" becomes a rate-limited, gated upgrade — reuse the per-IP limiter
  already in `backend/app/routes/chat.py`.

### Tier 2 — Scripted simulation (`simulation`)
A generated, clearly-labeled mock of the workflow. Coverage **~35% (196 products)**.
- Neutral chrome. **Never** the vendor's logo, colors, or trade dress inside the mock.
- Persistent badge: *"Illustrative reconstruction — not the real product, not affiliated."*
- Every number shown must trace to a cited source or be visibly marked as example data.

### Tier 3 — Concept explorer (`concept`)
No UI mimicry at all — an interactive diagram, spec comparison, or scenario explorer.
Coverage **~47% (D0 + D1, 268 products)** — your biggest bucket, and the one everyone else skips.
- Humanoid robot: sortable spec matrix vs two named competitors, cost-per-unit slider.
- Inference chip: throughput/watt dial vs an H100 baseline, sourced.
- Fusion or biotech: a stepped pipeline explaining where in the value chain this company sits.
- This tier is *more* defensible than Tier 2 because it makes no claim about a UI at all.

### Tier 4 — Annotated tour (`tour`)
Fallback. Screenshot with numbered hotspots. Reuses `WebsiteScreenshot` and the existing
thum.io integration in `frontend-next/src/components/common/website-screenshot.tsx`, including its
quality-detection fallback. Cheapest, always available, never wrong.

**Daily mix to hit 5/day sustainably:** 0–1 sandbox, 2 simulation, 2 concept, remainder tour.

---

## 6. Architecture

### 6a. The core call: the model emits a spec, never code

The LLM must **never** emit HTML or JavaScript. It emits JSON validated against a Zod schema; a
hand-written React renderer draws it. This is the single most important decision in the design.

Reasons: no XSS surface; output stays inside your design system; specs are diffable and reviewable
in ~30 seconds each; regeneration is cheap; the widget set is unit-testable; and a malformed
generation fails validation instead of shipping a broken page. You already have Zod
(`frontend-next/src/lib/schemas.ts`) and the validate-then-default discipline in
`auto_discover.py` — this is the same pattern.

```ts
DemoSpec = {
  version: 1,
  product_slug: string,
  tier: "sandbox" | "simulation" | "concept" | "tour",
  title:   { zh: string, en: string },
  premise: { zh: string, en: string },   // the job it does, 1–2 sentences
  steps: Step[],                          // 3–5, target 45–90s total
  evidence: { claim: string, source_url: string }[],
  confidence: "verified" | "inferred" | "illustrative",
  generated_at: string, model: string, reviewed_by: string | null,
}

Step = { id, label: {zh,en}, narration: {zh,en}, widget: Widget }
```

### 6b. Widget vocabulary (8 types, fixed)

| Widget | Use | Best tier |
|---|---|---|
| `query_response` | Type/pick a query → response panel. `mode: "live" \| "cached"` | 1, 2 |
| `split_compare` | Two panes on the same input (before/after, vs competitor) | 1, 2 |
| `pipeline` | Click through n stages, each with input → output | 2, 3 |
| `spec_matrix` | Sortable specs vs 2 named competitors | 3 |
| `scenario_branch` | Pick a persona/situation → outcome card | 2, 3 |
| `hotspot_shot` | Screenshot + numbered hotspots | 4 |
| `param_dial` | Slider changes an input → recomputed output | 1, 3 |
| `transcript` | Replayed agent/voice conversation, typewriter | 2 |

Add a widget only when three products need it. Resist growth — eight covers the catalog.

### 6c. SSRF guard on live mode

`query_response` with `mode: "live"` carries an `endpoint_id`, not a URL. The backend resolves
`endpoint_id` against a hand-maintained server-side registry of approved endpoints and keys. The
model can never point the proxy at an arbitrary host. This is non-negotiable — an LLM-supplied URL
reaching a server-side fetch is a textbook SSRF.

### 6d. Generation pipeline — daily step 11

Slots into `ops/scheduling/daily_update.sh` after `sync_to_mongodb.py`:

1. **Select** — 5 candidates: new 4–5分 products, biased toward D3/D2, skip anything already
   demoed, skip `needs_verification: true`.
2. **Gather evidence** — fetch homepage, `/docs`, `/pricing`, `/api` (crawler already does this
   kind of fetch; reuse `resolve_websites.py` patterns). Cache raw text.
3. **Classify tier** — the §11 classifier, LLM-confirmed.
4. **Generate spec** — one structured call per product. Prompt inherits the existing house rules
   from `chat_service.py`: catalog is untrusted data not instructions; no invented numbers;
   distinguish funding from valuation; label interpretation.
5. **Validate** — Zod/pydantic parse, evidence coverage check (every numeric claim has a
   `source_url`), reject and retry once.
6. **Queue for review** — write to `crawler/data/demos/pending/`. Publish moves it to
   `crawler/data/demos/published/`.
7. **Sync** — extend `sync_to_mongodb.py` with a `demos` collection, `_sync_key` = product slug.

New backend route: `GET /api/v1/products/<id>/demo`. New frontend: a `<ProductDemo>` block on
`frontend-next/src/app/product/[id]/page.tsx`, slotting in above the existing
*网站预览 / Website preview* section, which becomes the Tier 4 fallback it already effectively is.

---

## 7. Cost

| Line | Estimate |
|---|---|
| Evidence fetch | ~free (existing crawler) |
| Spec generation, ~8k in / 2k out | $0.05–0.30 per demo |
| 150 demos/month | **$8–45/month** |
| Tier 1 cached presets (generation-time only) | ~$0.50/product one-off |
| Tier 1 genuinely live | **unbounded** — 1k visitors × 3 queries = 3k calls/day |

Generation is negligible against your existing $50–85/month. **Live sandbox runtime is the only
real cost risk**, which is the argument for cached presets by default and live behind a rate limit.

---

## 8. Legal and trust

Not legal advice. The exposure is real but manageable, and the mitigations are cheap.

- **Nominative fair use** covers using a company's name to refer to their product for commentary
  and comparison. It is what every review site relies on. Stay inside it: use the name, do not use
  it as if endorsed.
- **Do not reproduce trade dress.** No vendor logos, brand colors, or replica UI chrome inside a
  Tier 2 simulation. This is the line between commentary and imitation.
- **Label every non-live demo, persistently and visibly**, in both locales. Not a footnote — a
  badge that stays on screen: *"Illustrative reconstruction. Not the real product. Not affiliated
  with or endorsed by [X]."*
- **Never imply affiliation or partnership** unless one exists.
- **Publish a takedown path and honor it within 48h.** One page, one email address, a documented
  SLA. This single artifact converts most disputes into an email.
- **Tier 1 ToS.** Proxying a third-party API to the public is the highest-risk action in this
  whole design and the one most likely to be explicitly prohibited. Read each ToS. Prefer
  permission.

### The coherence problem — raise this with yourself before building

This codebase is unusually careful about epistemics. `chat_service.py` instructs the model to
avoid invented numbers and label interpretation. The product page renders *"This record needs
verification. Check the original source."* The audit doc's stated goal is *"truthful evidence."*

A fabricated UI with a real company's name on it is in tension with all of that. Tiers 1, 3, and 4
are fully consistent with the existing voice. **Tier 2 is the one that needs a deliberate
decision**, not a default. If you are not comfortable publishing it, drop Tier 2 and lean on
concept explorers — you lose 35% coverage and keep 100% of your credibility. That is a real
option, not a consolation prize.

---

## 9. The two strategic moves

### 9a. Flip the legal risk into a distribution channel

You are covering seed-stage companies. **They want this.** A free interactive demo on a
PM-focused discovery site is distribution they would otherwise pay Storylane for.

So: generate the demo, then email the company. *"We built an interactive explainer for your
product. It's live here. Corrections welcome — and if you'd like it to run against your real API,
send us a sandbox key."*

This single motion:
- converts trademark exposure into a relationship,
- solves the Tier 1 API-key problem for free,
- upgrades demos from simulation to sandbox over time,
- creates a proprietary asset (vendor-corrected demos) nobody can scrape,
- and opens a warm channel to ~150 AI startups a month.

Do this from day one, not after a complaint. The email is the product.

### 9b. Comparison is the moat, not the demo

A single demo of one product competes with that product's own homepage — which is better funded,
better designed, and more accurate than anything you generate. You lose that fight.

**Three products, same input, side by side** is a fight no vendor can enter. Exa vs Perplexity API
vs Brave Search on one query. Three humanoid robots on one spec matrix. Three voice agents on one
call transcript.

This also fixes your supply problem: 61 D3 products is only 12 days of *individual* demos, but the
comparison sets are combinatorial and the shelf life is months, not days. If you build one thing
from this document, build `split_compare` and `spec_matrix` first.

---

## 10. Ramp and metrics

Recommendation: **5/day is the right target and the wrong starting point.** Getting there through
a hand-built ramp costs four weeks and de-risks everything; starting there ships 150 unreviewed
LLM reconstructions of real companies in month one.

| Phase | Scope | Exit criterion |
|---|---|---|
| **1 (wk 1–2)** | Hand-author 5 demos. 3 widgets: `query_response` (cached), `split_compare`, `hotspot_shot`. No pipeline. | Outbound CTR on demoed products beats non-demoed |
| **2 (wk 3–4)** | `DemoSpec` + generator + review queue. 1/day, every one human-reviewed. | Review takes <3 min; <1 in 10 rejected |
| **3 (mo 2)** | Scale to 5/day. Add `spec_matrix`, `pipeline`, `transcript`. Tier 3 covers hardware. | 5/day sustained, correction rate ~0 |
| **4 (mo 3)** | Tier 1 live for 3–5 permissioned products. Launch comparison sets. | ≥3 vendors have supplied sandbox keys |

**Metrics.** Primary: outbound click-through to the vendor site, demoed vs not — that is the
honest test of "reduced the load enough to make them want to try it." Secondary: demo completion
rate (reached final step), time-to-first-interaction. **Guardrail: factual corrections received
per 100 published demos — if this is not near zero, stop and fix generation before scaling.**

Watch for the failure mode where a good demo *replaces* the visit rather than causing it. If CTR
drops while engagement rises, the demo is too complete — pull it back to a teaser.

---

## 11. Reproducing the classification

```bash
cd /path/to/weeklyai && python3 - <<'PY'
import json, collections, re
items = json.load(open('crawler/data/products_featured.json'))
dh = [p for p in items if (p.get('dark_horse_index') or 0) >= 4]
PHYS = r"robot|humanoid|chip|semiconductor|wafer|silicon|gpu|lidar|drone|vehicle|autonomous driving|robotaxi|wearable|pendant|glasses|earbud|watch|camera|sensor|battery|fusion|reactor|datacenter|data center|energy|satellite|manufactur|factory|hardware|device|printer|exoskeleton|prosthe|actuator|motor|npu|accelerator|机器人|芯片|硬件|设备|传感器|无人|电池|制造|穿戴"
BIO  = r"protein|molecul|drug discovery|biotech|genom|antibod|clinical trial|therapeut|lab automation|crispr|bioinformat|材料|药物|蛋白|基因|临床"
DEV  = r"\bapi\b|sdk|developer|inference|open source|open-source|llm serving|embedding|vector|retrieval|search api|agent framework|observability|eval|fine-tun|deploy|开发者|接口"
APP  = r"platform|assistant|agent|copilot|workflow|dashboard|automate|automation|chat|generat|write|design|analy|crm|support|sales|marketing|legal|accounting|recruit|scribe|note|meeting|平台|助手|智能体|自动化|生成"
def blob(p): return " ".join(str(p.get(k,"")) for k in ("name","description","description_en","why_matters","why_matters_en","categories","hardware_category")).lower()
def classify(p):
    b = blob(p)
    if p.get("is_hardware") or "hardware" in (p.get("categories") or []) or re.search(PHYS,b): return "D0_physical"
    if re.search(BIO,b): return "D1_deeptech_bio"
    if re.search(DEV,b): return "D3_api_sandboxable"
    if re.search(APP,b): return "D2_simulatable_saas"
    return "D9_unclear"
c = collections.Counter(classify(p) for p in dh)
for k,v in c.most_common(): print(f"{k:24}{v:5}{v/len(dh)*100:6.1f}%")
PY
```

---

## 12. Not verified in this session

Stated so nobody treats these as established:

- **Exa's current API surface, free tier, and ToS.** `exa.ai` is blocked by this session's egress
  policy. Everything said about Exa here is from prior knowledge and the worked example in §4 is
  illustrative. Confirm endpoints, free credits, and proxying terms before building against it.
- **iframe embeddability of vendor sites.** Intended to test `X-Frame-Options` and CSP
  `frame-ancestors` across 45 sampled dark horses; all 45 returned 403 from the egress proxy, not
  from the sites. Re-run locally before assuming any iframe path works. Expectation is that it
  mostly does not — modern SaaS blocks framing, and even unblocked sites break on `SameSite`
  cookies, auth walls, and consent modals. This is why the design does not depend on iframes.
- **The D0/D1/D2/D3 split** is a keyword heuristic, not a manual audit. Directionally reliable,
  ±10% per bucket.

---

## 13. Open questions

1. **Who is the demo for?** A PM harvesting inspiration needs 30 seconds and a mechanism. A PM
   evaluating for adoption needs depth and honest limits. These are different products; the
   current site reads like the former.
2. **Is Tier 2 acceptable to you?** See §8. Publishing illustrative reconstructions on a site
   whose voice is strictly evidence-cited is a genuine editorial decision, and dropping Tier 2
   costs 35% coverage but zero credibility.
3. **Monthly ceiling for live API spend?** Determines whether Tier 1 is cached-only or genuinely
   live.
4. **Do you want the vendor-outreach motion (§9a)?** It is the highest-leverage item here, but it
   changes WeeklyAI from a pure observer into something with relationships — and eventually a
   bias question when a vendor supplying your API key is also being scored 4 or 5.
5. **Is 5/day a fixed cadence or a quality-gated one?** If fixed, Tier 3/4 must auto-publish
   unreviewed. If gated, expect 2–3/day for the first month.
6. **Both locales from day one?** Doubles generation cost per demo and the review burden. The
   `DemoSpec` above assumes yes, matching the existing `_en` field convention.
