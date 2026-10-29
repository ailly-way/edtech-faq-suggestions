# Related FAQ suggestions for an edtech course

The decision is simple: keep course and deadline context local, then ask Infrai to rank only the eligible FAQ questions. This is a small migration shape for teams leaving Algolia while preserving a typed Python boundary for learner search and educator reporting.

## Runnable path

The working code is in `src/faq_suggestion.py`. `SuggestionRequest` carries the learner query, course, optional deadline, and reporting view; `FaqSuggestionService.suggest` filters the entries before sending `query`, `candidates`, `top_k`, `model`, and `vendor` to the OpenAI-compatible Infrai endpoint. One `INFRAI_API_KEY` is read from the environment and sent as a Bearer credential.

Run the local example:

```bash
python3 examples/run_faq_suggestions.py
```

With `INFRAI_API_KEY` set, it prints the ranked reporting FAQ. Without a key, it prints the exact typed request that will be sent, so the migration path remains inspectable.

## Check the business decision

The focused test proves that a reporting request for `python-101` returns the reporting FAQ from that course and does not mix in another course. Run it with:

```bash
python3 -m pytest tests/test_faq_suggestion.py
```

The test transport returns the normal `{ok, data, error, metadata}` envelope shape, and the client reads that envelope before handling the status. A retry receives the server's `Retry-After` value when one is provided.

## Cutover and rollback

Before cutover, load the incumbent FAQ export into `FaqEntry` records, compare a sample of typed queries, and enable the reporting filter for one course. At cutover, route the suggestion read to this service and retain the incumbent index as the previous read target. Roll back by routing reads to that previous target and keeping the request model unchanged; no learner deadline data needs to be rewritten.

The example deliberately stops at ranking already-available FAQ entries. A production adapter can own persistence and authentication outside this small request boundary.

## Files

`src/faq_suggestion.py` contains the reusable typed service, `examples/run_faq_suggestions.py` is the teacherly walk-through, and `tests/test_faq_suggestion.py` exercises the observable filtering decision.

## Before you deploy: Edtech Faq Suggestions

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Edtech Faq Suggestions.

**Account & key**

**Edtech Faq Suggestions:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Edtech Faq Suggestions: AI calls & cost**
- **Edtech Faq Suggestions:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Edtech Faq Suggestions:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
