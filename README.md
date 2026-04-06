# Homework 2: Build and Evaluate a Simple GenAI Workflow

## Project title
Customer Support Reply Drafting Assistant for a Small Ecommerce Store

## Project overview
This project prototypes a narrow, business-relevant GenAI workflow: drafting customer support email replies for a small ecommerce store while flagging risky cases for human review. The system is intentionally small, reproducible, and evaluation-driven.

The prototype takes three inputs:
1. a customer email
2. order context
3. store policy notes

It returns structured JSON with:
- `category`
- `reply_subject`
- `reply_body`
- `needs_human`
- `reason`

## Why this workflow
Customer support is a strong GenAI workflow because it is writing-heavy, repetitive at the low-risk end, and high-impact at the exception-heavy end. A good assistant can accelerate routine replies, but poor handling of refunds, chargebacks, legal threats, or unclear facts can create real business risk. That makes it a strong fit for a human-in-the-loop workflow rather than blind automation.

## User
The primary user is a customer support agent at a small ecommerce company.

## Input
- customer email text
- order metadata such as item, status, delivery date, and return window
- short policy notes

## Output
Structured JSON containing:
- a category for routing
- a polished draft subject line
- a polished draft email body
- a `needs_human` decision
- a brief explanation of why the case should or should not be escalated

## Repository contents
- `README.md` - project summary and run instructions
- `app.py` - command-line prototype and evaluation runner
- `prompts.md` - initial prompt plus two revisions
- `eval_set.json` - canonical evaluation set used by the script
- `eval_set.md` - human-readable version of the evaluation set
- `report.md` - polished report draft with honest placeholders for measured results
- `report.pdf` - PDF version of the report draft
- `requirements.txt` - Python dependencies
- `.env.example` - environment variable template
- `.gitignore` - ignores secrets and generated outputs

## Quick start
### 1) Create and activate a virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Create your environment file
Copy `.env.example` to `.env` and add your Gemini API key.

```env
GEMINI_API_KEY=your_key_here
# optional override
GEMINI_MODEL=gemini-2.5-flash
```

### 4) Run a minimal single-case test
```bash
python app.py --mode single --case-id case_01 --prompt-version v3
```

### 5) Run the full evaluation set
```bash
python app.py --mode eval --prompt-version v3
```

Outputs will be saved to `outputs/`.

## Model note
The updated script now defaults to `gemini-2.5-flash`, which is the current stable Gemini Flash model. If you need a lighter fallback, you can run:

```bash
python app.py --model gemini-2.5-flash-lite
```

If you see a quota error, the script is reaching the API successfully, but your Gemini project needs available quota or billing.

## Suggested grading/demo workflow
1. Run one minimal case to prove the API call works.
2. Run the full evaluation set with `v1`.
3. Run the full evaluation set with `v2`.
4. Run the full evaluation set with `v3`.
5. Compare the saved output files and update the bracketed placeholders in `report.md`.
6. Export or keep `report.pdf` after final edits.
7. Record the short walkthrough video.

## Reproducibility notes
- The script runs from the command line.
- At least one system prompt is configurable using `--prompt-version`.
- Outputs are saved to timestamped files in `outputs/`.
- The canonical evaluation set is fixed in `eval_set.json`.

## Submission placeholders

- GitHub repo link: [genai-support-workflow-prototype](https://github.com/Bwana912/genai-support-workflow-prototype)
- Video link: [Walkthrough video](https://www.youtube.com/watch?v=i_7nt57O7lA)

## Final note
This repository is designed to show judgment, not just generation quality. The intended deployment recommendation is a human-reviewed drafting assistant for routine tickets, with automatic escalation for policy exceptions, missing facts, legal threats, chargebacks, abusive messages, and other higher-risk cases.
