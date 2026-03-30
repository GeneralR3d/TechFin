# TechFin — Know the World Before the Market Does

> **Real-time geopolitical intelligence meets personal portfolio management.**
> **Update: 1st place winner of the 2026 NTU Fintech Hackathon**

TechFin is an AI-powered personal finance dashboard that doesn't just track your stocks — it reads the world. By aggregating news across multiple sources, performing deep sentiment analysis, and mapping relationships between global events and financial sectors, TechFin gives retail investors the kind of macro-awareness that used to be reserved for institutional traders.

## Demo

Try it live at [tech-fin-xi.vercel.app](https://tech-fin-xi.vercel.app/) and log in with:

- Username: `demo`
- Password: `password`

### Demo Video

[![Demo Video](https://img.youtube.com/vi/Jn0XqxhPRJE/maxresdefault.jpg)](https://youtu.be/Jn0XqxhPRJE)


---

### The Problem

Most retail investors react to the market. TechFin helps you get ahead of it.

TechFin is world-event-focused. It identifies like most mentioned geopolitical world events, mergers and acquisitions, as well as government macro-policy announcements to find the the most up to date investor sentiments related to the affected sectors, and quickly makes investment suggestions.

### What Makes TechFin Different

At its core, TechFin uses a **custom knowledge graph** (powered by Neo4j) to model the relationships between news articles, world events, sectors, and tickers. This enables intelligent graph traversals that surface the most contextually relevant insights for each event — not just the loudest headlines, but the most *connected* ones.

On top of that graph sits a **LangGraph multi-agent AI chatbot** that can answer natural-language questions about your portfolio, current market themes, and recent events by querying the knowledge graph in real time. Ask it "What's happening with NVDA?" and it pulls live, structured data — not hallucinations.

---

![Neo4J graph](neo4j.png)

---

### Core Features


| Feature                       | Description                                                                                  |
| ----------------------------- | -------------------------------------------------------------------------------------------- |
| **Event Intelligence**        | Detects top geopolitical events, M&A, and macro-policy shifts in real time                   |
| **Sentiment Grid**            | Sector-by-sector sentiment heatmap updated daily                                             |
| **Graph-Powered Matching**    | Neo4j graph traversals match news to the most affected sectors and tickers                   |
| **AI Chatbot**                | LangGraph multi-agent assistant that queries your knowledge graph to answer market questions |
| **Portfolio Recommendations** | LLM-powered stock suggestions tuned to your holdings                                         |
| **Multi-Source Aggregation**  | Yahoo Finance, Reddit, Twitter, LinkedIn — all in one feed                                   |
| **Social Pulse**              | Community sentiment from Reddit and social platforms per ticker                              |


---

## Tech Stack

**Frontend** — React 19 · Vite 6 · TypeScript · Tailwind CSS 4 · shadcn/ui · SWR

**Backend** — FastAPI · SQLAlchemy 2 (async) · PostgreSQL · Alembic

**Intelligence Layer** — Neo4j (graph traversal) · LangGraph + LangChain · OpenAI gpt-4o-mini · RapidAPI (Yahoo Finance) · Reddit OAuth · APScheduler (hourly ingestion)

---

## Team


| Builder       | Handle                                     |
| ------------- | ------------------------------------------ |
| Tuan Ding Ren | [@General3d](https://github.com/General3d) |
| Jayce Goh     | [@JyG12](https://github.com/JyG12)         |
| Boxuan        | [@boxuan-yu](https://github.com/boxuan-yu) |
| Shianne       | [@zikyuu](https://github.com/zikyuu)       |
| Jden Goh      | [@jdengoh](https://github.com/jdengoh)     |


---

## Getting Started

### Prerequisites

- Node.js ≥ 18
- Python ≥ 3.12 + [uv](https://docs.astral.sh/uv/)
- Docker (for PostgreSQL + Neo4j)

### Infrastructure

```bash
docker compose -f docker-compose.infra.yaml up -d
```

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

Or run everything at once: `make dev`

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/techfin
SECRET_KEY=change-me-in-production
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
OPENAI_API_KEY=your_openai_key
```

> `OPENAI_API_KEY` is required for the AI chatbot and graph entity extraction.

---

## Demo

Try it live at [tech-fin-xi.vercel.app](https://tech-fin-xi.vercel.app/) or run locally and log in with:

- **Username:** `demo`
- **Password:** `password`

