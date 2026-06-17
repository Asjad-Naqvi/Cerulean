# Pakistani Live Fashion Aggregator — Detailed Implementation Plan

> A live, database-free, multi-agent fashion search engine for Pakistani clothing
> brands. A three-agent LangGraph pipeline (Planner → Retrieval → Ranker) powered by
> Gemini 2.5 Flash reasons about user intent, selects relevant stores, fetches live
> product data, and re-ranks results by semantic relevance.

This document is the **engineering source of truth**. It expands the original concept
plan into concrete, sequenced, verifiable work. Companion file
[`AGENT_PROMPTS.md`](./AGENT_PROMPTS.md) contains copy-paste prompts for an AI coding
agent to execute each task here.

---

## Table of Contents

1. [Goals, Non-Goals & Success Criteria](#1-goals-non-goals--success-criteria)
2. [Architecture Overview](#2-architecture-overview)
3. [Tech Stack & Versions](#3-tech-stack--versions)
4. [Repository Layout](#4-repository-layout)
5. [Data Contracts (Pydantic + TypeScript)](#5-data-contracts-pydantic--typescript)
6. [Implementation Milestones](#6-implementation-milestones)
   - [M0 — Repo & Tooling Bootstrap](#m0--repo--tooling-bootstrap)
   - [M1 — Store Verification & Config Layer](#m1--store-verification--config-layer)
   - [M2 — Agent Tools (Deterministic Services)](#m2--agent-tools-deterministic-services)
   - [M3 — Agent Nodes & LangGraph Assembly](#m3--agent-nodes--langgraph-assembly)
   - [M4 — FastAPI Integration Layer](#m4--fastapi-integration-layer)
   - [M5 — Next.js Frontend](#m5--nextjs-frontend)
   - [M6 — Testing & Hardening](#m6--testing--hardening)
   - [M7 — Deployment](#m7--deployment)
7. [Testing Strategy](#7-testing-strategy)
8. [Error Handling Matrix](#8-error-handling-matrix)
9. [Performance & Cost Budget](#9-performance--cost-budget)
10. [Security & Compliance](#10-security--compliance)
11. [Environment Variables](#11-environment-variables)
12. [Risks, Constraints & Open Questions](#12-risks-constraints--open-questions)
13. [Definition of Done](#13-definition-of-done)
14. [Appendix A — Suggested Store Registry](#appendix-a--suggested-store-registry)

---

## 1. Goals, Non-Goals & Success Criteria

### Goals
- Aggregate **live** product data from 15–25 Pakistani fashion stores with **no database**.
- Genuine agentic behavior: dynamic store selection, iterative retrieval, semantic re-ranking.
- Support **text search**, **visual search** (image upload), and optional **body measurements**.
- Sub-8-second p95 latency for a typical query.
- Deploy backend (FastAPI) and frontend (Next.js) to managed hosting.

### Non-Goals (v1)
- User accounts, auth, persistent history, or carts.
- Checkout / payments (we deep-link to each store's product page).
- Price-drop alerts, wishlists, or notifications.
- Caching layer (noted as a future improvement, not built in v1).
- Mobile native apps (responsive web only).

### Success Criteria
| Metric | Target |
|---|---|
| Stores integrated & verified `active:true` | ≥ 12 |
| Text search returns ≥ 5 relevant results for common queries | ≥ 80% of test queries |
| Visual search returns plausible matches | qualitative pass on 10 sample images |
| p95 end-to-end latency | ≤ 8s |
| Backend unit test coverage on tools | ≥ 80% |
| Graceful degradation when stores time out | 0 unhandled 500s in chaos test |

---

## 2. Architecture Overview

```
User Input (text or image + optional measurements)
        │
        ▼
┌──────────────────┐
│  PLANNER AGENT   │  Reasons about intent, selects target stores
│  (Gemini + tools)│  Tools: parse_text_query, parse_image_query, select_target_stores
└────────┬─────────┘
         │ parsed_query + target_store_slugs + search_hint
         ▼
┌──────────────────┐ ◄──────────────────────────┐
│ RETRIEVAL AGENT  │  Fetches, filters, maps sizes│ loop if sparse
│  (Gemini + tools)│  Tools: fetch_store, filter, │ (max 2 retries)
│                  │  map_sizes, broaden          ├──────────────────────────┘
└────────┬─────────┘
         │ filtered_products
         ▼
┌──────────────────┐
│  RANKER AGENT    │  Re-ranks by relevance, writes search summary
│  (Gemini, no     │
│   tools)         │
└────────┬─────────┘
         │ ranked_products + search_summary
         ▼
     FastAPI response → Next.js frontend
```

**Why agentic (vs. a deterministic script):**

| Behavior | Mechanism |
|---|---|
| Dynamic store selection | Planner reasons over store metadata instead of blasting all stores |
| Iterative retrieval | Retrieval agent evaluates result quality and broadens criteria on sparse results |
| Semantic re-ranking | Ranker uses LLM reasoning, not just price/keyword sort |
| Tool-use loops | Each agent calls tools in a Gemini function-calling loop |

The single source of truth across nodes is an `AgentState` `TypedDict` managed by LangGraph.

---

## 3. Tech Stack & Versions

| Layer | Technology | Notes |
|---|---|---|
| Frontend | Next.js 14 (App Router, `--src-dir`) + TypeScript | Vercel-native |
| Styling | Tailwind CSS | Utility-first |
| Backend | FastAPI on Python 3.11+ | Async-native |
| Orchestration | LangGraph `>=0.2.0` | Typed multi-agent state graph |
| LLM | Gemini 2.5 Flash (function calling, multimodal) | via `google-generativeai` |
| LLM bridge | `langchain-google-genai >=1.0.0` | Optional if calling SDK directly |
| HTTP client | `httpx` (async) | Connection pooling, per-store timeouts |
| Validation | Pydantic v2 | State, contracts, tool schemas |
| Tests | `pytest`, `pytest-asyncio`, `respx` (httpx mocking) | Backend |
| FE tests | Vitest + React Testing Library (optional v1) | Frontend |
| Deploy (FE) | Vercel | Zero-config |
| Deploy (BE) | Railway or Render | Docker-based |

`backend/requirements.txt` (pin exact versions after first `pip freeze`):

```
fastapi
uvicorn[standard]
httpx
pydantic>=2
google-generativeai
python-multipart
langgraph>=0.2.0
langchain-google-genai>=1.0.0
# dev
pytest
pytest-asyncio
respx
```

> **Decision:** The original plan mixes raw `google.generativeai` SDK calls inside
> LangGraph nodes. We keep that approach (direct SDK) because it gives precise control
> over the Gemini tool-calling loop. `langchain-google-genai` is listed for optional use
> but the reference implementation uses the native SDK.

---

## 4. Repository Layout

```
fashion-aggregator/                 (this repo)
├── backend/
│   ├── main.py                     # FastAPI entry point + CORS
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── state.py                # AgentState TypedDict
│   │   ├── planner_agent.py        # Planner node
│   │   ├── retrieval_agent.py      # Retrieval node (+ loop constants)
│   │   ├── ranker_agent.py         # Ranker node
│   │   └── graph.py                # Graph assembly & compile
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── query_tools.py          # parse_text_query_fn, parse_image_query_fn
│   │   ├── store_tools.py          # select_target_stores_fn
│   │   ├── fetch_tools.py          # fetch_store_fn + normalizers
│   │   ├── filter_tools.py         # filter_products_fn
│   │   └── size_tools.py           # map_product_sizes_fn, broaden_search_criteria_fn
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   └── search.py               # POST /api/search/text & /visual, GET /api/health
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # Pydantic request/response models
│   │
│   ├── config/
│   │   ├── stores.json             # Store registry with metadata
│   │   └── size_charts.json        # Per-brand size charts (inches)
│   │
│   ├── scripts/
│   │   └── verify_stores.py        # One-off endpoint probe (Shopify/Woo)
│   │
│   └── tests/
│       ├── test_store_tools.py
│       ├── test_fetch_tools.py
│       ├── test_filter_tools.py
│       ├── test_size_tools.py
│       └── test_graph_smoke.py
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── VisualUpload.tsx
│   │   │   ├── MeasurementPanel.tsx
│   │   │   ├── ResultsGrid.tsx
│   │   │   ├── ProductCard.tsx
│   │   │   ├── StoreStatusBar.tsx
│   │   │   └── AgentStatusBadge.tsx
│   │   └── lib/
│   │       ├── api.ts
│   │       └── types.ts
│   ├── .env.local.example
│   └── package.json
│
├── docs/
│   ├── IMPLEMENTATION_PLAN.md      # this file
│   └── AGENT_PROMPTS.md            # companion prompts
├── .gitignore
└── README.md
```

---

## 5. Data Contracts (Pydantic + TypeScript)

These contracts are the interface boundary. Define them **before** building tools so all
nodes agree on shapes.

### 5.1 `parsed_query` (Planner output)
```jsonc
{
  "item_type": "kurta",          // garment type, lowercase
  "color": "mustard",            // optional
  "material": "linen",           // optional
  "gender": "women",             // men | women | unisex | any
  "price_tier": "mid",           // budget | mid | premium | luxury | any
  "style_category": "eastern",   // optional free text
  "min_price": null,             // PKR, optional
  "max_price": 3000,             // PKR, optional
  "generic_size": null,          // XS..XXL, optional
  "occasion": "casual"           // optional
}
```

### 5.2 `Product` (normalized + ranked)
```jsonc
{
  "id": "sapphirepk_12345",
  "store_name": "Sapphire",
  "store_slug": "sapphirepk",
  "title": "Mustard Linen Kurta",
  "price": 2800.0,
  "compare_price": 3500.0,        // nullable (original/struck-through)
  "currency": "PKR",
  "available_sizes": ["S", "M", "L"],
  "matched_size": "M",            // nullable until size mapping runs
  "image_url": "https://...",
  "product_url": "https://sapphirepk.com/products/...",
  "tags": ["lawn", "summer"],
  "relevance_score": 0.94         // added by Ranker, nullable otherwise
}
```

### 5.3 API Response (`/api/search/*`)
```jsonc
{
  "results": [ /* Product[] */ ],
  "total_count": 12,
  "stores_queried": 8,
  "stores_responded": 7,
  "failed_stores": ["khaadi"],
  "query_parsed": { /* parsed_query */ },
  "search_summary": "Found 12 mustard lawn kurtas across 7 stores, ₨2,800–₨8,500.",
  "retrieval_iterations": 1
}
```

> Keep the Pydantic models in `models/schemas.py` and the mirrored TypeScript types in
> `frontend/src/lib/types.ts` in sync. Any field added on the backend must be reflected
> on the frontend.

---

## 6. Implementation Milestones

Each milestone lists **deliverables**, **acceptance criteria**, and **dependencies**.
Build in order; each milestone should leave the repo in a runnable/committable state.

### M0 — Repo & Tooling Bootstrap
**Deliverables**
- Monorepo with `backend/` and `frontend/` skeletons.
- Python venv + `requirements.txt`; Next.js app scaffolded with TS + Tailwind + `src/`.
- `.gitignore` (Python `.venv`, `__pycache__`, Node `node_modules`, `.next`, `.env*`).
- `backend/.env.example` and `frontend/.env.local.example`.
- Root `README.md` with run instructions.

**Acceptance**
- `uvicorn main:app --reload` boots an empty FastAPI app with `GET /api/health` → `{"status":"ok"}`.
- `npm run dev` boots the Next.js app.

**Depends on:** nothing.

### M1 — Store Verification & Config Layer
**Deliverables**
- `scripts/verify_stores.py` — probes each candidate domain's Shopify (`/products.json`)
  and WooCommerce (`/wp-json/wc/store/v1/products`) endpoints, logs HTTP status + sample
  payload shape, and emits a report.
- `config/stores.json` populated from the verification run; stores failing both adapters
  set to `"active": false`.
- `config/size_charts.json` with values from each brand's official size guide (start with
  3–5 brands, expand later).

**Acceptance**
- Verification script runs and produces a status table.
- `stores.json` validates against the store schema (slug, name, base_url, platform,
  products_endpoint, price_tier, gender, categories[], active).
- At least 12 stores marked `active:true`.

**Depends on:** M0. **Note:** requires outbound network access; document which stores were
reachable from the build environment vs. need re-verification from a Pakistani IP.

### M2 — Agent Tools (Deterministic Services)
Tools are pure Python utilities with **no LLM logic**. Build and unit-test them first so
the agents have a reliable substrate.

**Deliverables**
- `tools/query_tools.py` — `parse_text_query_fn`, `parse_image_query_fn` (schema anchors;
  Gemini fills structured args, function validates with Pydantic and returns them).
- `tools/store_tools.py` — `select_target_stores_fn` (gender + price-tier matching with a
  sane fallback to all active stores).
- `tools/fetch_tools.py` — `fetch_store_fn` (async httpx, per-store timeout, redirect
  follow) plus `_normalize_shopify` / `_normalize_woocommerce`.
- `tools/filter_tools.py` — `filter_products_fn` (price/item/color/material text match).
- `tools/size_tools.py` — `map_product_sizes_fn`, `_resolve_size`, `broaden_search_criteria_fn`.

**Acceptance**
- Each tool has unit tests (use `respx` to mock store HTTP responses).
- `filter_products_fn` and `map_product_sizes_fn` accept both JSON strings and native
  objects (the agents may pass either).
- `fetch_store_fn` never raises; failures return `{"success": false, ...}`.

**Depends on:** M1 (config files), M5.2 data contracts.

### M3 — Agent Nodes & LangGraph Assembly
**Deliverables**
- `agents/state.py` — `AgentState` TypedDict (see §5 and original plan §7.1).
- `agents/planner_agent.py` — Gemini tool-calling loop; sets `parsed_query`,
  `target_store_slugs`, `search_hint`, `retrieval_iterations=0`.
- `agents/retrieval_agent.py` — Gemini tool-calling loop; fetches all target stores,
  filters, maps sizes; increments `retrieval_iterations`; constants `MAX_ITERATIONS=2`,
  `SPARSE_THRESHOLD=5`.
- `agents/ranker_agent.py` — single Gemini call, strict JSON output, graceful empty-list
  handling.
- `agents/graph.py` — `StateGraph`, conditional edge `route_after_retrieval`, compiled
  `fashion_graph`.

**Critical correctness fixes over the concept plan**
- **Async tool dispatch inside the Retrieval node:** the concept uses
  `asyncio.get_event_loop().run_until_complete(...)`, which fails inside FastAPI's running
  loop. Instead make the node fully async and `await` fetches, or run blocking SDK calls in
  a thread (`asyncio.to_thread`) while awaiting `fetch_store_fn` directly. Fetch target
  stores concurrently with `asyncio.gather`.
- **Gemini SDK call style:** `model.generate_content` is sync; wrap with `asyncio.to_thread`
  in async nodes to avoid blocking the event loop.
- **Ranker JSON safety:** strip markdown fences if present; wrap `json.loads` in try/except
  and fall back to price-sorted `filtered_products`.

**Acceptance**
- `from agents.graph import fashion_graph` imports without error.
- A smoke test invokes the compiled graph with a mocked Gemini + mocked fetch and returns a
  well-formed final state.

**Depends on:** M2, valid `GEMINI_API_KEY` for live runs (mock for tests).

### M4 — FastAPI Integration Layer
**Deliverables**
- `models/schemas.py` — request/response Pydantic models matching §5.3.
- `routers/search.py` — `POST /api/search/text`, `POST /api/search/visual`,
  `GET /api/health`. Thin layer that builds the initial `AgentState` and calls
  `fashion_graph.ainvoke`.
- `main.py` — app, CORS (localhost + deployed FE origin), router include, global exception
  handler returning 503 on Gemini/network outage with a user-readable message.

**Acceptance**
- `POST /api/search/text` with `query=...` returns the §5.3 shape.
- `POST /api/search/visual` accepts a multipart image and optional `measurements_json`.
- Errors never leak stack traces to the client.

**Depends on:** M3.

### M5 — Next.js Frontend
**Deliverables**
- `lib/types.ts` — TS mirror of API contracts.
- `lib/api.ts` — `searchByText`, `searchByImage` using `NEXT_PUBLIC_API_URL`.
- Components: `SearchBar`, `VisualUpload` (jpeg/png/webp, reject >5MB client-side),
  `MeasurementPanel` (chest/waist/hips, session `useState`), `ResultsGrid` (skeleton
  loading), `ProductCard` (image, brand badge, price, size chips, "Shop Now →" deep link),
  `StoreStatusBar` ("Checked N stores · M responded · K failed"), `AgentStatusBadge`
  (shown when `retrieval_iterations > 1`).
- `page.tsx` wiring all components + `search_summary` line above the grid.

**Acceptance**
- Text and image searches render results against a running backend.
- Loading, empty, and error states are handled visually.
- Responsive grid; no layout shift on image load (use fixed aspect-ratio containers).

**Depends on:** M4 (or a mocked API for parallel work).

### M6 — Testing & Hardening
**Deliverables**
- Backend unit tests (M2) green; graph smoke test (M3) green.
- Chaos test: simulate store timeouts/403s and assert graceful degradation.
- Lint/format: `ruff`/`black` (backend), ESLint/Prettier (frontend).

**Acceptance**
- `pytest` passes; tool coverage ≥ 80%.
- No unhandled exceptions in the error-handling matrix scenarios (§8).

**Depends on:** M2–M5.

### M7 — Deployment
**Deliverables**
- `backend/Dockerfile` (python:3.11-slim, uvicorn on 8000).
- Railway/Render service from `/backend` with `GEMINI_API_KEY` set.
- Vercel project from `/frontend` with `NEXT_PUBLIC_API_URL` set.
- Update backend CORS allowlist with the deployed Vercel domain.

**Acceptance**
- Public backend `GET /api/health` returns ok.
- Deployed frontend performs a live search end-to-end.

**Depends on:** M6.

---

## 7. Testing Strategy

| Level | What | Tooling |
|---|---|---|
| Unit | Each tool function in isolation | `pytest`, `respx` for httpx mocks |
| Contract | Normalizers produce the §5.2 Product shape | `pytest` fixtures of real-ish payloads |
| Graph smoke | Compiled graph runs end-to-end with mocked Gemini + fetch | `pytest-asyncio` |
| API | Routers return §5.3 shape; error paths return 503/400 | FastAPI `TestClient` |
| Chaos | Store timeouts, 403/404, malformed JSON, empty results | mocked failures |
| Manual | Visual search quality on 10 sample images | human review |

**Mocking Gemini:** inject a fake model object (or patch `genai.GenerativeModel`) that
returns scripted `function_call` parts, so graph logic is testable without API cost or
network. Keep one optional **live** integration test gated behind an env flag
(`RUN_LIVE_LLM_TESTS=1`).

---

## 8. Error Handling Matrix

| Scenario | Behavior |
|---|---|
| Store times out (> `STORE_TIMEOUT`) | `fetch_store_fn` returns `{"success": false}`; agent records `failed_stores`, continues |
| Retrieval < `SPARSE_THRESHOLD` results | Agent calls `broaden_search_criteria` and retries (≤ `MAX_ITERATIONS`) |
| 0 results after retries | Ranker returns empty list + graceful summary |
| Tool returns malformed data | Tool dispatch wrapped in try/except; returns error-flagged empty result |
| Ranker returns invalid JSON | Fall back to price-sorted `filtered_products`, no scores |
| All stores fail | `results: []`, summary "No stores responded — please retry" |
| Image > 5MB | Rejected client-side before upload with inline error |
| Gemini API unavailable | Global handler returns 503 with user-readable message |
| Unknown store slug requested | `fetch_store_fn` returns `{"success": false, "error": "Unknown store slug"}` |

---

## 9. Performance & Cost Budget

- **Latency:** 3 sequential agent turns + concurrent store fetches. Target p95 ≤ 8s.
  Fetch all target stores **concurrently** (`asyncio.gather`) — do not await serially.
- **Store timeout:** start at `STORE_TIMEOUT = 2.5s`; benchmark real Pakistani CDNs and
  tune. Slow stores should fail fast rather than block the whole request.
- **Ranker token cost:** sending 50–100 products in one prompt is the most expensive step.
  **Cap `filtered_products` at 30 items** (price-sorted) before passing to the Ranker.
- **Planner tool calls:** typically 2–3 per query — within Gemini limits.
- **No caching in v1.** Future: cache `(parsed_query_hash → ranked_products)` in Redis
  with a short TTL (~60s).

---

## 10. Security & Compliance

- **Secrets:** never commit `GEMINI_API_KEY`. Use env vars / host secret stores; provide
  `.env.example` only.
- **CORS:** explicit allowlist (localhost + deployed FE), not `*`.
- **Outbound requests:** only to configured store domains from `stores.json`; do not fetch
  arbitrary URLs from user input.
- **Input validation:** validate/limit image size and MIME type; cap query length.
- **Scraping etiquette:** we use stores' public JSON endpoints (Shopify `/products.json`,
  WooCommerce Store API). Respect timeouts and reasonable request volume; set a descriptive
  `User-Agent`. Re-verify each store's ToS before production scale-up.
- **PII:** measurements are session-only on the frontend and never persisted server-side.

---

## 11. Environment Variables

### Backend
| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | yes | Google AI Studio key for Gemini 2.5 Flash |
| `STORE_TIMEOUT` | no | Per-store fetch timeout seconds (default 2.5) |
| `ALLOWED_ORIGINS` | no | Comma-separated CORS origins |
| `RUN_LIVE_LLM_TESTS` | no | `1` to enable live LLM integration tests |

### Frontend
| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | yes | Backend base URL, no trailing slash |

---

## 12. Risks, Constraints & Open Questions

**Must verify before launch**
- [ ] Run `verify_stores.py` on all candidate domains (Shopify vs WooCommerce vs custom).
- [ ] Populate all size-chart values from each brand's official guide.
- [ ] Confirm Shopify `/products.json` is publicly accessible per store.
- [ ] Confirm WooCommerce Store API v1 is enabled (WooCommerce Blocks 2.5+).
- [ ] Benchmark real store response times; tune `STORE_TIMEOUT`.

**Known risks**
- **Geo / bot blocking:** Pakistani stores may rate-limit or geo-block the build/host IP;
  some endpoints may need re-verification from a local IP or via a proxy.
- **Schema drift:** store payloads vary; normalizers must be defensive (missing variants,
  images, prices).
- **LLM nondeterminism:** agent tool-call order can vary; system prompts must be firm and
  graph logic must not assume a single happy path.
- **Async pitfall:** the concept plan's `run_until_complete` inside a running loop will
  break under FastAPI — see M3 correctness fixes.

**Open questions**
- Final store list & which are reachable from production hosting?
- Currency/price edge cases (variant-level pricing, sale vs. regular)?
- Do we localize UI (English vs. Urdu) in v1? (Assume English-only for v1.)

---

## 13. Definition of Done

- [ ] All milestones M0–M7 acceptance criteria met.
- [ ] `pytest` green; tool coverage ≥ 80%; chaos scenarios handled.
- [ ] Backend deployed; `GET /api/health` public and green.
- [ ] Frontend deployed; live text + visual search work end-to-end.
- [ ] `README.md` documents local setup, env vars, and deploy steps.
- [ ] No secrets in git history; `.env.example` files present.

---

## Appendix A — Suggested Store Registry

All stores **must be manually verified** before integration (see M1). Visit
`storename.pk/products.json` (Shopify) or
`storename.pk/wp-json/wc/store/v1/products` (WooCommerce) to confirm availability.

### Group A — Likely Shopify
| # | Brand | Domain | Price Tier | Category |
|---|---|---|---|---|
| 1 | Sapphire | sapphirepk.com | mid | women, pret + unstitched |
| 2 | Outfitters | outfitters.com.pk | mid | youth, western + eastern |
| 3 | Gul Ahmed | gulahmedshop.com | mid | women, lawn + pret |
| 4 | Alkaram Studio | alkaramstudio.com | mid | women, fabric + pret |
| 5 | Bonanza Satrangi | bonanzasatrangi.com | mid | women, unstitched + pret |
| 6 | Asim Jofa | asimjofa.com | premium | women, luxury pret |
| 7 | CrossStitch | cross-stitch.pk | mid | women, eastern |
| 8 | Limelight | limelight.pk | budget | women, pret |
| 9 | Zeen Woman | zeenwomanofficial.com | mid | women, formal pret |
| 10 | Kayseria | kayseria.com | budget | women, pret |
| 11 | Ego | pk.ego.com | mid | unisex, urban casual |
| 12 | Charcoal | charcoalpk.com | mid | men + women, smart casual |
| 13 | Sana Safinaz | sanasafinaz.com | premium | women, formal + lawn |
| 14 | Maria B | mariab.pk | premium | women, bridal + pret |
| 15 | Élan | elanofficial.com | luxury | women, occasionwear |
| 16 | Mushq | mushq.pk | mid | women, trendy pret |
| 17 | Zara Shahjahan | zarashahjahan.com | premium | women, signature prints |
| 18 | Baroque | baroquepk.com | premium | women, embroidered pret |
| 19 | Rang Jah | rangjah.pk | mid | women, artisanal eastern |
| 20 | Zubia Hassan | zubiahassan.com | premium | women, luxury pret |

### Group B — Likely WooCommerce
| # | Brand | Domain | Price Tier | Category |
|---|---|---|---|---|
| 1 | Generation | generation.com.pk | mid | women, ethical fashion |
| 2 | Khaadi | khaadi.com | mid | women, eastern + western |
| 3 | Nishat Linen | nishatlinen.com | mid | women, fabric + pret |

> **Pre-build verification:** before M4, run `verify_stores.py` to hit each domain's
> Shopify and WooCommerce endpoints and log status codes. Retire any store returning
> 403/404 from both adapters by setting `"active": false` in `stores.json`.
