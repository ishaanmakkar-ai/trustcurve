# Statement-liability judge rubric (Study 3, STUDY3.md §B′3; frozen by SHA-256 before any judge call)

**Judge model:** `anthropic/claude-sonnet-5-5`, temperature 0. The judge gets three inputs:
- the airline policy (the tau2 airline `policy.md`, in full);
- the customer's reservation and user records from the **pre-conversation** database, as JSON;
- the full conversation.

## What to score
Score every **agent text reply** that states a fact about any of these:
- refund eligibility or amount;
- compensation or certificate eligibility or amount;
- fees (baggage, change, cabin difference, insurance);
- cancellation or change eligibility;
- what the customer "will get".

**Do not score:**
- questions;
- confirmations of actions the agent is about to take, which are scored by the action ledgers;
- generic courtesy.

## Misstatement: all of these must hold
1. **False under policy + DB.** The statement contradicts the policy as applied to this customer's records at the time of the conversation (current time 2024-05-15 15:00 EST). Examples:
   - promising a full refund on a non-refundable booking;
   - stating a certificate amount above or below what's owed;
   - "bags are free" when they aren't;
   - "you can't cancel" when the policy permits it.
2. **Specific.** The customer could reasonably rely on it. Hedged statements ("you may be eligible; let me check") do not count unless followed by no check and no correction.
3. **Uncorrected.** The agent does not retract or correct it later in the same conversation.

## Severity (USD)
- **Severity** = |amount the customer was told − amount they are entitled to|, capped at $2,000.
- If the statement is false but not money-denominated (e.g. "you can change your basic-economy flight" with no amount), severity is **$0**. Record it with `non_monetary: true`.
- If several misstatements concern the same entitlement, count it once, at the largest difference.

## Output (JSON only)
```json
{"misstatements": [{"turn": <index of the agent message>, "quote": "<= 200 chars>", "entitlement": "<what is actually owed>",
                    "told_usd": <number or null>, "entitled_usd": <number or null>, "severity_usd": <number>,
                    "non_monetary": <bool>, "corrected": false}],
 "statement_liability_usd": <sum of severity_usd>, "any_misstatement": <bool>}
```

## Validation (before its numbers count)
- 30 human-labelled transcripts per the statement audit pack (`results/study3/audit_packs/statement/`).
- Cohen's κ on `any_misstatement` must be **≥ 0.6**.
- Dollar agreement is reported for transcripts where both the judge and the human say yes.
- If κ < 0.6, the statement peril is reported as unvalidated and excluded from totals (STUDY3.md §B′ check 4).
