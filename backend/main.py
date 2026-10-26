"""NER-SARTHI FastAPI application entry point."""

from typing import Literal

import networkx as nx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.data.road_network import load_ner_road_graph
from backend.hazard_engine import simulate_weather_impact
from backend.router import get_safe_resilient_route, get_standard_route


Coordinates = list[float]


# Create the API application instance.
app = FastAPI(
    title="NER-SARTHI",
    description="Predictive terrain-aware logistics platform for India's North-Eastern Region.",
)


# Allow local frontend development servers to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Keep the active network in memory so hazard simulations and reports affect
# subsequent network and route requests during the running process.
road_graph = load_ner_road_graph()


class HealthResponse(BaseModel):
    """Health status returned by the service."""

    status: str
    project: str


class NetworkNode(BaseModel):
    """A waypoint exposed to the map frontend."""

    id: str
    coordinates: Coordinates


class NetworkEdge(BaseModel):
    """A road segment and its current operational state."""

    source: str
    target: str
    coordinates: list[Coordinates]
    distance_km: float
    default_speed_kmh: float
    name: str
    risk_score: float
    current_rainfall_mm: float
    status: str


class NetworkResponse(BaseModel):
    """Road network payload for map rendering."""

    nodes: list[NetworkNode]
    edges: list[NetworkEdge]


class RouteRequest(BaseModel):
    """Origin, destination, and routing strategy selected by the dispatcher."""

    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    mode: Literal["safe", "standard"] = "safe"


class RouteResponse(BaseModel):
    """Route summary consumed by the dispatch UI."""

    coordinates: list[Coordinates]
    total_distance_km: float
    estimated_travel_time_hours: float
    average_route_risk: float
    safety_score: float
    segments_bypassed_due_to_hazard: int


class HazardSimulationRequest(BaseModel):
    """Rainfall event applied to a geographic zone."""

    center_lat: float
    center_lng: float
    radius_km: float = Field(ge=0)
    rainfall_mm: float = Field(ge=0)


class HazardSimulationResponse(BaseModel):
    """Summary of a completed in-memory hazard simulation."""

    updated_segments: int
    critical_segments: int


class BlockageReportRequest(BaseModel):
    """Manual report for a known road segment."""

    segment_name: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class BlockageReportResponse(BaseModel):
    """Confirmation of a manually reported blockage."""

    segment_name: str
    reason: str
    status: str


# Basic service health endpoint for local development and monitoring.
@app.get("/api/health")
def health_check() -> HealthResponse:
    """Return the current API service status."""
    return HealthResponse(status="ok", project="NER-SARTHI")


@app.get("/api/network", response_model=NetworkResponse)
def get_network() -> NetworkResponse:
    """Return all waypoints and road segments with current hazard state."""
    nodes = [
        NetworkNode(
            id=str(node_id),
            coordinates=[
                float(node_data["latitude"]),
                float(node_data["longitude"]),
            ],
        )
        for node_id, node_data in road_graph.nodes(data=True)
    ]
    edges = [
        NetworkEdge(
            source=str(source),
            target=str(target),
            coordinates=[
                [
                    float(road_graph.nodes[source]["latitude"]),
                    float(road_graph.nodes[source]["longitude"]),
                ],
                [
                    float(road_graph.nodes[target]["latitude"]),
                    float(road_graph.nodes[target]["longitude"]),
                ],
            ],
            distance_km=float(edge_data["distance_km"]),
            default_speed_kmh=float(edge_data["default_speed_kmh"]),
            name=str(edge_data["name"]),
            risk_score=float(edge_data.get("risk_score", 0.0)),
            current_rainfall_mm=float(edge_data.get("current_rainfall_mm", 0.0)),
            status=str(edge_data.get("status", "OPEN")),
        )
        for source, target, edge_data in road_graph.edges(data=True)
    ]
    return NetworkResponse(nodes=nodes, edges=edges)


@app.post("/api/route", response_model=RouteResponse)
def calculate_route(request: RouteRequest) -> RouteResponse:
    """Calculate either a distance-optimal or risk-aware route."""
    if request.origin not in road_graph or request.destination not in road_graph:
        raise HTTPException(
            status_code=404,
            detail="Origin or destination waypoint was not found",
        )

    try:
        route = (
            get_safe_resilient_route(road_graph, request.origin, request.destination)
            if request.mode == "safe"
            else get_standard_route(road_graph, request.origin, request.destination)
        )
    except nx.NetworkXNoPath as error:
        raise HTTPException(
            status_code=409,
            detail="No route is available between the requested waypoints",
        ) from error

    return RouteResponse(
        **route,
        safety_score=1.0 - route["average_route_risk"],
    )


@app.post("/api/simulate-hazard", response_model=HazardSimulationResponse)
def simulate_hazard(request: HazardSimulationRequest) -> HazardSimulationResponse:
    """Apply a rainfall event to the shared in-memory road graph."""
    simulate_weather_impact(
        road_graph,
        (request.center_lat, request.center_lng),
        request.radius_km,
        request.rainfall_mm,
    )
    critical_segments = sum(
        edge_data.get("status") == "BLOCKED_OR_CRITICAL"
        for _, _, edge_data in road_graph.edges(data=True)
    )
    return HazardSimulationResponse(
        updated_segments=road_graph.number_of_edges(),
        critical_segments=critical_segments,
    )


@app.post("/api/report-blockage", response_model=BlockageReportResponse)
def report_blockage(
    request: BlockageReportRequest,
) -> BlockageReportResponse:
    """Manually mark every matching named segment as critically blocked."""
    matching_edges = [
        edge_data
        for _, _, edge_data in road_graph.edges(data=True)
        if edge_data.get("name") == request.segment_name
    ]
    if not matching_edges:
        raise HTTPException(
            status_code=404,
            detail=f"Road segment not found: {request.segment_name}",
        )

    for edge_data in matching_edges:
        edge_data["status"] = "BLOCKED_OR_CRITICAL"
        edge_data["risk_score"] = 1.0
        edge_data["blockage_reason"] = request.reason

    return BlockageReportResponse(
        segment_name=request.segment_name,
        reason=request.reason,
        status="BLOCKED_OR_CRITICAL",
    )
