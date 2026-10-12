# Product experience gates

Updated 2026-10-12 after the Autentic Reddit trial. This supplements structural tests with human review; passing JSON validation does not establish that a visitor understands a product.

## Start from the task

Before changing a product flow, write five concrete sentences:

1. The visitor arrives because they want to ___.
2. They provide ___; the product returns ___.
3. The first useful result they can inspect is ___.
4. The result is live / cached / illustrative, supported by ___.
5. The next useful action is ___, with ___ still needing verification.

Use the existing product components and visual language. Choose the shortest necessary path; never copy a four-step wizard just because another product has one. Share quality standards, not an identical journey.

## Review gates before promotion

- Entry: a new visitor can point to the job, required input, and one primary next action without reading a manual.
- First value: the first meaningful choice reveals a tangible example or result. Do not delay all value behind setup.
- Choice: changing an input changes a relevant visible result. Dependent choices reset when context changes; every branch remains reachable.
- Reading load: ask one question at a time, explain domain terms beside the decision, hide unneeded future-step content, and name buttons for their result where useful.
- Evidence: mark illustrative output where it appears. A simulated quote is not an interview; a vendor claim is not an independently verified result. Do not imply live execution through completion labels.
- Product fit: use the artifact natural to the task: card listing comparison, research synthesis, search result with sources, or storyboard. If real value requires the vendor's service, expose that handoff and its signup friction.
- Recovery: keyboard access, narrow viewport reflow, back/edit behavior, empty states, external links, and downloaded summaries remain usable and honest.
- Human check: ask a first-time tester what the product does, what just happened, and what they would do next. Record their actual answer and hesitation; do not mark this gate passed based only on an agent's opinion.

## Distinct product contracts

| Product | Visitor's task | First useful result | Necessary distinction |
| --- | --- | --- | --- |
| DarkHorseRadar / Autentic example | Understand whether this research tool is worth trying | A clear research input → vendor-described transcript/synthesis output, then a labeled fictional insight card | This is an explanation, not the vendor's actual AI interviewer. Link to the official trial. |
| TCGlens | Compare offers for the exact card version | Two original listings with visible set, number, language, rarity and separately stated item/shipping/tax information | A asking-price comparison does not establish identity, condition, authenticity, final checkout cost or lowest price. |

## What is enforced today

The schema validates sizes, widget types, safe cited URLs, earlier-choice references, and branch coverage. The renderer clears downstream selections. Tests cover those rules and curated profile precedence. Generation now requests 3–6 useful steps and explicit product input/output rather than exactly four steps.

Semantic fit and comprehension still require the review above. Old cached examples are not regenerated automatically and have not all been reviewed. Do not infer that a prompt update repaired existing examples or every product.
