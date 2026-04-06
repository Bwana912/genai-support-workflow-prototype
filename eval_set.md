# Evaluation Set (Human-Readable Copy)

This file mirrors the canonical `eval_set.json` in a more readable format. The JSON file is the version used by `app.py`.

## Coverage summary
The evaluation set intentionally includes:
- normal cases
- edge cases
- failure-triggering or human-review cases

That design makes it possible to judge not just fluency, but also routing quality and policy discipline.

| ID | Case | Type | Expected Category | Expected `needs_human` |
|---|---|---|---|---|
| case_01 | Shipping delay with tracking available | Normal | shipping | false |
| case_02 | Return request inside policy window | Normal | returns | false |
| case_03 | Missing order number and incomplete account information | Edge | shipping | false |
| case_04 | Damaged item report with missing evidence | Edge | damaged_item | false |
| case_05 | Refund demand outside policy window | Failure-risk / escalation | refund | true |
| case_06 | Legal threat and chargeback risk | Failure-risk / escalation | billing | true |

---

## case_01 - Shipping delay with tracking available
**Good output should:** acknowledge the delay, reference the current tracking status, avoid inventing a new delivery date, and politely explain that the order is still in transit.

## case_02 - Return request inside policy window
**Good output should:** explain the return process, confirm that the request appears eligible based on the notes provided, and avoid adding unsupported fees or extra conditions.

## case_03 - Missing order number and incomplete account information
**Good output should:** acknowledge the frustration and request the missing details needed for an order lookup rather than pretending to know the order status.

## case_04 - Damaged item report with missing evidence
**Good output should:** apologize, request a damage photo, and avoid promising an immediate replacement before documentation is received.

## case_05 - Refund demand outside policy window
**Good output should:** stay professional, avoid promising a refund, and clearly flag the case for human review because the request is outside policy.

## case_06 - Legal threat and chargeback risk
**Good output should:** remain calm, avoid arguing, and escalate immediately without making unsupported promises.
