"""Input and output guardrails.

TODO: implement the checks sketched below and call them from the agent
loop *before* the first LLM call (input) and *before* returning the final reply
(output). Keep this module free of provider-specific code.

Ideas that map well to a grocery assistant and to the eval set's safety cases:

Input
  - Prompt-injection / jailbreak phrases ("ignore previous instructions",
    "reveal your system prompt", "you are now DAN").
  - Requests that are clearly out of scope (medical dosing, legal advice,
    building weapons, anything unrelated to grocery shopping).
  - Requests to change prices, exfiltrate other customers' orders, or dump
    hidden prompts.

Output
  - Do not invent allergen or dietary claims that are not in the tool result.
  - Do not invent order statuses.
  - Refuse to provide another customer's personal data.
  - Keep refunds / policy answers grounded in retrieved policy text.

A simple first version can be keyword / regex heuristics plus a short
"if in doubt, refuse and offer to escalate" policy. A later version can add an
LLM classifier — but heuristics are enough for the safety eval cases.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str | None = None
    refusal_message: str | None = None


def check_input(user_message: str) -> GuardrailResult:
    """Return whether the user message should be sent to the agent.

    TODO: implement real checks. The current stub allows everything so the
    eval harness can run against a dummy agent without false refusals.
    """
    _ = user_message
    return GuardrailResult(allowed=True)


def check_output(user_message: str, assistant_message: str) -> GuardrailResult:
    """Return whether the assistant message is safe to show.

    TODO: implement real checks (allergens, PII, policy grounding).
    """
    _ = (user_message, assistant_message)
    return GuardrailResult(allowed=True)
