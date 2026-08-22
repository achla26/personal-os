import pytest
import yaml
import asyncio
import re
from pathlib import Path

from httpx import AsyncClient
from app.api.deps import get_llm_provider
from app.infra.llm import GroqProvider

CASES_FILE = Path(__file__).parent / "cases.yaml"


def load_cases():
    with open(CASES_FILE) as f:
        return yaml.safe_load(f)


def check_chat_case(response_data: dict, expect: dict) -> tuple[bool, list[str]]:
    failures = []
    items = response_data.get("items", [])

    expected_nag = expect.get("nag_policy")
    if expected_nag is False:
        expected_nag = "off"

    # 1. COUNT CHECK
    if "count" in expect:
        if len(items) != expect["count"]:
            failures.append(f"count: expected {expect['count']}, got {len(items)}")

    if expect.get("count", 1) == 0:
        return len(failures) == 0, failures

    if not items:
        return False, ["no items returned but expected some"]

    # 2. TYPE CHECK
    if "type" in expect:
        for i, item in enumerate(items):
            if item.get("item_type") != expect["type"]:
                failures.append(f"item[{i}].item_type: expected {expect['type']}, got {item.get('item_type')}")

    # 3. NAG POLICY CHECK
    if expected_nag is not None:
        for i, item in enumerate(items):
            if item.get("nag_policy") != expected_nag:
                failures.append(f"item[{i}].nag_policy: expected {expected_nag}, got {item.get('nag_policy')}")

    # 4. DUE_AT CHECK
    if "due_at" in expect:
        due_val = items[0].get("due_at")
        if expect["due_at"] == "set" and due_val is None:
            failures.append("due_at: expected set, got null")
        elif expect["due_at"] == "null" and due_val is not None:
            failures.append(f"due_at: expected null, got {due_val}")

    return len(failures) == 0, failures


@pytest.mark.eval
@pytest.mark.asyncio
async def test_full_pipeline_chat_eval(auth_client: AsyncClient):
    cases = load_cases()
    passed = 0
    total = len(cases)
    failure_details = []

    print("\n🚀 Starting Full Integration Eval (POST /chat) sequentially...")

    for i, case in enumerate(cases):
        name = case["name"]
        input_text = case["input"]
        expect = case["expect"]

        print(f"Running pipeline case {i+1}/{total}: {name}...", end="", flush=True)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # ── REAL HTTP POST /chat CALL ──
                response = await auth_client.post("/chat", json={"text": input_text})

                if response.status_code == 201:
                    data = response.json()
                    ok, reasons = check_chat_case(data, expect)
                    if ok:
                        passed += 1
                        print(" Passed! ✅")
                    else:
                        failure_details.append((name, input_text, expect, reasons))
                        print(" Failed! ❌")
                    break
                else:
                    err_text = response.text
                    if "429" in err_text or "rate_limit" in err_text:
                        wait_time = 10.0
                        match = re.search(r"try again in (\d+\.?\d*)s", err_text)
                        if match:
                            wait_time = float(match.group(1)) + 1.5
                        print(f"\n[Rate Limit] Sleeping {wait_time:.1f}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        failure_details.append((name, input_text, expect, [f"HTTP {response.status_code}: {err_text}"]))
                        print(" Failed! ❌")
                        break
            except Exception as e:
                failure_details.append((name, input_text, expect, [f"EXCEPTION: {e}"]))
                print(" Failed! ❌")
                break

        # 1.5s delay between cases for Rate Limit safety
        await asyncio.sleep(1.5)

    print("\n" + "=" * 60)
    print("  INTEGRATION EVAL RESULTS (POST /chat Pipeline)")
    print("=" * 60)

    for name, input_text, expect, reasons in failure_details:
        print(f"\n  FAIL  {name}")
        print(f"    input:    \"{input_text}\"")
        print(f"    expected: {expect}")
        print(f"    got:      {reasons}")

    print("\n" + "-" * 60)
    print(f"  PIPELINE SCORE: {passed}/{total} ({passed * 100 // total}%)")
    print("=" * 60 + "\n")

    assert passed > 0, "All pipeline cases failed"