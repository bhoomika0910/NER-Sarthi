"""Synthetic road network for the Siliguri-Gangtok logistics corridor."""

import networkx as nx


def load_ner_road_graph() -> nx.Graph:
    """Build and return the NER-SARTHI road network graph.

    Coordinates are representative real-world waypoint locations. Distances,
    speeds, slopes, and landslide frequencies are synthetic planning values
    intended for development and simulation.
    """
    graph = nx.Graph()

    # Key waypoints along NH-10 and the Lava-Algarah alternative route.
    waypoints = {
        "Siliguri": {"latitude": 26.7271, "longitude": 88.3953},
        "Sevoke": {"latitude": 26.9024, "longitude": 88.4663},
        "Kalijhora": {"latitude": 27.0138, "longitude": 88.5638},
        "Teesta Bazaar": {"latitude": 27.0646, "longitude": 88.4952},
        "Rangpo": {"latitude": 27.1766, "longitude": 88.5339},
        "Singtam": {"latitude": 27.2347, "longitude": 88.5010},
        "Gangtok": {"latitude": 27.3389, "longitude": 88.6065},
        "Lava": {"latitude": 27.0928, "longitude": 88.6653},
        "Algarah": {"latitude": 27.1290, "longitude": 88.6328},
    }
    graph.add_nodes_from(waypoints.items())

    # Main NH-10 corridor and the mountainous Lava-Algarah bypass.
    road_segments = [
        (
            "Siliguri",
            "Sevoke",
            {
                "distance_km": 22.0,
                "default_speed_kmh": 45.0,
                "base_slope_angle": 20.0,
                "historical_landslide_frequency": 0.12,
                "name": "NH-10 Southern Approach",
            },
        ),
        (
            "Sevoke",
            "Kalijhora",
            {
                "distance_km": 18.5,
                "default_speed_kmh": 35.0,
                "base_slope_angle": 32.0,
                "historical_landslide_frequency": 0.38,
                "name": "NH-10 Riverside Corridor",
            },
        ),
        (
            "Kalijhora",
            "Teesta Bazaar",
            {
                "distance_km": 16.0,
                "default_speed_kmh": 30.0,
                "base_slope_angle": 40.0,
                "historical_landslide_frequency": 0.55,
                "name": "Teesta Gorge Section",
            },
        ),
        (
            "Teesta Bazaar",
            "Rangpo",
            {
                "distance_km": 25.0,
                "default_speed_kmh": 35.0,
                "base_slope_angle": 28.0,
                "historical_landslide_frequency": 0.31,
                "name": "NH-10 Teesta Crossing",
            },
        ),
        (
            "Rangpo",
            "Singtam",
            {
                "distance_km": 20.0,
                "default_speed_kmh": 30.0,
                "base_slope_angle": 36.0,
                "historical_landslide_frequency": 0.42,
                "name": "Rangpo-Singtam Mountain Road",
            },
        ),
        (
            "Singtam",
            "Gangtok",
            {
                "distance_km": 25.0,
                "default_speed_kmh": 28.0,
                "base_slope_angle": 45.0,
                "historical_landslide_frequency": 0.48,
                "name": "Singtam-Gangtok Ascent",
            },
        ),
        (
            "Teesta Bazaar",
            "Lava",
            {
                "distance_km": 33.0,
                "default_speed_kmh": 24.0,
                "base_slope_angle": 52.0,
                "historical_landslide_frequency": 0.44,
                "name": "Lava Mountain Pass",
            },
        ),
        (
            "Lava",
            "Algarah",
            {
                "distance_km": 16.0,
                "default_speed_kmh": 26.0,
                "base_slope_angle": 38.0,
                "historical_landslide_frequency": 0.27,
                "name": "Lava-Algarah Bypass",
            },
        ),
        (
            "Algarah",
            "Rangpo",
            {
                "distance_km": 31.0,
                "default_speed_kmh": 25.0,
                "base_slope_angle": 55.0,
                "historical_landslide_frequency": 0.36,
                "name": "Algarah-Rangpo Ridge Road",
            },
        ),
    ]
    graph.add_edges_from(road_segments)

    return graph


def test_ner_road_graph() -> None:
    """Verify that the synthetic network contains usable topology."""
    graph = load_ner_road_graph()
    assert graph.number_of_nodes() > 0
    assert graph.number_of_edges() > 0


if __name__ == "__main__":
    test_ner_road_graph()
    print("NER-SARTHI road graph check passed")
