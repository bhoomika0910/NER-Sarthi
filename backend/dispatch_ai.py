"""Keyless conversational dispatch parsing and tactical route assistance."""

import re
from typing import Any


WAYPOINTS = (
    "Teesta Bazaar",
    "Siliguri",
    "Gangtok",
    "Kalijhora",
    "Rangpo",
    "Singtam",
    "Sevoke",
    "Algarah",
    "Lava",
)


def _find_waypoint(text: str, candidates: list[str]) -> str | None:
    """Find the longest matching known waypoint in a prompt."""
    lowered_text = text.casefold()
    for candidate in sorted(candidates, key=len, reverse=True):
        if re.search(rf"\b{re.escape(candidate.casefold())}\b", lowered_text):
            return candidate
    return None


def parse_dispatch_prompt(user_prompt: str) -> dict[str, Any]:
    """Extract routing and cargo constraints from a dispatch message.

    The parser is deliberately deterministic so the assistant remains
    available without external LLM credentials or network access.
    """
    if not user_prompt or not user_prompt.strip():
        raise ValueError("user_prompt must not be empty")

    prompt = " ".join(user_prompt.split())
    origin: str | None = None
    destination: str | None = None
    route_match = re.search(
        r"\bfrom\s+(?P<origin>.+?)\s+to\s+(?P<destination>.+?)(?=,|\.|;|\s+(?:avoiding|avoid|with|carrying|for)\b|$)",
        prompt,
        re.IGNORECASE,
    )
    if route_match:
        origin = _find_waypoint(route_match.group("origin"), list(WAYPOINTS))
        destination = _find_waypoint(route_match.group("destination"), list(WAYPOINTS))

    if not origin or not destination:
        mentioned = [
            waypoint
            for waypoint in WAYPOINTS
            if re.search(rf"\b{re.escape(waypoint)}\b", prompt, re.IGNORECASE)
        ]
        if not origin and mentioned:
            origin = mentioned[0]
        if not destination and len(mentioned) > 1:
            destination = mentioned[1]

    lowered_prompt = prompt.casefold()
    if re.search(r"\b(medical|medicine|medicines|relief supplies)\b", lowered_prompt):
        cargo_priority = "medical"
    elif re.search(r"\b(food|ration|rations|groceries)\b", lowered_prompt):
        cargo_priority = "food"
    else:
        cargo_priority = "standard"

    hazard_constraint = None
    hazard_match = re.search(
        r"\b(avoid(?:ing)?|no)\s+([^.;]+?)(?=\s+(?:from|for|with|carrying)\b|[.;]|$)",
        prompt,
        re.IGNORECASE,
    )
    if hazard_match:
        hazard_constraint = f"avoid {hazard_match.group(2).strip()}"
    elif re.search(r"\b(rain|landslide|flood|hazard|blocked)\b", lowered_prompt):
        hazard_constraint = "avoid active hazard zones"

    return {
        "origin": origin,
        "destination": destination,
        "cargo_priority": cargo_priority,
        "hazard_constraint": hazard_constraint,
    }

