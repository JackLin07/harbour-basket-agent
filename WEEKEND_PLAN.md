# Weekend plan

This coming weekend is Saturday 28 and Sunday 29 November 2026 (Melbourne,
Australia/Melbourne, UTC+11). The AI Engineer application is time-sensitive,
so treat Sunday evening as hard stop: README filled in, evals run, repo pushed.

The scaffold around you is done. Your job is the agent. Every TODO below points
at a real file.

Before you start: `cp .env.example .env` and add one API key. OpenAI is the
most documented path for tool calling; Azure OpenAI is the closest match to
the job listing; xAI Grok is also supported (OpenAI-compatible). Then:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,llm]"
make test
harbour-basket search "avocado"   # sanity check the backend
```

---

## Saturday — get an agent in the loop

### 08:30–09:00 — Read the official tool-calling primer

- OpenAI function calling:
  https://developers.openai.com/api/docs/guides/function-calling
- xAI Grok (OpenAI-compatible, if you set `LLM_PROVIDER=xai`):
  https://docs.x.ai/docs/overview
- Anthropic tool use (if you pick Claude):
  https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview

You only need the loop: send tools → model may return a tool call → you run it
→ you send the result back → model answers in prose. That is the whole agent.

### 09:00–10:30 — LLM client

File: [`src/shopping_agent/llm/client.py`](src/shopping_agent/llm/client.py)

Implement **one** of `OpenAILLMClient`, `AzureOpenAILLMClient`, or
`AnthropicLLMClient`, and wire it in `build_client()`. Keep the
`LLMResponse` / `ToolCall` shapes so the loop stays provider-agnostic.

If you want to use Grok, set `LLM_PROVIDER=xai` and `XAI_API_KEY` in `.env`.
xAI's API is OpenAI-compatible ([docs](https://docs.x.ai/docs/overview),
endpoint `https://api.x.ai/v1`), so the same `OpenAILLMClient` works for both
OpenAI and xAI when you pass `base_url`. Call `get_provider_endpoint(settings)`
to get the base URL, key, and model (defaults: `grok-4.20-non-reasoning` for
the agent, `grok-4.7` for the judge; override with `LLM_MODEL` / `JUDGE_MODEL`).

Sanity check with a tiny script or a `python` REPL: send "say hello" with no
tools and print `response.text`.

### 10:30–12:30 — Tool schemas + dispatch

File: [`src/shopping_agent/agent/tools.py`](src/shopping_agent/agent/tools.py)

Fill `TOOL_SCHEMAS` and `execute_tool()`. The service is already implemented:

| Tool | Service method |
|------|----------------|
| `search_products` | `service.search_products(...)` |
| `add_to_cart` | `service.add_to_cart(customer_id, product_id, quantity)` |
| `view_cart` | `service.view_cart(customer_id)` |
| `check_order` | `service.get_order(...)` or `service.list_orders(...)` |
| `report_issue` | `service.report_issue(...)` |
| `retrieve_knowledge` | your retriever, after the afternoon session |

Catch `ShoppingError` with `error_payload()` and always return a JSON string.

Unskip `test_tool_schemas_are_registered` and `test_execute_search_tool` in
[`tests/test_agent.py`](tests/test_agent.py) when they should pass.

### 12:30–13:00 — Lunch

### 13:00–15:30 — The agent loop

File: [`src/shopping_agent/agent/loop.py`](src/shopping_agent/agent/loop.py)

Write `SYSTEM_PROMPT` and `ShoppingAgent.run()` as a plain `for` loop up to
`settings.max_tool_iters`. Hook [`src/shopping_agent/tracing.py`](src/shopping_agent/tracing.py)
(`JsonlTracer`) around each LLM and tool call.

Then:

```bash
harbour-basket chat "I want some ripe avocados for smashed avo"
harbour-basket chat "Add a kilo of bananas to my basket"
harbour-basket cart
```

If those three work, you already have a demo.

### 15:30–18:00 — Simple RAG

Files:

- Corpus (done): [`src/shopping_agent/rag/chunks.py`](src/shopping_agent/rag/chunks.py)
- Helpers (done): [`src/shopping_agent/rag/embeddings.py`](src/shopping_agent/rag/embeddings.py)
- Your work: [`src/shopping_agent/rag/retriever.py`](src/shopping_agent/rag/retriever.py)

Read, then pick an embedder:

- Local and free: sentence-transformers quickstart —
  https://sbert.net/docs/quickstart.html
  (`pip install -e ".[rag]"`, model `sentence-transformers/all-MiniLM-L6-v2`)
- API: OpenAI embeddings —
  https://developers.openai.com/api/docs/guides/embeddings
- Azure OpenAI embeddings, if you want the README to mention AI Foundry

Implement `InMemoryRetriever.build()` and `.retrieve()` using
`cosine_similarity`. Wire a `retrieve_knowledge` tool. Test with:

```bash
harbour-basket chat "How much is delivery, and when is it free?"
```

You should see the $9 / $50 rule from `data/policies/delivery.md`, not an
invented fee. A `HashingEmbedder` exists only to test wiring — do not demo it.

### 18:00–19:30 — MCP server

File: [`src/shopping_agent/mcp_server/server.py`](src/shopping_agent/mcp_server/server.py)

Official Python SDK (v2 docs, verified):

- https://py.sdk.modelcontextprotocol.io/
- Install: https://py.sdk.modelcontextprotocol.io/get-started/installation/
- Run: https://py.sdk.modelcontextprotocol.io/run/
- Source: https://github.com/modelcontextprotocol/python-sdk

`pip install -e ".[mcp]"`. Wrap the same tools. `make mcp` should start a
stdio server. If you have Node.js, `mcp dev` gives you the Inspector.

Check the installed major version — v2 uses `from mcp.server import MCPServer`;
older v1 tutorials use `FastMCP`. Follow the docs for what you installed and
note it in the README.

### 19:30–20:00 — Guardrails first cut + commit

File: [`src/shopping_agent/agent/guardrails.py`](src/shopping_agent/agent/guardrails.py)

Cover the easy safety cases in [`evals/test_cases.yaml`](evals/test_cases.yaml)
(E23–E26): medical dosing, "ignore previous instructions", jailbreak / DAN,
malware. Keyword checks are enough tonight. Call `check_input` at the start
of `run()` and skip the LLM on a refusal.

Commit locally. You will push on Sunday once GitHub exists.

---

## Sunday — evals, packaging, README

### 08:30–09:00 — Official evals primer

- LLM-as-judge and evaluation design:
  https://developers.openai.com/api/docs/guides/evaluation-best-practices
- Graders: https://developers.openai.com/api/docs/guides/graders

Takeaway: a clear rubric, reason-then-score, prefer pass/fail over a fuzzy
1–10, watch verbosity bias.

### 09:00–11:30 — LLM-as-judge + run the suite

File: [`src/shopping_agent/evals/judge.py`](src/shopping_agent/evals/judge.py)

Implement `judge_case()` so it returns `JudgeVerdict` from a JSON score and
the case rubric. Then:

```bash
python -m shopping_agent.evals.runner --agent real
```

Read `evals/results/latest.md`. You will fail some cases. That is useful.
Fix the two or three most embarrassing ones (wrong tool, invented fee,
missed allergy filter) rather than chasing 30/30.

The dummy agent (`make eval`) is only a harness smoke test. Do not put dummy
scores in the README.

### 11:30–13:00 — Docker, CI, a short demo

```bash
make lint
make test
make docker-build   # if Docker is installed
```

GitHub Actions already lints and tests, and has an optional eval job gated
on an API-key secret (`OPENAI_API_KEY` or `XAI_API_KEY`). If only the xAI
secret is set, the job passes `LLM_PROVIDER=xai`. Record a 60–90 second CLI
walkthrough (search, add to cart, check `ORD-5002`, ask about delivery fees)
or a few terminal screenshots for the README.

### 13:00–15:00 — README in your own voice

File: [`README.md`](README.md)

Fill in every `TODO`:

- Pitch (three or four sentences)
- Design trade-offs (rewrite, do not just leave the starter bullets)
- Eval results table, copied from `evals/results/latest.md`, plus what failed
  and what you changed
- "What I would do in production" — AKS, Cosmos DB, AI Foundry, tracing,
  cost/latency. This is where a platform-engineer background stands out.

### 15:00–16:00 — Push and apply

Create a **public** GitHub repository, add it as `origin`, and push `main`.
Do not force-push after you send the link.

A draft note to HR is in [`docs/APPLICATION_DRAFT.md`](docs/APPLICATION_DRAFT.md).
If the application went out earlier, reply with the repo URL.

---

## If you run short on time

Cut in this order (keep the earlier item, drop the later one):

1. Keep the agent loop, tools, and evals.
2. Keep RAG; it is what makes the policy answers honest.
3. Ship MCP as a thin wrapper if you can; mention it even if Inspector
   polish is missing.
4. A hashing-embedder retriever is worse than no retriever in the README —
   say you would use sentence-transformers and show the code path, or spend
   the 20 minutes to wire MiniLM.
5. Skip a web UI. The CLI is enough.
6. Never skip the synthetic-data notice or the honesty about what you did
   not have time to finish.

## Useful ids while you test

| What | Id |
|------|----|
| Default customer | `CUST-1001` Maya Chen (pescatarian, avoids peanuts) |
| Vegan customer | `CUST-1004` |
| Gluten-free customer | `CUST-1003` |
| In-transit order | `ORD-5002` |
| Missing butter | `ORD-5003` / `HB-3008` |
| Click & collect | `ORD-5016` (CUST-1002) |
| Out of stock | `HB-1017` raspberries |
| Hass avocados | `HB-1001` |
| Gluten-free pasta | `HB-5038` |
| Oat milk | `HB-3005` |
