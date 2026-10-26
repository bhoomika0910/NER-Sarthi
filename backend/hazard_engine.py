"""Dynamic landslide-risk calculations for the NER-SARTHI road network."""

from math import exp, radians, sin, cos, sqrt, atan2
from typing import Any

import networkx as nx


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    """Keep a numeric value within an inclusive range."""
    return max(lower, min(value, upper))


def calculate_segment_risk(
    rainfall_mm_24h: float,
    slope_angle: float,
    historical_freq: float,
    soil_saturation: float = 0.5,
) -> float:
    """Calculate a normalized landslide vulnerability score for a road segment.

    The interaction term increases exponentially when both rainfall exceeds
    70 mm in 24 hours and the slope exceeds 35 degrees. Inputs representing
    normalized frequencies and saturation are constrained to [0.0, 1.0].
    """
    if rainfall_mm_24h < 0:
        raise ValueError("rainfall_mm_24h must be non-negative")
    if not 0 <= historical_freq <= 1:
        raise ValueError("historical_freq must be between 0.0 and 1.0")
    if not 0 <= soil_saturation <= 1:
        raise ValueError("soil_saturation must be between 0.0 and 1.0")

    rainfall_factor = 1 - exp(-rainfall_mm_24h / 70)
    slope_factor = _clamp(max(slope_angle, 0.0) / 55)
    excess_rainfall = max(rainfall_mm_24h - 70, 0.0) / 70
    excess_slope = max(slope_angle - 35, 0.0) / 20
    extreme_weather_interaction = exp(excess_rainfall * excess_slope) - 1

    hazard_pressure = (
        1.4 * rainfall_factor
        + 0.8 * slope_factor
        + 1.2 * historical_freq
        + 0.8 * soil_saturation
        + 2.5 * extreme_weather_interaction
    )
    return _clamp(1 - exp(-hazard_pressure))


def _haversine_distance_km(
    first_coords: tuple[float, float], second_coords: tuple[float, float]
) -> float:
    """Return the great-circle distance between (latitude, longitude) pairs."""
    earth_radius_km = 6371.0
    first_lat, first_lon = map(radians, first_coords)
    second_lat, second_lon = map(radians, second_coords)
    delta_lat = second_lat - first_lat
    delta_lon = second_lon - first_lon
    haversine = (
        sin(delta_lat / 2) ** 2
        + cos(first_lat) * cos(second_lat) * sin(delta_lon / 2) ** 2
    )
    return 2 * earth_radius_km * atan2(sqrt(haversine), sqrt(1 - haversine))


def _edge_midpoint(graph: nx.Graph, first_node: Any, second_node: Any) -> tuple[float, float]:
    """Return the geographic midpoint of an edge's endpoint coordinates."""
    first = graph.nodes[first_node]
    second = graph.nodes[second_node]
    return (
        (first["latitude"] + second["latitude"]) / 2,
        (first["longitude"] + second["longitude"]) / 2,
    )


def simulate_weather_impact(
    graph: nx.Graph,
    affected_zone_center_coords: tuple[float, float],
    radius_km: float,
    rainfall_mm: float,
) -> nx.Graph:
    """Apply a rainfall event to graph edges within a geographic radius.

    The supplied graph is updated in place and returned for convenient
    composition with routing workflows.
    """
    if radius_km < 0:
        raise ValueError("radius_km must be non-negative")
    if rainfall_mm < 0:
        raise ValueError("rainfall_mm must be non-negative")

    for first_node, second_node, edge_data in graph.edges(data=True):
        midpoint = _edge_midpoint(graph, first_node, second_node)
        distance_from_zone = _haversine_distance_km(
            affected_zone_center_coords, midpoint
        )
        current_rainfall = rainfall_mm if distance_from_zone <= radius_km else 0.0
        edge_data["current_rainfall_mm"] = current_rainfall
        edge_data["risk_score"] = calculate_segment_risk(
            rainfall_mm_24h=current_rainfall,
            slope_angle=edge_data["base_slope_angle"],
            historical_freq=edge_data["historical_landslide_frequency"],
        )
        edge_data["status"] = (
            "BLOCKED_OR_CRITICAL"
            if edge_data["risk_score"] > 0.75
            else "OPEN"
        )

    return graph


def test_hazard_engine() -> None:
    """Verify risk bounds and dynamic graph attributes."""
    safe_risk = calculate_segment_risk(0, 20, 0)
    extreme_risk = calculate_segment_risk(150, 55, 0.8, 0.9)
    assert 0.0 <= safe_risk <= 1.0
    assert 0.0 <= extreme_risk <= 1.0
    assert extreme_risk > safe_risk

    graph = nx.Graph()
    graph.add_node("A", latitude=27.0, longitude=88.5)
    graph.add_node("B", latitude=27.01, longitude=88.5)
    graph.add_edge(
        "A",
        "B",
        base_slope_angle=45.0,
        historical_landslide_frequency=0.5,
    )
    simulate_weather_impact(graph, (27.005, 88.5), 10, 100)
    edge_data = graph["A"]["B"]
    assert 0.0 <= edge_data["risk_score"] <= 1.0
    assert edge_data["current_rainfall_mm"] == 100
    assert edge_data["status"] == "BLOCKED_OR_CRITICAL"


if __name__ == "__main__":
    test_hazard_engine()
    print("NER-SARTHI hazard engine check passed")
