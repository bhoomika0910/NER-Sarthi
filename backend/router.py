"""Terrain-aware routing utilities for the NER-SARTHI road network."""

from typing import Any

import networkx as nx


BLOCKED_EDGE_WEIGHT = 10_000.0


def _distance_weight(_: Any, __: Any, edge_data: dict[str, Any]) -> float:
    """Return the standard distance-only cost for an edge."""
    return float(edge_data["distance_km"])


def _risk_weight(
    _: Any,
    __: Any,
    edge_data: dict[str, Any],
    hazard_penalty_multiplier: float,
) -> float:
    """Return a distance cost that penalizes high-risk segments."""
    if edge_data.get("status") == "BLOCKED_OR_CRITICAL":
        return BLOCKED_EDGE_WEIGHT

    distance_km = float(edge_data["distance_km"])
    risk_score = min(max(float(edge_data.get("risk_score", 0.0)), 0.0), 1.0)
    return distance_km * (
        1 + hazard_penalty_multiplier * (risk_score**2)
    )


def _edge_data(graph: nx.Graph, first_node: Any, second_node: Any) -> dict[str, Any]:
    """Return edge data while keeping route calculations focused on Graphs."""
    return graph[first_node][second_node]


def _route_summary(
    graph: nx.Graph,
    path: list[Any],
    segments_bypassed_due_to_hazard: int = 0,
) -> dict[str, Any]:
    """Build the public route response from a node path."""
    coordinates = [
        [float(graph.nodes[node]["latitude"]), float(graph.nodes[node]["longitude"])]
        for node in path
    ]
    distances: list[float] = []
    travel_time_hours = 0.0
    risk_distance = 0.0

    for first_node, second_node in zip(path, path[1:]):
        edge_data = _edge_data(graph, first_node, second_node)
        distance_km = float(edge_data["distance_km"])
        speed_kmh = float(edge_data["default_speed_kmh"])
        if speed_kmh <= 0:
            raise ValueError(
                f"Edge {first_node!r}-{second_node!r} has a non-positive speed"
            )
        distances.append(distance_km)
        travel_time_hours += distance_km / speed_kmh
        risk_distance += distance_km * float(edge_data.get("risk_score", 0.0))

    total_distance_km = sum(distances)
    average_route_risk = (
        risk_distance / total_distance_km if total_distance_km else 0.0
    )
    return {
        "coordinates": coordinates,
        "total_distance_km": total_distance_km,
        "estimated_travel_time_hours": travel_time_hours,
        "average_route_risk": average_route_risk,
        "segments_bypassed_due_to_hazard": segments_bypassed_due_to_hazard,
    }


def get_standard_route(
    graph: nx.Graph, origin_id: Any, destination_id: Any
) -> dict[str, Any]:
    """Return the shortest route using distance only."""
    path = nx.shortest_path(
        graph,
        origin_id,
        destination_id,
        weight=_distance_weight,
        method="dijkstra",
    )
    return _route_summary(graph, path)


def get_safe_resilient_route(
    graph: nx.Graph,
    origin_id: Any,
    destination_id: Any,
    risk_tolerance: float = 1.5,
) -> dict[str, Any]:
    """Return a route minimizing distance plus squared hazard risk.

    Critical or blocked edges receive a massive cost so Dijkstra selects an
    available bypass whenever one exists.
    """
    if risk_tolerance < 0:
        raise ValueError("risk_tolerance must be non-negative")

    standard_path = nx.shortest_path(
        graph,
        origin_id,
        destination_id,
        weight=_distance_weight,
        method="dijkstra",
    )
    safe_path = nx.shortest_path(
        graph,
        origin_id,
        destination_id,
        weight=lambda first, second, data: _risk_weight(
            first, second, data, risk_tolerance
        ),
        method="dijkstra",
    )
    bypassed_count = sum(
        1
        for first_node, second_node in zip(standard_path, standard_path[1:])
        if _edge_data(graph, first_node, second_node).get("status")
        == "BLOCKED_OR_CRITICAL"
        and {first_node, second_node}
        not in (
            {safe_first, safe_second}
            for safe_first, safe_second in zip(safe_path, safe_path[1:])
        )
    )
    return _route_summary(graph, safe_path, bypassed_count)


def test_router() -> None:
    """Verify standard routing, risk detours, and response fields."""
    graph = nx.Graph()
    for node, latitude in (("A", 27.0), ("B", 27.1), ("C", 27.2)):
        graph.add_node(node, latitude=latitude, longitude=88.5)
    graph.add_edge("A", "B", distance_km=10, default_speed_kmh=40, risk_score=0.9,
                   status="BLOCKED_OR_CRITICAL")
    graph.add_edge("B", "C", distance_km=10, default_speed_kmh=40, risk_score=0.9,
                   status="BLOCKED_OR_CRITICAL")
    graph.add_edge("A", "C", distance_km=30, default_speed_kmh=30, risk_score=0.0,
                   status="OPEN")

    standard = get_standard_route(graph, "A", "C")
    resilient = get_safe_resilient_route(graph, "A", "C")
    assert standard["total_distance_km"] == 20
    assert resilient["total_distance_km"] == 30
    assert resilient["segments_bypassed_due_to_hazard"] == 2
    assert 0.0 <= resilient["average_route_risk"] <= 1.0


if __name__ == "__main__":
    test_router()
    print("NER-SARTHI router check passed")
