"""LLM-as-judge stub.

TODO (Sunday morning): send the case, the agent transcript, and the rubric to a
stronger model and return a structured verdict.

Official guidance (verified):
- OpenAI evaluation best practices, including LLM-as-judge:
  https://developers.openai.com/api/docs/guides/evaluation-best-practices
- Graders: https://developers.openai.com/api/docs/guides/graders

Practical tips from those docs:
  - Use a clear rubric (the test cases already have one).
  - Ask the judge to reason first, then emit a structured score (e.g. JSON
    with pass: bool, score: 0-5, and a one-sentence reason).
  - Prefer pass/fail plus a short justification over a fuzzy 1-10 scale.
  - Calibrate against a handful of hand-labelled cases before you trust it.
  - Watch for verbosity bias (judges prefer longer answers).

Until this is implemented, the runner still scores *tool-call agreement*
deterministically (expected tool names vs actual) and leaves `judge` as null.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shopping_agent.llm.client import LLMClient


@dataclass
class JudgeVerdict:
    passed: bool | None
    score: float | None
    reason: str
    raw: Any = None


class JudgeNotImplementedError(NotImplementedError):
    pass


def judge_case(
    *,
    case: dict[str, Any],
    result_text: str,
    tool_calls: list[dict[str, Any]],
    client: LLMClient | None = None,
) -> JudgeVerdict:
    """Return an LLM-as-judge verdict for one eval case.

    TODO: format a prompt with case['prompt'], case['rubric'], the tool-call
    log, and result_text; call `client.complete`; parse JSON from the reply.
    """
    raise JudgeNotImplementedError(
        "LLM-as-judge is a Sunday TODO. Implement judge_case() in "
        "shopping_agent/evals/judge.py. The harness already records tool-call "
        "agreement without it."
    )
