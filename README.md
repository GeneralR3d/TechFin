# TechFin — Know the World Before the Market Does

> **Real-time geopolitical intelligence meets personal portfolio management.**

TechFin is an AI-powered personal finance dashboard that doesn't just track your stocks — it reads the world. By aggregating news across multiple sources, performing deep sentiment analysis, and mapping relationships between global events and financial sectors, TechFin gives retail investors the kind of macro-awareness that used to be reserved for institutional traders.

### The Problem

TechFin is world-event-focused. It identifies like most mentioned geopolitical world events, mergers and acquisitions, as well as government macro-policy announcements to find the the most up to date investor sentiments related to the affected sectors, and quickly makes investment suggestions.


### What Makes TechFin Different



At its core, TechFin uses a **custom graph structure** (powered by Neo4j) to model the relationships between news articles, world events, sectors, and tickers. This enables intelligent graph traversals that surface the most contextually relevant insights for each event — not just the loudest headlines, but the most connected ones.

---

<!-- INSERT NEO4J GRAPH VISUALIZATION HERE -->
<!-- Suggested: screenshot or export of the TechFin knowledge graph showing nodes (events, sectors, tickers) and their relationships -->
![Neo4J graph](neo4j.png)

---

### Core Features

| Feature | Description |
|---|---|
| **Event Intelligence** | Detects top geopolitical events, M&A, and macro-policy shifts in real time |
| **Sentiment Grid** | Sector-by-sector sentiment heatmap updated daily |
| **Graph-Powered Matching** | Neo4j graph traversals match news to the most affected sectors and tickers |
| **Portfolio Recommendations** | Investment suggestions derived from current sentiment, tuned to your holdings |
| **Multi-Source Aggregation** | Yahoo Finance, Reddit, Twitter, LinkedIn — all in one feed |
| **Social Pulse** | Community sentiment from Reddit and social platforms per ticker |

---

## Tech Stack

**Frontend** — React 19 · Vite 6 · TypeScript · Tailwind CSS 4 · shadcn/ui · SWR

**Backend** — FastAPI · SQLAlchemy 2 (async) · PostgreSQL · Alembic

**Intelligence Layer** — Neo4j (graph traversal) · Custom sentiment pipeline · RapidAPI (Yahoo Finance) · Reddit OAuth

---

## Team

| Builder | Handle |
|---|---|
| Tuan Ding Ren | [@General3d](https://github.com/General3d) |
| Jayce Goh | [@JyG12](https://github.com/JyG12) |
| Boxuan | [@boxuan-yu](https://github.com/boxuan-yu) |
| Shianne | [@zikyuu](https://github.com/zikyuu) |
| Jden Goh | [@jdengoh](https://github.com/jdengoh) |

---

## Getting Started

### Prerequisites

- Node.js ≥ 18
- Python ≥ 3.12 + [uv](https://docs.astral.sh/uv/)
- PostgreSQL running locally with a database named `techfin`

### Backend

```bash
cd backend
uv sync
cp .env.example .env        # edit DATABASE_URL and API keys as needed
uv run alembic upgrade head
uv run python scripts/seed.py
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                 # dev server on localhost:5173
```

The Vite dev server proxies all `/api/*` requests to the FastAPI backend on `:8000`.

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/techfin
SECRET_KEY=change-me-in-production
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_YAHOO_FINANCE_HOST=yahoo-finance15.p.rapidapi.com
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=TechFin/1.0 by YourRedditUsername
```

> API keys are optional — the app falls back to mock data if they are missing.

---

## Demo

After seeding, log in with:

- **Username:** `demo`
- **Password:** `password`
