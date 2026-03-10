from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.graph.message import MessagesState, add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.config import settings
from app.services.graph_queries import (
    find_events_by_name,
    find_themes_by_name,
    get_active_themes,
    get_articles_by_company,
    get_articles_by_event,
    get_articles_by_theme,
    get_existing_context_nodes,
    get_recent_events,
)

logger = logging.getLogger("ai_agents")


class AgentState(MessagesState):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_articles(articles: list[dict]) -> list[dict]:
    """Normalize datetime fields so the list is JSON-serializable."""
    out = []
    for a in articles:
        row: dict[str, Any] = {}
        for k, v in a.items():
            row[k] = str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@tool
async def query_company_news(ticker: str, limit: int = 10) -> str:
    """Fetch recent news articles mentioning a specific company ticker (e.g. NVDA, AAPL)."""
    try:
        articles = await get_articles_by_company(ticker.upper(), limit=limit)
        if not articles:
            return json.dumps({"found": False, "ticker": ticker, "articles": []})
        return json.dumps({"found": True, "ticker": ticker, "articles": _format_articles(articles)})
    except Exception as exc:
        logger.exception("query_company_news failed")
        return json.dumps({"error": str(exc)})


@tool
async def query_event_news(event_name: str, limit: int = 10) -> str:
    """Fetch news articles about a named event (e.g. 'Fed rate decision', 'CPI report')."""
    try:
        events = await find_events_by_name(event_name, limit=5)
        if not events:
            return json.dumps({"found": False, "event_name": event_name, "articles": []})
        # Use the best match (first result)
        event_id = events[0]["id"]
        event_title = events[0]["title"]
        articles = await get_articles_by_event(event_id, limit=limit)
        return json.dumps({
            "found": True,
            "event_name": event_title,
            "matched_events": events,
            "articles": _format_articles(articles),
        })
    except Exception as exc:
        logger.exception("query_event_news failed")
        return json.dumps({"error": str(exc)})


@tool
async def query_theme_news(theme_name: str, limit: int = 10) -> str:
    """Fetch news articles related to a macro theme (e.g. 'AI', 'Interest Rates', 'Energy Transition')."""
    try:
        themes = await find_themes_by_name(theme_name, limit=5)
        if not themes:
            return json.dumps({"found": False, "theme_name": theme_name, "articles": []})
        matched_name = themes[0]["name"]
        articles = await get_articles_by_theme(matched_name, limit=limit)
        return json.dumps({
            "found": True,
            "theme_name": matched_name,
            "matched_themes": themes,
            "articles": _format_articles(articles),
        })
    except Exception as exc:
        logger.exception("query_theme_news failed")
        return json.dumps({"error": str(exc)})


@tool
async def list_recent_events(days: int = 7, limit: int = 10) -> str:
    """List recent market events from the last N days. Use for discovery: 'what's happening?'"""
    try:
        events = await get_recent_events(days=days, limit=limit)
        if not events:
            return json.dumps({"found": False, "events": []})
        formatted = []
        for e in events:
            row: dict[str, Any] = {}
            for k, v in e.items():
                row[k] = str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
            formatted.append(row)
        return json.dumps({"found": True, "events": formatted})
    except Exception as exc:
        logger.exception("list_recent_events failed")
        return json.dumps({"error": str(exc)})


@tool
async def list_active_themes(limit: int = 10) -> str:
    """List the currently trending macro themes by article volume. Use for: 'what themes are trending?'"""
    try:
        themes = await get_active_themes(limit=limit)
        if not themes:
            return json.dumps({"found": False, "themes": []})
        formatted = []
        for t in themes:
            row: dict[str, Any] = {}
            for k, v in t.items():
                row[k] = str(v) if not isinstance(v, (str, int, float, bool, type(None), list)) else v
            formatted.append(row)
        return json.dumps({"found": True, "themes": formatted})
    except Exception as exc:
        logger.exception("list_active_themes failed")
        return json.dumps({"error": str(exc)})


TOOLS = [
    query_company_news,
    query_event_news,
    query_theme_news,
    list_recent_events,
    list_active_themes,
]

# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------


async def _build_system_prompt(state: AgentState) -> list:
    context = await get_existing_context_nodes(limit=30)
    theme_list = ", ".join(context["macro_themes"]) or "none indexed yet"
    event_list = ", ".join(context["events"]) or "none indexed yet"

    system_content = (
        "You are an AI financial assistant for a fintech dashboard powered by a Neo4j knowledge graph.\n\n"
        "You have access to tools that query indexed news articles, events, and macro themes.\n"
        "Always use tools to fetch real data before answering questions about specific companies, "
        "events, or themes.\n\n"
        f"Currently indexed macro themes: {theme_list}\n"
        f"Recent event titles: {event_list}\n\n"
        "When you find articles, cite them using this exact format at the end of relevant sentences:\n"
        "[Source: Article Title (https://url)]\n\n"
        "If no data is found (found=false or empty arrays), clearly say so and offer general knowledge "
        "as a fallback. Do not fabricate citations or URLs."
    )

    return [SystemMessage(content=system_content)] + list(state["messages"])


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_graph():
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.2,
    ).bind_tools(TOOLS)

    async def agent_node(state: AgentState) -> dict:
        prompt = await _build_system_prompt(state)
        response = await llm.ainvoke(prompt)
        return {"messages": [response]}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile()


compiled_graph = build_graph()
