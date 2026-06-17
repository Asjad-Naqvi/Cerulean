# Cerulean - Pakistani Live Fashion Aggregator

Cerulean is a database-free, live multi-agent search engine for Pakistani clothing brands. It uses a three-agent LangGraph pipeline (**Planner** → **Retrieval** → **Ranker**) powered by Gemini 2.5 Flash to reason about user search intent, select relevant stores, fetch live product listings concurrently, filter and map custom sizing constraints, and re-rank the results semantically.

---

## 1. Repository Layout

```
├── backend/
│   ├── main.py                     # FastAPI entry point & exception middleware
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile                  # Container definition
│   ├── .env.example                # Template configuration
│   ├── config/                     # Configs (stores.json, size_charts.json)
│   ├── agents/                     # LangGraph nodes and orchestration
│   ├── tools/                      # Deterministic parsers & fetch filters
│   └── tests/                      # Pytest unit & integration suite
│
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js Pages & Layouts
│   │   ├── components/             # Reusable UI elements (SearchBar, Sizing drawer, grids)
│   │   └── lib/                    # API services & TS typings
│   ├── .env.local.example          # Template configuration
│   └── package.json                # Node script commands
```

---

## 2. Local Setup and Installation

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment template and fill in your Gemini API Key:
   ```bash
   cp .env.example .env
   ```
   *Modify `.env` and set `GEMINI_API_KEY=your-api-key-here`.*

5. Boot the API dev server:
   ```bash
   uvicorn main:app --reload
   ```
   The backend API will run at `http://localhost:8000`.

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Copy the environment template:
   ```bash
   cp .env.local.example .env.local
   ```
4. Run the Next.js dev server:
   ```bash
   npm run dev
   ```
   The frontend UI will run at `http://localhost:3000`.

---

## 3. Running Tests

We have implemented a thorough test suite. To run all backend tests:
```bash
cd backend
pytest tests/
```

This tests:
* Sizing mappings and store category filters.
* Live store fetchers (Shopify and WooCommerce Store APIs mocked via `respx`).
* Complete multi-agent state graph transitions using mocked Gemini message turns.
* Router endpoint behaviors, file limitations (max 5MB), and invalid inputs.

---

## 4. Deployment Instructions

### Backend Deployment (Docker)
We include a `Dockerfile` for the backend. You can deploy it to platforms like Railway, Render, or any cloud provider:
1. Set the following environment variables:
   * `GEMINI_API_KEY`: Your Google AI Studio API Key.
   * `STORE_TIMEOUT`: Per-store HTTP request timeout (defaults to `2.5` seconds).
   * `ALLOWED_ORIGINS`: Comma-separated list of origins allowed by CORS (e.g., your deployed frontend URL `https://your-app.vercel.app`).
2. Build the Docker image:
   ```bash
   docker build -t fashion-be backend/
   ```
3. Run the container:
   ```bash
   docker run -p 8000:8000 -e GEMINI_API_KEY=yourkey fashion-be
   ```

### Frontend Deployment
The frontend is a standard Next.js application designed to compile statically. You can deploy it directly to Vercel:
1. Link your repository.
2. Set the following Environment Variable in Vercel:
   * `NEXT_PUBLIC_API_URL`: The URL of your deployed backend (e.g. `https://your-backend.railway.app` without a trailing slash).
