# Manual Test Scenarios (browser, test_client.html)

These were run manually against `/ws/chat` while building the app. Kept here so the
same steps/results can be reused verbatim in `README_SUBMISSION.md`'s "How to test" section.

Tokens below were minted with the default `.env` `JWT_SECRET` — regenerate with
`python mint_tokens.py` if they've expired (7-day TTL) or the secret changed.

---

## Scenario 1 — Invalid token (auth_failed)

1. Paste garbage text (e.g. `abc123`) into the JWT field → Connect.
2. **Expected:** `auth failed: invalid token`, connection closes.
3. **Result:** ✅ Pass.

---

## Scenario 2 — `emp-001` (department=hr, level=1)

Token:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlbXAtMDAxIiwiZW1haWwiOiJlbXBAdGVzdC5jb20iLCJkZXBhcnRtZW50IjoiaHIiLCJsZXZlbCI6MSwiaWF0IjoxNzg5OTAyNjkyLCJleHAiOjE3OTA1MDc0OTJ9.MEKWYiF2c8ky3dCCzfp5Itpk3FCz1NmQFBJssO62zUk
```

| Message | Expected | Result |
|---|---|---|
| `hi there` | Normal greeting, no forced context | ✅ Pass |
| `how many annual leave days do I get?` | Answer citing `leave_policy.pdf` (22 days) | ✅ Pass |
| `what is the performance review rating scale?` | NOT visible (hr, but access_level 2 > user's level 1) | ✅ Pass — "no information available" |
| `what is the expense reimbursement policy?` | NOT visible (finance, not hr) | ✅ Pass |
| `who is my manager?` | Tool call (`get_employee_context`) → "John Smith" | ✅ Pass (after a transient 429 retry) |

---

## Scenario 3 — `mgr-002` (department=hr, level=2)

Token:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtZ3ItMDAyIiwiZW1haWwiOiJtZ3JAdGVzdC5jb20iLCJkZXBhcnRtZW50IjoiaHIiLCJsZXZlbCI6MiwiaWF0IjoxNzg5OTAyNjkyLCJleHAiOjE3OTA1MDc0OTJ9.b_oT-YybYReCKE4er4nIBlxP86BACta-PaNH5jLxdRQ
```

| Message | Expected | Result |
|---|---|---|
| `what is the performance review rating scale?` | NOW visible (hr, level 2 ≤ 2) | ✅ Pass — full 5-point scale returned, cited |
| `what is the expense reimbursement policy?` | NOT visible (finance) | ✅ Pass |
| `what is the compensation committee policy?` | NOT visible (**exec**, level 3 — hr does not get exec's documents) | ✅ Pass — proves the HR exception is one-directional |
| `what is the strategic plan for 2026?` | NOT visible (exec) | ✅ Pass |

---

## Scenario 4 — `exec-003` (department=exec, level=3)

Token:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJleGVjLTAwMyIsImVtYWlsIjoiZXhlY0B0ZXN0LmNvbSIsImRlcGFydG1lbnQiOiJleGVjIiwibGV2ZWwiOjMsImlhdCI6MTc4OTkwMjY5MiwiZXhwIjoxNzkwNTA3NDkyfQ.cE4bz_6ph6iWDet1JvqiG5jBD-38H0xEyhvSTka8lsY
```

| Message | Expected | Result |
|---|---|---|
| `what is the compensation committee policy?` | Visible (own exec doc) | ✅ Pass, correctly cited (compensation_committee.pdf) |
| `what is the strategic plan for 2026?` | Visible (own exec doc, **OCR-sourced**) | ✅ Pass — 3 consecutive runs, correct and consistent, confirms the tool-hallucination fix holds |
| `what is the performance review rating scale?` | Visible (hr exception, level 2 ≤ 3) | ✅ Pass |
| `what is the expense reimbursement policy?` | NOT visible (finance) | ✅ Pass (after a transient per-minute 429 — free tier allows 5 req/min on gemini-2.5-flash, retried ~15s later) |
| `who is my manager?` / `what team am I on?` | Tool call → "John Smith" / "Platform" | ✅ Pass, elapsed ~1s for the tool itself (verified in isolation, see below) |

---

## Isolated timing check — parallel tool call

Run directly (bypasses the LLM round-trip to measure only the tool):
```bash
python -c "
import asyncio, time
from app.features.feature_employee_tool.tool_get_employee_context import tool_get_employee_context

async def main():
    t0 = time.monotonic()
    result = await tool_get_employee_context('emp-001')
    print(f'elapsed: {time.monotonic()-t0:.2f}s', result)

asyncio.run(main())
"
```
**Result:** `elapsed: 1.01s` — confirms `asyncio.gather` runs the 3 mock calls concurrently (not ~3s sequential).

---

## Known issues found & fixed during testing

1. **Gemini free-tier 429 (rate limit).** `gemini-3.6-flash` (a newer/preview-tier model) only
   allows 20 free requests/day. Error handling itself worked correctly (user-facing `error`
   event, connection stayed open) — this was a quota problem, not a bug. Fixed by switching
   to `gemini-2.5-flash` (see `.env` `GEMINI_MODEL`).
2. **Tool hallucination on `gemini-2.5-flash-lite`.** The lite model sometimes invented
   nonexistent tool names (e.g. `get_strategic_plan`) when document names appeared in the
   RAG context, instead of reading the context directly. The SDK's automatic function
   calling raised a `KeyError` for the unknown tool, which surfaced correctly as a
   user-facing `error` (connection stayed open) but left the question unanswered. Fixed by
   (a) tightening the system prompt to state explicitly that `get_employee_context` is the
   only tool and document content never requires a tool call, and (b) switching off the
   `-lite` model tier to the full `gemini-2.5-flash` for more reliable tool-call judgment.
   Confirmed fixed: 3 consecutive runs of the strategic_plan question all answered correctly.
3. **Gemini free-tier per-minute limit (5 req/min on `gemini-2.5-flash`).** Firing several
   test messages back-to-back triggered a `429` with `retryDelay: ~10s`. Again, error
   handling worked as designed (user-facing error, connection open) — waiting ~15s and
   resending succeeded. Not a code issue; a free-tier characteristic worth noting in the
   submission README's tradeoffs section.

---

## Provider swap test (pluggability)

`LLM_PROVIDER` in `.env` switches between `gemini` (default) and `openai` with no code
changes (`app/core/dependencies.py::get_llm_provider`). Both a Gemini key and an OpenAI key
are present in `.env` for this comparison.

- [x] RAG question (`what is the strategic plan for 2026?`) with `LLM_PROVIDER=openai` (model `gpt-4o-mini`) — ✅ correct answer, cited `strategic_plan.pdf`
- [x] Tool-call question (`who is my manager and what team am I on?`) with `LLM_PROVIDER=openai` — ✅ correct ("John Smith", "Platform"), via OpenAI's manual tool-call loop (`openai_provider.py`)
- Switched back to `LLM_PROVIDER=gemini` as the submitted default (free tier, no billing required).
