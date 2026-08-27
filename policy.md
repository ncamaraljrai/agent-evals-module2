# Northwind Returns Policy — Module 2 compatible reconstructed fixture

> The lab references official course fixture files that were not supplied.
> This policy is reconstructed from behavior explicitly stated in Modules 1–2.

Rules use precedence: lower-numbered controlling exceptions win.

**R1 — Safety.** Injury, burn, fire, or other product-safety reports must be escalated; do not auto-refund.
**R2 — Lookup.** Look up the order before deciding. Unknown order => `not_found`.
**R3 — High value.** Orders over $500.00 must `escalate`; no refund side effect.
**R5 — Clearance.** Clearance/final-sale items are denied unless a higher-priority rule applies.
**R6 — Outside return window.** Orders delivered more than 60 days ago are denied.
**R9 — Full refund window.** Eligible non-clearance items delivered within 30 days, unused/unopened, receive a full refund.
**R10 — Partial refund window.** Eligible non-clearance items delivered 31–60 days ago, unused/unopened, receive 50% of the order total using integer floor division.
**R11 — Unclear condition.** If condition is required but not stated, ask for clarification.
**R12 — Reply discipline.** State the decision and reason in plain language; do not expose internal rule IDs or invent compensation.
