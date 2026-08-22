import pytest
import yaml
import asyncio
import re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from app.infra.llm import GroqProvider
from app.domain.classification import ClassificationResult
from app.api.agent.prompts import get_system_prompt  
CASES_FILE = Path(__file__).parent / "cases.yaml"


def load_cases():
    with open(CASES_FILE) as f:
        return yaml.safe_load(f)


def check_case(result: ClassificationResult, expect: dict) -> tuple[bool, list[str]]:
    failures = []
    items = result.items

    expected_nag = expect.get("nag_policy")
    if expected_nag is False:
        expected_nag = "off"

    # ── COUNT CHECK ──
    if "count" in expect:
        if len(items) != expect["count"]:
            failures.append(f"count: expected {expect['count']}, got {len(items)}")

    if expect.get("count", 1) == 0:
        return len(failures) == 0, failures

    if not items:
        return False, ["no items returned but expected some"]

    # ── TYPE CHECK ──
    if "type" in expect:
        for i, item in enumerate(items):
            if item.type != expect["type"]:
                failures.append(f"item[{i}].type: expected {expect['type']}, got {item.type}")

    # ── NAG POLICY CHECK ──
    if expected_nag is not None:
        for i, item in enumerate(items):
            if item.nag_policy != expected_nag:
                failures.append(f"item[{i}].nag_policy: expected {expected_nag}, got {item.nag_policy}")

    # ── DUE_AT CHECK ──
    if "due_at" in expect:
        item = items[0]
        if expect["due_at"] == "set" and item.due_at is None:
            failures.append("due_at: expected set, got null")
        elif expect["due_at"] == "null" and item.due_at is not None:
            failures.append(f"due_at: expected null, got {item.due_at}")

    return len(failures) == 0, failures


async def run_single_case_with_backoff(provider, case, now):
    """Runs a single case sequentially and handles 429 rate limits gracefully."""
    name = case["name"]
    input_text = case["input"]
    expect = case["expect"]
    
    system_prompt = get_system_prompt(now)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = await provider.complete(
                prompt=input_text,
                schema=ClassificationResult,
                system_prompt=system_prompt,
            )
            ok, reasons = check_case(result, expect)
            return name, input_text, expect, ok, reasons
        except Exception as e:
            err_str = str(e)
            # Check if it is a rate limit error (429)
            if "429" in err_str or "rate_limit" in err_str:
                # Try to parse sleep time, e.g., "try again in 19.4s"
                wait_time = 10.0  # default backup sleep
                match = re.search(r"try again in (\d+\.?\d*)s", err_str)
                if match:
                    wait_time = float(match.group(1)) + 1.5  # add 1.5s safety margin
                
                print(f"\n[Rate Limit] Sleeping for {wait_time:.1f}s on case: {name}...")
                await asyncio.sleep(wait_time)
                continue
            else:
                return name, input_text, expect, False, [f"EXCEPTION: {e}"]

    return name, input_text, expect, False, ["Rate limit exceeded after multiple retries"]


@pytest.mark.eval
@pytest.mark.asyncio
async def test_classification_eval():
    cases = load_cases()
    provider = GroqProvider(temperature=0)  # Deterministic!
    now = datetime.now(ZoneInfo("Pacific/Auckland"))

    passed = 0
    total = len(cases)
    results = []

    print("\nStarting evaluation sequentially to respect Rate Limits...")
    for i, case in enumerate(cases):
        print(f"Running case {i+1}/{total}: {case['name']}...", end="", flush=True)
        res = await run_single_case_with_backoff(provider, case, now)
        results.append(res)
        print(" Done!" if res[3] else " Failed!")
        # 1.5 seconds gap to stay under 8000 TPM limit
        await asyncio.sleep(1.5)

    failure_details = []
    for name, input_text, expect, ok, reasons in results:
        if ok:
            passed += 1
        else:
            failure_details.append((name, input_text, expect, reasons))

    print("\n" + "=" * 60)
    print("  EVAL RESULTS")
    print("=" * 60)

    for name, input_text, expect, reasons in failure_details:
        print(f"\n  FAIL  {name}")
        print(f"    input:    \"{input_text}\"")
        print(f"    expected: {expect}")
        print(f"    got:      {reasons}")

    print("\n" + "-" * 60)
    print(f"  SCORE: {passed}/{total} ({passed * 100 // total}%)")
    print("=" * 60 + "\n")

    assert passed > 0, "All cases failed"