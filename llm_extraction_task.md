# Task: Context-Aware LLM Extraction

## Background
Currently, the LLM extracts nodes strictly based on the provided title and content, combined with some deterministic Yahoo Finance categories. It does not look at the nodes already present in the Neo4j Graph Database. To have the LLM reference existing nodes first, we need we inject the known nodes into the system prompt.
This ensures the LLM reuses existing Strings for Entities and Themes instead of hallucinating slightly different variations (e.g., generating "Artificial Intelligence" when "AI Chip Boom" already exists).

---

## Proposed Changes

### 1. Update `app/services/graph_queries.py`
Add an async function `get_existing_context_nodes(limit: int = 30)` to fetch recent `MacroTheme` names and `Event` titles.
- **Cypher Query 1:** Fetch top Themes sorted by article count.
- **Cypher Query 2:** Fetch recent Events within the last 30 days.

### 2. Update `app/services/llm_extraction.py`
Modify `extract_entities(title: str, content: str)` to:
- Fetch `context_nodes = await get_existing_context_nodes()`.
- Dynamically build and inject an `EXISTING GRAPH DB NODES` section into the prompt before passing it to OpenAI.

**Prompt Addition Example:**
```text
Existing MacroThemes to reuse if applicable: [AI Chip Boom, US Rate Hikes 2022-2024, ...]
Existing Events to reuse if applicable: [SVB Bank Collapse, Apple Q1 2025 Earnings, ...]
```

### 3. Pipeline Verification (`scripts/run_ingestion.py`)
No code changes are needed here. `run_ingestion.py` fetches the RSS feed and calls `ingest_article_to_graph` internally, which relies on `extract_entities`. The ingestion pipeline will automatically benefit from this context-aware extraction the next time it runs by pulling existing nodes from the graph database prior to prompting the LLM.

---

## Action Items Checklist

- [ ] Add `get_existing_context_nodes()` to `app/services/graph_queries.py`.
- [ ] Add `context_nodes` fetching to `extract_entities()` in `app/services/llm_extraction.py`.
- [ ] Update `SYSTEM_PROMPT` inside `app/services/llm_extraction.py` to allow dynamic string interpolation.
- [ ] Test the pipeline by running `uv run python ../scripts/run_ingestion.py` locally and verifying the logged payload bounds.
