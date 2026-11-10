# Clutch content review — 2026-11-09

## Task contract

- **Task:** understand how an agent can finish a specific job while keeping its access within that job's scope.
- **Input:** a test-database debugging task or one customer's billing question, plus the requested resource/action.
- **First result:** a concrete request, its required access and an allowed, authorization-needed or out-of-scope example decision.
- **Evidence:** independently authored sample policies and responses, not an executed Clutch session or verified integration. Official pages support the product's general role; they do not verify this example's exact credential mechanism.
- **Next action:** compare another request or task, then verify the necessary integrations and controls with the vendor.

## Findings and correction

The supplied screenshot is the Clutch Security cache `a4c21dccf77c1b8009a70798-ecbdc5d85e669caaec13eaaa`, product `p_16ab841852cd830c`. Its code-agent branch said all keys, environment variables and deployment configuration should be blocked. This conflated secret values with configuration and authenticated operations. Its support branch blocked all payment information even though a billing task may need payment status. A later monitoring section always showed support-ticket activity, including after selecting the code agent.

Both shipped cache copies now open with a concrete test-debugging or billing task. They distinguish readable configuration/data, actions requiring a scoped authorization, and resources outside that task. The example tool may use authorized credentials without returning raw passwords to the conversation; that is an authored example policy, not a verified claim about Clutch's implementation. The request examples follow the selected task. The previous generic boundary section and unsupported “low risk” conclusion were removed.

The generation prompt now requests task-specific necessary access, separates configuration, credentials and authenticated actions, and requires later requests/logs to remain consistent with earlier choices. This improves generation guidance; it is not a semantic validator or a factual guarantee for future outputs.

## Official evidence checked in this run

- [Agent Guardrails](https://www.clutch.security/agentic-ai/agent-guardrails) describes policies for people, tools, identities and resources, including different treatment of development and production contexts.
- [Least Privilege Enforcement](https://www.clutch.security/use-cases/least-privilege-enforcement) describes identifying unnecessary permissions and reducing them while preserving operational needs.
- [Clutch website](https://www.clutch.security/) supplies the official route to request a product demonstration.

## Delivery and verification

`ready_experience` prefers a compatible shipped cache before querying MongoDB. The corrected record preserves its product identity and fingerprint, and a regression check resolves the current bundled catalog product to that record while making any database access or model generation fail the test. The backend and crawler JSON copies are byte-identical. Publishing the backend bundle delivers this correction without a database write; existing response caches may need their normal refresh window.

`tests/test_clutch_demo.py` plus `tests/test_product_demos.py`: **67 passed**. The checks cover schema validation, cache precedence, mirrored data, and distinct dependent request examples for both tasks. They do not establish vendor execution, a security audit, or comprehension by first-time human users. The supplied screenshot and current source were reviewed; this document's content review is separate from the browser interaction checks recorded by the main task.

## Independent simulator review

Read-only review of `frontend-next/src/lib/clutch-access.ts` and `frontend-next/src/components/demo/clutch-access-demo.tsx` found that the sample grant only changes the current task's authorization-required request. Secret disclosure, production access, full card numbers and other-customer records remain denied even with the grant. Changing tasks clears it. Credential use is described separately from credential disclosure, with an explicit note that the connection-layer mechanism is authored for this example. No blocking semantic issue was found. The implementation agent was asked to name the exact database and invoice in the grant labels to match the already-specific result explanations.
