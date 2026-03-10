from __future__ import annotations

from typing import Any, Iterable

from neo4j import GraphDatabase, Driver

from app.config import settings


_driver: Driver | None = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
        )
    return _driver


def run_cypher(query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """
    Execute a Cypher query and return a list of plain dict records.
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(query, parameters or {})
        records: Iterable[dict[str, Any]] = (r.data() for r in result)
        return list(records)


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None

