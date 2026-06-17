# Pakistani Fashion Aggregator — Detailed Build Prompts

> Copy-paste prompts for an AI coding agent (Cursor, Claude Code, etc.) to build the
> project described in [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md). Run them
> **in order** — each prompt assumes the previous one succeeded. After each prompt, review
> the diff, run the stated verification command, and commit before moving on.

## How to use this file

1. Start each prompt with the **Global Context** block below (paste it once at the start of
   a session, or prepend it to every prompt if the agent loses context).
2. Run prompts sequentially: `P0 → P10`.
3. Each prompt has a **Goal**, the **Prompt** to paste, **Files**, and a **Verify** step.
4. Do not let the agent invent store data or size charts — those come from the verification
   script (P2) and official brand size guides.

---

## Global Context (prepend to any prompt)

```
You are building a "Pakistani Live Fashion Aggregator": a database-free, multi-agent
fashion search engine. A 3-agent LangGraph pipeline (Planner → Retrieval → Ranker) powered
by Gemini 2.5 Flash reasons about user intent, selects relevant Pakistani clothing stores,
fetches live product JSON (Shopify /products.json and WooCommerce Store API), filters,
maps sizes, and re-ranks by semantic relevance.

Authoritative references in this repo:
- docs/IMPLEMENTATION_PLAN.md  (architecture, milestones, data contracts, error matrix)
- docs/AGENT_PROMPTS.md         (this file)

Rules:
- Backend: Python 3.11+, FastAPI, async httpx, Pydantic v2, LangGraph, google-generativeai.
- Frontend: Next.js 14 (App Router, src dir), TypeScript, Tailwind.
- Follow the exact data contracts in IMPLEMENTATION_PLAN.md §5. Keep Pydantic models and
  TypeScript types in sync.
- Tools (tools/*.py) are deterministic — NO LLM calls inside them.
- Agent nodes are async; never call asyncio.get_event_loop().run_until_complete() inside a
  running event loop. Wrap the sync Gemini SDK call with asyncio.to_thread, and fetch stores
  concurrently with asyncio.gather.
- Never hardcode secrets. Read GEMINI_API_KEY from the environment.
- Every tool must fail safe (return an error-flagged result, never raise to the caller).
- Write unit tests as you go (pytest, pytest-asyncio, respx for httpx mocking).
```

---

## P0 — Repo & Tooling Bootstrap

**Goal:** Runnable empty backend + frontend skeletons.

**Prompt**
```
Bootstrap the monorepo.

Backend (backend/):
- Create a Python project with a virtualenv-friendly layout.
- requirements.txt with: fastapi, uvicorn[standard], httpx, pydantic>=2,
  google-generativeai, python-multipart, langgraph>=0.2.0, langchain-google-genai>=1.0.0,
  and dev deps pytest, pytest-asyncio, respx.
- main.py: a minimal FastAPI app with CORS (allow http://localhost:3000) and a
  GET /api/health endpoint returning {"status": "ok"}.
- .env.example with GEMINI_API_KEY=, STORE_TIMEOUT=2.5, ALLOWED_ORIGINS=http://localhost:3000
- Empty package dirs with __init__.py: agents/, tools/, routers/, models/, config/,
  scripts/, tests/.

Frontend (frontend/):
- Scaffold Next.js 14 with: npx create-next-app@latest frontend --typescript --tailwind
  --app --src-dir --eslint --no-import-alias (accept defaults otherwise).
- Add .env.local.example with NEXT_PUBLIC_API_URL=http://localhost:8000

Root:
- .gitignore covering: .venv/, __pycache__/, *.pyc, node_modules/, .next/, .env, .env.local
- Update README.md with local run instructions for both apps.
```

**Verify**
- `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn main:app --reload` then `curl localhost:8000/api/health`.
- `cd frontend && npm install && npm run dev`.

---

## P1 — Data Contracts (schemas)

**Goal:** Lock the Pydantic + TypeScript contracts before building logic.

**Prompt**
```
Implement the data contracts from IMPLEMENTATION_PLAN.md §5.

Backend (backend/models/schemas.py), Pydantic v2:
- ParsedQuery: item_type:str|None, color:str|None, material:str|None,
  gender:Literal["men","women","unisex","any"]="any",
  price_tier:Literal["budget","mid","premium","luxury","any"]="any",
  style_category:str|None, min_price:float|None, max_price:float|None,
  generic_size:str|None, occasion:str|None.
- Product: id, store_name, store_slug, title, price:float, compare_price:float|None,
  currency:str="PKR", available_sizes:list[str], matched_size:str|None,
  image_url:str|None, product_url:str, tags:list[str]=[], relevance_score:float|None=None.
- SearchResponse: results:list[Product], total_count:int, stores_queried:int,
  stores_responded:int, failed_stores:list[str], query_parsed:ParsedQuery|dict,
  search_summary:str, retrieval_iterations:int.

Frontend (frontend/src/lib/types.ts):
- Mirror ParsedQuery, Product, and SearchResponse as TypeScript interfaces with identical
  field names and nullability.
```

**Verify**
- `python -c "from models.schemas import Product, SearchResponse, ParsedQuery"` from `backend/`.

---

## P2 — Store Verification Script + Config

**Goal:** Discover which stores actually expose public JSON; build `stores.json`.

**Prompt**
```
Create backend/scripts/verify_stores.py.

Input: a hardcoded list of candidate stores (use Appendix A of IMPLEMENTATION_PLAN.md:
brand, domain, suspected platform, price_tier, gender, categories).

For each candidate, async with httpx:
- Probe Shopify:  https://<domain>/products.json?limit=1
- Probe WooCommerce: https://<domain>/wp-json/wc/store/v1/products?per_page=1
- Use a 6s timeout, follow_redirects=True, a descriptive User-Agent.
- Record: HTTP status for each endpoint, whether JSON parsed, and product count seen.

Output:
- Print a results table (brand | shopify_status | woo_status | detected_platform).
- Write backend/config/stores.json with one entry per store using the detected platform.
  Schema per store: slug, name, base_url (https://domain), platform ("shopify"|"woocommerce"),
  products_endpoint ("/products.json" or "/wp-json/wc/store/v1/products"),
  price_tier, gender, categories[], active (true only if at least one endpoint returned 200
  with valid JSON; otherwise false).

Also create backend/config/size_charts.json seeded with 3 brands (sapphirepk, outfitters,
generation) using the example values from the concept plan; add a top comment-free note in
the plan that remaining charts must be filled from official size guides.

Make the script idempotent and safe to re-run.
```

**Verify**
- `cd backend && python scripts/verify_stores.py` (needs network; if blocked, note which stores were unreachable and keep them `active:false`).
- `python -c "import json; d=json.load(open('config/stores.json')); print(len(d), 'stores')"`.

---

## P3 — Agent Tools (deterministic services)

**Goal:** Build and unit-test all tool functions. No LLM logic inside.

**Prompt**
```
Implement the tool functions exactly per IMPLEMENTATION_PLAN.md and the concept plan §8.
All functions live under backend/tools/. They must be deterministic and fail-safe.

tools/query_tools.py:
- parse_text_query_fn(raw_query: str) -> dict
- parse_image_query_fn(image_b64: str, mime_type: str) -> dict
  (These are schema-anchor hooks; Gemini supplies the parsed fields via function-calling.
   Validate/normalize args into the ParsedQuery shape and return a dict.)

tools/store_tools.py:
- Load config/stores.json once; ACTIVE_STORES = active only.
- select_target_stores_fn(price_tier="any", gender="any", item_type="", style_category="")
  -> list[str] of slugs. Gender matches store gender or "unisex". Price-tier mapping:
  budget->[budget]; mid->[budget,mid]; premium->[mid,premium]; luxury->[premium,luxury].
  Fallback to all active slugs if the filter yields nothing.

tools/fetch_tools.py:
- STORE_MAP from active stores; STORE_TIMEOUT from env (default 2.5).
- async fetch_store_fn(slug, search_hint) -> dict {success, slug, products|error}.
  Shopify params: {limit:100, title:search_hint?}. Woo params: {per_page:50, search:hint}.
  follow_redirects=True, descriptive User-Agent. Never raise; catch all and return success=False.
- _normalize_shopify and _normalize_woocommerce producing the Product shape from §5.2
  (only include products with availability; defensive against missing variants/images/prices;
  prices to float; Woo prices are minor units -> divide by 100).

tools/filter_tools.py:
- filter_products_fn(raw_products_json, parsed_query_json) -> {"products": [...]}.
  Accept BOTH JSON strings and native lists/dicts. Match on combined title+tags text for
  item_type/color/material; apply min_price/max_price. Return price-sorted.

tools/size_tools.py:
- Load config/size_charts.json once.
- map_product_sizes_fn(products_json, measurements_json=None, generic_size=None)
  -> {"products": [...]}. Resolve matched_size per store via _resolve_size (smallest label
  whose chest >= user chest). When a size constraint exists, drop products whose matched_size
  is not in available_sizes. Accept strings or native objects.
- broaden_search_criteria_fn(parsed_query_json, strategy) -> relaxed query dict. Strategies:
  remove_color, remove_material, increase_price_ceiling_20pct, make_size_optional,
  remove_color_and_material.

Write pytest tests under backend/tests/ for store_tools, fetch_tools (mock httpx with respx),
filter_tools, and size_tools. Cover happy paths and failure paths.
```

**Verify**
- `cd backend && pytest tests/ -q`.

---

## P4 — Agent State + Planner Node

**Goal:** Shared state and the Planner agent (intent → stores).

**Prompt**
```
Create backend/agents/state.py with the AgentState TypedDict from IMPLEMENTATION_PLAN.md §5
/ concept plan §7.1 (input fields, planner outputs, retrieval outputs, ranker outputs).

Create backend/agents/planner_agent.py:
- Configure genai with GEMINI_API_KEY.
- PLANNER_SYSTEM_PROMPT instructing: parse the query (text or image) into structured tags,
  then select ONLY relevant stores (no luxury for budget; respect gender; broaden when
  ambiguous), then produce a concise search_hint. Always call parse_* first, then
  select_target_stores.
- PLANNER_TOOLS: function declarations for parse_text_query, parse_image_query,
  select_target_stores (matching the tool signatures).
- TOOL_DISPATCH mapping names to the tools/*_fn functions.
- async planner_node(state) -> state:
  * Build the initial Gemini message; if image_bytes present, include an inline_data image
    part + instruction, else use raw_query.
  * Run the Gemini function-calling loop. IMPORTANT: model.generate_content is sync — call it
    via asyncio.to_thread. Loop until no function_call parts remain.
  * Capture parsed_query from parse_* results and target_store_slugs from
    select_target_stores. Build search_hint from item_type/color/material.
  * Return {**state, parsed_query, target_store_slugs, search_hint, retrieval_iterations:0}.
  * Wrap tool dispatch in try/except; on tool error feed an error result back to the model.
```

**Verify**
- `python -c "from agents.planner_agent import planner_node"` from `backend/`.

---

## P5 — Retrieval Node (with broaden loop)

**Goal:** Fetch → filter → size-map, with autonomous broaden-on-sparse.

**Prompt**
```
Create backend/agents/retrieval_agent.py.

Constants: MAX_ITERATIONS = 2, SPARSE_THRESHOLD = 5.

RETRIEVAL_SYSTEM_PROMPT: fetch ALL target stores first, then filter, then map sizes; if
fewer than 5 results remain and a retry is available, call broaden_search_criteria and repeat;
stop when results are sufficient or retries are exhausted.

RETRIEVAL_TOOLS: declarations for fetch_store, filter_products, map_product_sizes,
broaden_search_criteria (match tool signatures; filter/size/broaden take JSON-string args).

async retrieval_node(state) -> state:
- Build a context message with target_store_slugs, parsed_query, search_hint, measurements,
  and current iteration.
- Run the Gemini function-calling loop (generate_content via asyncio.to_thread).
- CRITICAL async handling: fetch_store_fn is async. Do NOT use run_until_complete. When the
  model requests one or more fetch_store calls in a turn, gather them concurrently with
  asyncio.gather and await directly. Other tools are sync.
- Accumulate raw products from successful fetches; record failed_stores from failures.
  Track filtered_products from filter_products / map_product_sizes results.
- Return {**state, filtered_products, failed_stores, stores_queried, stores_responded,
  retrieval_iterations: state.retrieval_iterations + 1}.
- Cap filtered_products at 30 (price-sorted) before returning, to bound Ranker cost.
- Fail-safe: wrap tool dispatch in try/except.
```

**Verify**
- `python -c "from agents.retrieval_agent import retrieval_node, MAX_ITERATIONS, SPARSE_THRESHOLD"`.

---

## P6 — Ranker Node + Graph Assembly

**Goal:** Semantic re-rank + summary, then wire the LangGraph graph.

**Prompt**
```
Create backend/agents/ranker_agent.py:
- RANKER_SYSTEM_PROMPT: re-rank products by true relevance to the original query (fabric,
  occasion, color accuracy, style), assign relevance_score 0.0–1.0, write a <=20-word
  search_summary, return ONLY valid JSON {ranked_products:[...], search_summary:""} with no
  markdown fences.
- async ranker_node(state) -> state:
  * If filtered_products is empty, return ranked_products=[] with a graceful summary.
  * Otherwise call Gemini (generate_content via asyncio.to_thread, temperature 0.2) with the
    original query, parsed intent, and the products.
  * Parse JSON defensively: strip ```json fences if present; on JSONDecodeError fall back to
    price-sorted filtered_products with no scores and a generic summary.

Create backend/agents/graph.py:
- route_after_retrieval(state): return "retrieval" if len(filtered_products) < SPARSE_THRESHOLD
  and retrieval_iterations < MAX_ITERATIONS, else "ranker".
- Build StateGraph(AgentState): nodes planner/retrieval/ranker; entry=planner;
  planner->retrieval; conditional edges from retrieval via route_after_retrieval to either
  retrieval or ranker; ranker->END. Compile to fashion_graph.

Add a smoke test backend/tests/test_graph_smoke.py that monkeypatches genai.GenerativeModel
(scripted function_call sequence) and fetch_store_fn (canned products), invokes
fashion_graph.ainvoke with a sample state, and asserts the final state has ranked_products
and search_summary.
```

**Verify**
- `cd backend && pytest tests/test_graph_smoke.py -q`.

---

## P7 — FastAPI Routers + App

**Goal:** Expose the graph over HTTP.

**Prompt**
```
Create backend/routers/search.py:
- async _run_graph(state) -> dict that awaits fashion_graph.ainvoke(state) and maps the final
  state to the SearchResponse shape (§5.3).
- POST /search/text  (Form: query:str required, measurements_json:str optional) -> builds the
  initial AgentState and runs the graph.
- POST /search/visual (File: image required, Form: measurements_json optional) -> reads bytes,
  sets image_mime_type from content_type, runs the graph.
- GET /health -> {"status":"ok"}.

Update backend/main.py:
- include_router(search.router, prefix="/api").
- CORS from ALLOWED_ORIGINS env (comma-separated; default localhost:3000).
- Global exception handler: on Gemini/network failure return HTTP 503 with a JSON
  user-readable message; never leak stack traces. Validate image size (<=5MB) and content_type
  for visual search and return 400 on violation.

Add backend/tests/test_api.py using FastAPI TestClient with the graph mocked: assert
/api/search/text returns the SearchResponse shape and error paths behave.
```

**Verify**
- `cd backend && pytest tests/test_api.py -q` and manual `curl -F 'query=mustard linen kurta' localhost:8000/api/search/text` (needs GEMINI_API_KEY for live).

---

## P8 — Frontend API Client + Components

**Goal:** Build the UI components and API layer.

**Prompt**
```
In frontend/src/lib/api.ts implement:
- searchByText(query, measurements?) -> POST {NEXT_PUBLIC_API_URL}/api/search/text (FormData).
- searchByImage(file, measurements?) -> POST .../api/search/visual (FormData).
- Both return the SearchResponse type from lib/types.ts; throw a typed error on non-2xx.

In frontend/src/components/ implement (Tailwind, accessible, responsive):
- SearchBar.tsx: controlled text input + submit; calls onSearch(query).
- VisualUpload.tsx: drag-and-drop + file picker; accept jpeg/png/webp; reject >5MB with an
  inline error; calls onUpload(file).
- MeasurementPanel.tsx: slide-out panel with chest/waist/hips number inputs (session useState).
- ResultsGrid.tsx: responsive CSS grid; skeleton loading state; empty state.
- ProductCard.tsx: fixed aspect-ratio image (no layout shift), brand badge, title, price
  (show compare_price struck-through when present), size chips (highlight matched_size), and a
  "Shop Now →" deep link to product_url (target=_blank, rel=noopener).
- StoreStatusBar.tsx: "Checked N stores · M responded · K failed".
- AgentStatusBadge.tsx: render only when retrieval_iterations > 1 ("↻ Search criteria
  broadened to find more results").
```

**Verify**
- `cd frontend && npm run build`.

---

## P9 — Frontend Page Wiring

**Goal:** Assemble the main page experience.

**Prompt**
```
Implement frontend/src/app/page.tsx as a client component that composes the components from P8:
- Tabs/toggle between text search and visual upload.
- A button to open MeasurementPanel; measurements are passed into the search calls.
- On submit: set loading, call searchByText/searchByImage, handle success/error/empty.
- Render above the grid: search_summary (one line) + StoreStatusBar + AgentStatusBadge.
- Render ResultsGrid with the results.
- Handle loading (skeletons), error (retry affordance), and empty ("no matches") states.

Give it a clean, modern, mobile-first UI with Tailwind. Update app/layout.tsx metadata
(title: "Pakistani Fashion Finder") and ensure globals.css is sensible.
```

**Verify**
- `cd frontend && npm run dev`, run a text and image search against the local backend.

---

## P10 — Deployment Artifacts

**Goal:** Containerize backend; document deploy.

**Prompt**
```
Create backend/Dockerfile:
- FROM python:3.11-slim; WORKDIR /app; copy requirements and pip install --no-cache-dir;
  copy source; EXPOSE 8000; CMD uvicorn main:app --host 0.0.0.0 --port 8000.

Update README.md with deployment steps:
- Backend on Railway/Render from /backend, set GEMINI_API_KEY (and ALLOWED_ORIGINS with the
  Vercel domain).
- Frontend on Vercel from /frontend, set NEXT_PUBLIC_API_URL to the backend URL.
- Reminder to add the deployed Vercel origin to backend CORS.

Do a final pass: ensure no secrets are committed, .env.example files exist, and pytest passes.
```

**Verify**
- `docker build -t fashion-be backend/` then `docker run -p 8000:8000 -e GEMINI_API_KEY=... fashion-be` and `curl localhost:8000/api/health`.

---

## Post-build checklist (from the plan's Definition of Done)

- [ ] `pytest` green; tool coverage ≥ 80%; chaos scenarios handled (timeouts, 403/404,
      malformed JSON, empty results, all-stores-fail).
- [ ] Fetches run concurrently; no `run_until_complete` inside the event loop.
- [ ] Ranker JSON parsing falls back gracefully.
- [ ] `filtered_products` capped at 30 before Ranker.
- [ ] CORS allowlist set; no secrets in git; `.env.example` present.
- [ ] Backend + frontend deployed; live text + visual search verified end-to-end.

## Tips for steering the agent

- If the agent strays from the contracts, paste the relevant §5 block and say "match this
  exactly."
- For flaky LLM behavior, tell it to "make the graph logic independent of tool-call order;
  rely on state, not on the model following the happy path."
- When tests need Gemini, instruct: "mock genai.GenerativeModel; do not call the live API in
  unit tests. Gate any live test behind RUN_LIVE_LLM_TESTS=1."
- Commit after each prompt with a message like `feat(P3): deterministic agent tools + tests`.
