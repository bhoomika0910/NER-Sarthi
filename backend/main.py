"""NER-SARTHI FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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


# Basic service health endpoint for local development and monitoring.
@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Return the current API service status."""
    return {"status": "ok", "project": "NER-SARTHI"}
