"""Eval runner.

Loads evals/test_cases.yaml, runs each case through an agent, scores tool-call
agreement, optionally calls the LLM judge (TODO), and writes
evals/results/latest.json plus evals/results/latest.md.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from shopping_agent.backend import ShoppingService
from shopping_agent.config import REPO_ROOT, get_settings

DEFAULT_CASES = REPO_ROOT / "evals" / "test_cases.yaml"
DEFAULT_OUT_DIR = REPO_ROOT / "evals" / "results"


def load_cases(path: Path = DEFAULT_CASES) -> list[dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return list(payload["cases"])


def tool_agreement(expected: list[str], actual: list[str]) -> dict[str, Any]:
    """Precision / recall / F1 over tool *names* (order-insensitive, multiplicity-light)."""
    expected_set = set(expected)
    actual_set = set(actual)
    if not expected_set and not actual_set:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "passed": True, "missing": [], "unexpected": []}
    if not expected_set:
        # Safety / out-of-scope cases: any tool call is unexpected.
        return {
            "precision": 0.0 if actual_set else 1.0,
            "recall": 1.0,
            "f1": 0.0 if actual_set else 1.0,
            "passed": not actual_set,
            "missing": [],
            "unexpected": sorted(actual_set),
        }
    true_pos = expected_set & actual_set
    precision = len(true_pos) / len(actual_set) if actual_set else 0.0
    recall = len(true_pos) / len(expected_set) if expected_set else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "passed": expected_set.issubset(actual_set),
        "missing": sorted(expected_set - actual_set),
        "unexpected": sorted(actual_set - expected_set),
    }


def _build_agent(kind: str, service: ShoppingService, customer_id: str):
    if kind == "dummy":
        from shopping_agent.evals.dummy_agent import DummyAgent

        return DummyAgent(service=service, customer_id=customer_id)
    if kind == "real":
        from shopping_agent.agent.loop import ShoppingAgent

        return ShoppingAgent(service=service, customer_id=customer_id)
    raise ValueError(f"Unknown agent kind {kind!r}. Use 'dummy' or 'real'.")


def run_case(agent: Any, case: dict[str, Any]) -> dict[str, Any]:
    customer_id = case.get("customer_id") or get_settings().default_customer_id
    # Fresh service per case so carts / issues do not leak across the suite.
    if hasattr(agent, "service"):
        agent.service = ShoppingService.default()
    if hasattr(agent, "customer_id"):
        agent.customer_id = customer_id

    error = None
    try:
        result = agent.run(case["prompt"], customer_id=customer_id)
        text = result.text
        tool_calls = result.tool_calls or []
        refused = bool(getattr(result, "refused", False))
    except NotImplementedError as exc:
        text = ""
        tool_calls = []
        refused = False
        error = str(exc)
    except Exception as exc:  # noqa: BLE001 - eval boundary
        text = ""
        tool_calls = []
        refused = False
        error = f"{type(exc).__name__}: {exc}"

    actual_names = [call.get("name", "") for call in tool_calls]
    expected_names = list(case.get("expected_tools") or [])
    agreement = tool_agreement(expected_names, actual_names)

    judge = None
    if case.get("use_judge", True):
        try:
            from shopping_agent.evals.judge import judge_case

            verdict = judge_case(case=case, result_text=text, tool_calls=tool_calls)
            judge = {
                "passed": verdict.passed,
                "score": verdict.score,
                "reason": verdict.reason,
            }
        except NotImplementedError:
            judge = None

    passed = agreement["passed"] and error is None
    # Safety cases also require a refusal / no-tool behaviour, already in agreement.
    if case.get("expect_refusal"):
        passed = passed and (refused or not actual_names)

    return {
        "id": case["id"],
        "title": case.get("title", case["id"]),
        "tags": case.get("tags", []),
        "prompt": case["prompt"],
        "customer_id": customer_id,
        "expected_tools": expected_names,
        "actual_tools": actual_names,
        "tool_agreement": agreement,
        "expect_refusal": bool(case.get("expect_refusal")),
        "refused": refused,
        "response": text,
        "tool_calls": tool_calls,
        "judge": judge,
        "error": error,
        "passed": passed,
        "rubric": case.get("rubric", ""),
    }


def render_markdown(run: dict[str, Any]) -> str:
    rows = []
    for case in run["cases"]:
        mark = "pass" if case["passed"] else "fail"
        judge = (
            "-"
            if case["judge"] is None
            else (f"{case['judge'].get('score')} ({'pass' if case['judge'].get('passed') else 'fail'})")
        )
        rows.append(f"| {case['id']} | {case['title']} | {mark} | {case['tool_agreement']['f1']:.2f} | {judge} |")
    table = "\n".join(
        [
            "| id | title | tool match | tool F1 | judge |",
            "|----|-------|------------|---------|-------|",
            *rows,
        ]
    )
    return (
        f"# Eval results\n\n"
        f"- Agent: `{run['agent']}`\n"
        f"- Ran at: {run['started_at']}\n"
        f"- Cases: {run['summary']['total']}\n"
        f"- Tool-match passes: {run['summary']['passed']}/{run['summary']['total']}\n"
        f"- Mean tool F1: {run['summary']['mean_tool_f1']}\n"
        f"- Judge: {run['summary']['judge_status']}\n\n"
        f"{table}\n\n"
        f"LLM-as-judge is a TODO until "
        f"`shopping_agent.evals.judge.judge_case` is implemented. Tool-match is a deterministic "
        f"baseline (expected tool names vs actual).\n"
    )


def run_suite(
    *,
    agent_kind: str = "dummy",
    cases_path: Path = DEFAULT_CASES,
    out_dir: Path = DEFAULT_OUT_DIR,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    cases = load_cases(cases_path)
    # Shared unused service just so we have a constructor hook; each case resets it.
    service = ShoppingService.default()
    agent = _build_agent(agent_kind, service, get_settings().default_customer_id)
    results = []
    for case in cases:
        if progress:
            progress(f"running {case['id']}: {case.get('title', '')}")
        results.append(run_case(agent, case))

    f1s = [case["tool_agreement"]["f1"] for case in results]
    mean_f1 = round(sum(f1s) / len(f1s), 3) if f1s else 0.0
    passed = sum(1 for case in results if case["passed"])
    judge_used = any(case["judge"] is not None for case in results)
    run = {
        "agent": agent_kind,
        "started_at": datetime.now(UTC).isoformat(),
        "cases": results,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": len(results) - passed,
            "mean_tool_f1": mean_f1,
            "judge_status": "enabled" if judge_used else "not_implemented",
        },
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest.json").write_text(json.dumps(run, indent=2, default=str) + "\n", encoding="utf-8")
    (out_dir / "latest.md").write_text(render_markdown(run), encoding="utf-8")
    return run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Harbour Basket agent eval suite.")
    parser.add_argument("--agent", choices=("dummy", "real"), default="dummy")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)
    run = run_suite(agent_kind=args.agent, cases_path=args.cases, out_dir=args.out, progress=print)
    summary = run["summary"]
    print(
        f"\nDone. {summary['passed']}/{summary['total']} passed tool-match, "
        f"mean F1={summary['mean_tool_f1']}, judge={summary['judge_status']}."
    )
    print(f"Wrote {args.out / 'latest.md'}")
    return 0 if summary["failed"] == 0 or args.agent == "dummy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
