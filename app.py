import argparse
import json
import os
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except ImportError as exc:
    raise SystemExit(
        "Missing dependencies. Run: pip install -r requirements.txt"
    ) from exc

BASE_DIR = Path(__file__).resolve().parent
EVAL_SET_PATH = BASE_DIR / "eval_set.json"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)
DEFAULT_MODEL = "gemini-2.5-flash"

PROMPTS = {
    "v1": """You are a helpful customer support assistant for a small ecommerce store.
Draft a professional reply to the customer's email.
Use the order context and policy notes provided.
Return JSON with these fields:
category, reply_subject, reply_body, needs_human, reason.""",
    "v2": """You are a customer support drafting assistant for a small ecommerce store.

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
category, reply_subject, reply_body, needs_human, reason.""",
    "v3": """You are a customer support drafting assistant for a small ecommerce store.

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
}""",
}

REQUIRED_FIELDS = ["category", "reply_subject", "reply_body", "needs_human", "reason"]


def load_eval_set(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_case(cases, case_id: str):
    for case in cases:
        if case["id"] == case_id:
            return case
    raise ValueError(f"Case ID not found: {case_id}")


def build_contents(case: dict) -> str:
    return f"""TICKET INPUT:
Customer email:
{case['customer_email']}

Order context:
{json.dumps(case['order_context'], indent=2)}

Policy notes:
{case['policy_notes']}

Return valid JSON only.
"""


def clean_json_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def explain_api_error(exc: Exception, model: str) -> str:
    message = str(exc)

    if "404" in message and "NOT_FOUND" in message:
        return (
            f"Model '{model}' is not available for this Gemini API project. "
            f"Use --model {DEFAULT_MODEL} or update the default in app.py.\n\n"
            f"Original error:\n{message}"
        )

    if "429" in message or "RESOURCE_EXHAUSTED" in message or "quota" in message.lower():
        return (
            "Your Gemini API key is working, but the project has no available quota for this request right now. "
            "Check your Gemini API plan/billing/quota in Google AI Studio or try again later.\n\n"
            f"Original error:\n{message}"
        )

    if "API key" in message or "permission" in message.lower() or "auth" in message.lower():
        return (
            "Authentication failed. Confirm that GEMINI_API_KEY is set in .env and that the key was created "
            "for the Gemini API / Google AI Studio project you intend to use.\n\n"
            f"Original error:\n{message}"
        )

    return message


def call_model(model: str, temperature: float, system_prompt: str, contents: str) -> tuple[dict, str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not found. Create a .env file in the project folder and add your key."
        )

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                response_mime_type="application/json",
            ),
        )
    except Exception as exc:
        raise RuntimeError(explain_api_error(exc, model)) from exc

    raw_text = (response.text or "").strip()
    if not raw_text:
        raise RuntimeError("Model returned an empty response. Try rerunning the case.")

    cleaned = clean_json_text(raw_text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON. Raw output:\n{raw_text}") from exc

    return parsed, raw_text


def auto_check(result: dict, case: dict) -> dict:
    checks = {
        "valid_required_fields": all(field in result for field in REQUIRED_FIELDS),
        "category_match": result.get("category") == case.get("expected_category"),
        "needs_human_match": result.get("needs_human") == case.get("expected_needs_human"),
        "reply_body_present": bool(result.get("reply_body", "").strip()),
    }

    score = sum(1 for passed in checks.values() if passed)
    checks["score_out_of_4"] = score
    checks["manual_review_prompt"] = [
        "Did the reply follow the provided policy notes?",
        "Did the reply avoid inventing facts, refunds, or exceptions?",
        "Would a real support agent send this with minimal editing?",
        "Was the escalation decision appropriate for the business risk?",
    ]
    return checks


def save_json(filename: Path, payload: dict):
    with filename.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def print_header(title: str):
    border = "=" * len(title)
    print(f"\n{border}\n{title}\n{border}")


def print_single_case_summary(output: dict, show_raw: bool = False):
    case = output["case"]
    result = output["model_output"]
    checks = output["auto_checks"]

    print_header("SINGLE CASE RESULT")
    print(f"Saved to: {output['output_file']}")
    print(f"Case ID: {case['id']}")
    print(f"Title: {case.get('title', 'N/A')}")
    print(f"Model: {output['model']} | Prompt: {output['prompt_version']} | Temperature: {output['temperature']}")
    print(f"Score: {checks['score_out_of_4']}/4 | Category match: {checks['category_match']} | Needs human match: {checks['needs_human_match']}")
    print(f"Category: {result.get('category', 'N/A')} | Needs human: {result.get('needs_human', 'N/A')}")
    print(f"Reason: {result.get('reason', '').strip()}")
    print(f"Reply subject: {result.get('reply_subject', '').strip()}")
    print("Reply body:")
    print(result.get('reply_body', '').strip())

    if show_raw:
        print_header("RAW MODEL RESPONSE")
        print(output['raw_response_text'])
        print_header("FULL OUTPUT JSON")
        print(json.dumps(output, indent=2, ensure_ascii=False))


def print_eval_summary(summary: dict, show_raw: bool = False):
    print_header("EVAL SUMMARY")
    print(f"Saved to: {summary['output_file']}")
    print(f"Model: {summary['model']} | Prompt: {summary['prompt_version']} | Temperature: {summary['temperature']}")
    print(f"Cases processed: {summary['num_cases']}")

    correct_category = sum(r["auto_checks"]["category_match"] for r in summary["results"])
    correct_routing = sum(r["auto_checks"]["needs_human_match"] for r in summary["results"])
    valid_json_like = sum(r["auto_checks"]["valid_required_fields"] for r in summary["results"])
    print(f"Required fields present: {valid_json_like}/{summary['num_cases']}")
    print(f"Category match: {correct_category}/{summary['num_cases']}")
    print(f"Needs human match: {correct_routing}/{summary['num_cases']}")

    print_header("CASE RESULTS")
    for result in summary["results"]:
        status = result["status"]
        score = result["auto_checks"]["score_out_of_4"]
        category_flag = "✓" if result["auto_checks"]["category_match"] else "✗"
        human_flag = "✓" if result["auto_checks"]["needs_human_match"] else "✗"
        print(f"{result['case_id']}: {status.upper():5} | Score: {score}/4 | Category: {category_flag} | Needs human: {human_flag} | Title: {result['title']}")
        if status == "error":
            print(f"  ERROR: {result['raw_response_text']}")
        elif show_raw:
            if not result["auto_checks"]["valid_required_fields"]:
                print(f"  RAW RESPONSE: {result['raw_response_text']}")


def run_single_case(cases, case_id: str, prompt_version: str, model: str, temperature: float, show_raw: bool):
    case = deepcopy(find_case(cases, case_id))
    system_prompt = PROMPTS[prompt_version]
    contents = build_contents(case)
    result, raw_text = call_model(
        model=model,
        temperature=temperature,
        system_prompt=system_prompt,
        contents=contents,
    )
    checks = auto_check(result, case)

    output = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mode": "single",
        "model": model,
        "prompt_version": prompt_version,
        "temperature": temperature,
        "case": case,
        "model_output": result,
        "raw_response_text": raw_text,
        "auto_checks": checks,
    }

    out_file = OUTPUT_DIR / f"single_{case_id}_{prompt_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output["output_file"] = str(out_file)
    save_json(out_file, output)

    print_single_case_summary(output, show_raw=show_raw)


def run_eval(cases, prompt_version: str, model: str, temperature: float, show_raw: bool):
    results = []
    system_prompt = PROMPTS[prompt_version]

    for case in cases:
        contents = build_contents(case)
        try:
            result, raw_text = call_model(
                model=model,
                temperature=temperature,
                system_prompt=system_prompt,
                contents=contents,
            )
            checks = auto_check(result, case)
            status = "ok"
        except Exception as exc:
            result = {}
            raw_text = str(exc)
            checks = {
                "valid_required_fields": False,
                "category_match": False,
                "needs_human_match": False,
                "reply_body_present": False,
                "score_out_of_4": 0,
                "manual_review_prompt": ["Inspect error output and rerun the case."],
            }
            status = "error"

        results.append(
            {
                "case_id": case["id"],
                "title": case["title"],
                "status": status,
                "expected_category": case["expected_category"],
                "expected_needs_human": case["expected_needs_human"],
                "model_output": result,
                "raw_response_text": raw_text,
                "auto_checks": checks,
            }
        )

    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mode": "eval",
        "model": model,
        "prompt_version": prompt_version,
        "temperature": temperature,
        "num_cases": len(cases),
        "results": results,
    }

    out_file = OUTPUT_DIR / f"eval_{prompt_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    summary["output_file"] = str(out_file)
    save_json(out_file, summary)
    print_eval_summary(summary, show_raw=show_raw)


def parse_args():
    parser = argparse.ArgumentParser(description="Customer support workflow prototype")
    parser.add_argument("--mode", choices=["single", "eval"], default="single")
    parser.add_argument("--case-id", default="case_01", help="Used only in single mode")
    parser.add_argument("--prompt-version", choices=["v1", "v2", "v3"], default="v3")
    parser.add_argument("--model", default=os.getenv("GEMINI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--show-raw", action="store_true", help="Print raw model response and full output JSON in the console")
    return parser.parse_args()


def main():
    load_dotenv()
    args = parse_args()
    cases = load_eval_set(EVAL_SET_PATH)

    if args.mode == "single":
        run_single_case(
            cases=cases,
            case_id=args.case_id,
            prompt_version=args.prompt_version,
            model=args.model,
            temperature=args.temperature,
            show_raw=args.show_raw,
        )
    else:
        run_eval(
            cases=cases,
            prompt_version=args.prompt_version,
            model=args.model,
            temperature=args.temperature,
            show_raw=args.show_raw,
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit("\nRun cancelled by user.")
    except Exception as exc:
        raise SystemExit(str(exc))
