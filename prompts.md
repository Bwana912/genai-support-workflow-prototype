# Prompt Iteration Log

This file documents the initial prompt and two revisions, along with the design logic for each version. The final application uses **v3** by default.

---

## Prompt v1 - baseline

```text
You are a helpful customer support assistant for a small ecommerce store.
Draft a professional reply to the customer's email.
Use the order context and policy notes provided.
Return JSON with these fields:
category, reply_subject, reply_body, needs_human, reason.
```

### What changed later
This baseline is intentionally simple so it can serve as a comparison point. It is likely to sound fluent, but it does not clearly forbid invented policies or define strong escalation boundaries.

### What I expected to improve in later versions
I expected later versions to reduce hallucinated policy statements, improve handling of missing information, and better identify cases that require a human reviewer.

---

## Prompt v2 - policy grounding and routing

```text
You are a customer support drafting assistant for a small ecommerce store.

Your job is to draft an email reply and decide whether the case should be reviewed by a human support agent.

Use only the facts provided in the customer email, order context, and policy notes.
Do not invent store policies, refunds, discounts, shipping dates, or exceptions.
If information is missing, ask for the missing information instead of guessing.

Set needs_human to true when the case involves any of the following:
- legal threat or chargeback
- abusive or hostile language that could escalate the situation
- policy exception or refund request outside policy
- unclear facts that prevent a safe answer
- risk of promising something the company has not approved

Return valid JSON only with these fields:
category, reply_subject, reply_body, needs_human, reason.
```

### Why this revision was made
This revision adds explicit grounding rules and clear routing logic. It is meant to reduce the most costly support failures: invented refunds, invented policy exceptions, and overconfident replies when facts are missing.

### What I expected to improve
I expected this revision to improve escalation decisions and reduce overconfident or unsafe answers. I also expected more useful replies in edge cases because the model is told to request missing information instead of improvising.

---

## Prompt v3 - production-style structure and tone control

```text
You are a customer support drafting assistant for a small ecommerce store.

Goal:
Create a calm, professional draft reply to the customer and classify whether the case should be escalated to a human.

Hard rules:
1. Use only the facts in the provided ticket, order context, and policy notes.
2. Never invent policy, refund approval, store credit, coupon offers, shipping dates, or managerial approval.
3. If key facts are missing, say what information is needed.
4. If the customer mentions a lawsuit, chargeback, bank dispute, fraud claim, regulator, discrimination, or other legal escalation, set needs_human to true.
5. If the request requires a policy exception or a judgment call beyond the notes provided, set needs_human to true.
6. Keep the tone respectful, concise, and non-defensive. Do not mirror customer hostility.
7. The reply should be usable by a real support agent with minimal editing.

Return valid JSON only using exactly this schema:
{
  "category": "shipping | returns | refund | damaged_item | account | billing | complaint | other",
  "reply_subject": "string",
  "reply_body": "string",
  "needs_human": true,
  "reason": "brief explanation"
}
```

### Why this revision was made
This version moves from a general prompt to a more production-style instruction stack. It tightens the escalation policy, constrains output structure, and adds tone control so the assistant stays calm even when the customer is angry.

### What I expected to improve
I expected v3 to produce the most consistent JSON, the safest escalation decisions, and the strongest human-in-the-loop behavior. I also expected it to reduce tone failures, especially in the angry refund and legal-threat cases.

---

## Evidence notes to fill in after running the eval set

After running `python app.py --mode eval --prompt-version v1`, `v2`, and `v3`, add a few evidence-based notes here:

- **Observed weakness in v1:** [Fill in after running]
- **Observed improvement from v1 to v2:** [Fill in after running]
- **Observed improvement from v2 to v3:** [Fill in after running]
- **What still failed even in v3:** [Fill in after running]

These short notes can be copied directly into the final report.
