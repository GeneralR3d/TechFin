from __future__ import annotations

from typing import Any, Dict, List, Literal, TypedDict
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.config import settings
from app.ai.neo4j_client import run_cypher


logger = logging.getLogger("ai_agents")


class AgentState(TypedDict):
    """Shared state for the LangGraph multi-agent workflow."""

    messages: List[Any]
    cypher_query: str | None
    query_result: List[Dict[str, Any]] | None


def _llm(system_prompt: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.2,
    ).bind(system_message=system_prompt)


def group_manager(state: AgentState) -> AgentState:
    """
    High-level planner. For now it always decides to:
    1) generate a Cypher query
    2) run the query
    3) answer using the results
    but it can be extended later.
    """
    messages = state["messages"]
    # Log latest user message for traceability
    user_message = next(
        (m for m in reversed(messages) if isinstance(m, HumanMessage)),
        None,
    )
    if user_message is not None:
        logger.info("group_manager: received user message: %s", user_message.content)
    else:
        logger.info("group_manager: no HumanMessage found in state")
    messages.append(
        AIMessage(
            content=(
                "I will analyze your request, generate a Neo4j Cypher query to fetch "
                "relevant data, run it, and then answer using the results."
            )
        )
    )
    return {**state, "messages": messages}


def neo4j_query_agent(state: AgentState) -> AgentState:
    """
    Generate a Cypher query based on the latest user request.
    """
    user_message = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        None,
    )
    if user_message is None:
        logger.warning("neo4j_query_agent: no HumanMessage found; skipping query generation")
        return state

    system = SystemMessage(
        content=(
            "You are a Cypher query generator for a Neo4j financial knowledge graph.\n"
            "The graph has nodes like User, Holding, and others. "
            "Return ONLY a Cypher query, nothing else.\n"
            "Do not include backticks or explanations. Use simple RETURN clauses.\n"
        )
    )
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0,
    )
    logger.info("neo4j_query_agent: generating Cypher for user message: %s", user_message.content)
    response = llm.invoke([system, user_message])
    cypher = response.content.strip()
    logger.info("neo4j_query_agent: generated Cypher: %s", cypher)
    return {**state, "cypher_query": cypher}


def neo4j_agent(state: AgentState) -> AgentState:
    """
    Execute the Cypher query and stash the results.
    """
    cypher = state.get("cypher_query")
    if not cypher:
        logger.warning("neo4j_agent: no Cypher query provided; skipping execution")
        return state
    try:
        logger.info("neo4j_agent: executing Cypher: %s", cypher)
        rows = run_cypher(cypher)
        logger.info("neo4j_agent: query returned %d row(s)", len(rows))
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("neo4j_agent: error while executing Cypher")
        rows = [{"error": str(exc), "cypher": cypher}]
    return {**state, "query_result": rows}


def answer_agent(state: AgentState) -> AgentState:
    """
    Use the Neo4j results plus the conversation to answer the user.
    """
    messages = list(state["messages"])
    rows = state.get("query_result") or []

    logger.info(
        "answer_agent: building answer with %d prior messages and %d Neo4j row(s)",
        len(messages),
        len(rows),
    )

    system = SystemMessage(
        content=(
            "You are an AI assistant for a fintech dashboard. "
            "You are given the user's question and JSON-like rows returned from a "
            "Neo4j database query. Use those rows as factual context. "
            "If the rows are empty, answer based on your general knowledge and say "
            "that no matching data was found in the graph."
        )
    )
    context_message = AIMessage(content=f"Neo4j rows:\n{rows!r}")

    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0.3,
    )
    response = llm.invoke([system, context_message, *messages])
    messages.append(response)
    return {**state, "messages": messages}


def build_graph():
    """
    Build and compile the LangGraph workflow once at import time.
    """
    graph = StateGraph(AgentState)

    graph.add_node("group_manager", group_manager)
    graph.add_node("neo4j_query_agent", neo4j_query_agent)
    graph.add_node("neo4j_agent", neo4j_agent)
    graph.add_node("answer_agent", answer_agent)

    graph.set_entry_point("group_manager")
    graph.add_edge("group_manager", "neo4j_query_agent")
    graph.add_edge("neo4j_query_agent", "neo4j_agent")
    graph.add_edge("neo4j_agent", "answer_agent")
    graph.add_edge("answer_agent", END)

    return graph.compile()


compiled_graph = build_graph()

