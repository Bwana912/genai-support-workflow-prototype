# Homework 2 Report: Build and Evaluate a Simple GenAI Workflow

## Business use case

This project prototypes a customer-support drafting assistant for a small ecommerce business. The target user is a support agent who handles repetitive written customer inquiries. The system takes three inputs: a customer email, structured order context, and short policy notes. It returns a structured JSON output containing a category label, a reply subject, a reply body, a `needs_human` flag, and a short reason for the decision.

This workflow is a strong fit for partial automation because many support emails are repetitive and policy-driven, but some cases still require judgment or exception handling. The goal of the prototype is not to automate support end-to-end. Instead, the goal is to test whether an LLM can reliably draft useful first-pass responses while correctly identifying cases that should be escalated to a human reviewer.

## Model choice and prototype design

I used `gemini-2.5-flash` as the final model for the prototype. I chose it because it was easy to access through Google AI Studio, fast enough for repeated testing, and strong enough to produce structured outputs consistently for a narrow business-writing task.

The prototype is implemented as a simple Python command-line app. It reads a small evaluation set from `eval_set.json`, loads one of three prompt versions from `prompts.md`, sends the case information to the model, parses the JSON response, and then scores the output with simple automatic checks. This design keeps the project reproducible and narrow, which is appropriate for the assignment.

## Evaluation setup

I created a stable evaluation set with 6 representative support cases:
- a normal shipping-delay inquiry
- a normal return request inside policy
- a case with missing order information
- a damaged-item report missing photo evidence
- a refund demand outside the return window
- a legal-threat / chargeback-risk billing case

This evaluation set intentionally includes both routine cases and riskier cases. That matters because a useful support-writing system should not only sound fluent; it should also avoid inventing policy exceptions and should correctly identify when human review is required.

## Prompt iteration

### Baseline prompt (v1)
The first prompt asked the model to draft a professional support response and return structured JSON. This version produced complete outputs, but it left category naming too open-ended. As a result, the model often produced semantically reasonable labels such as "Shipping Delay" or "Return Request" instead of the exact category labels used by the evaluation set. It also made one escalation mistake on the case with missing order information by marking it for human review when the better action was simply to ask the customer for more information.

### Revision 1 (v2)
In the second prompt, I tightened the instructions. I added stronger wording to use only the provided facts, avoid inventing refunds, avoid unsupported promises, and ask for missing information before escalating. This improved the escalation behavior: the `needs_human` decision matched the expected result in all 6 cases. However, category matching was still poor because the model continued using natural-language labels instead of the exact controlled category vocabulary.

### Revision 2 / final prompt (v3)
In the final prompt, I made the output schema more explicit and constrained the category values to the evaluation set vocabulary. I also added clearer escalation triggers for legal threats, chargebacks, fraud complaints, and policy-exception requests. This produced the strongest results overall and made the system more consistent and easier to evaluate.

## Results

The strongest performance came from the final prompt (`v3`) with `gemini-2.5-flash`.

| Prompt version | Required fields present | Category match | `needs_human` match |
|---|---:|---:|---:|
| v1 | 6/6 | 0/6 | 5/6 |
| v2 | 6/6 | 0/6 | 6/6 |
| v3 | 6/6 | 5/6 | 6/6 |

These results show two important patterns.

First, the system was reliable about returning complete structured output across all three versions. That means the prototype itself was stable and reproducible.

Second, prompt design had a meaningful effect on task quality. The biggest improvement from v1 to v2 was in escalation behavior: after I added clearer guidance about when to ask for more information versus when to escalate, the system correctly matched the expected `needs_human` decision in all 6 cases. The biggest improvement from v2 to v3 was category consistency: once I constrained the category vocabulary more explicitly, category matching improved from 0/6 to 5/6.

The one remaining category error in v3 occurred on the refund-demand case outside the policy window. The model labeled it as `returns` instead of `refund`, even though the reply itself was still appropriate and the escalation decision was correct. In other words, the remaining weakness was mostly a classification-label precision issue rather than a dangerous policy failure.

## Example output quality

A representative strong example was the shipping-delay case. The final system acknowledged the delay, cited the current tracking status, avoided inventing a new delivery promise, and correctly kept the case out of human review. This is the type of repetitive, policy-bounded case where the workflow appears most useful.

## Limitations and human review boundary

This prototype still has clear limits. It performs best when the policy is straightforward and the next step is well defined. It is weaker in situations where categories overlap semantically, where the order facts are incomplete or contradictory, or where the customer is asking for an exception outside policy.

For that reason, I would not recommend deploying this system as a fully autonomous email sender. I would recommend it only as a human-in-the-loop drafting assistant. In that setup, the model can save time on repetitive cases by generating a first-pass draft, while a support agent still reviews the output before sending it. High-risk cases involving legal threats, fraud, chargebacks, or requests for policy exceptions should continue to be routed to a human specialist.

## Recommendation

Overall, I would recommend this workflow for limited deployment as an internal support-drafting assistant. The final system showed strong consistency on structured output and escalation decisions, and it improved substantially through prompt iteration. However, because one category-label error remained and because policy-sensitive cases still require judgment, the best deployment model is assisted drafting with human review rather than full automation.
