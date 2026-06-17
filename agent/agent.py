"""ADK agent definition with Gemini 2.5 Flash lite model and four chekov tool functions."""

from google.adk import Agent

SYSTEM_INSTRUCTION = """\
You are Chekov assistant, a conversational helper for planning fuel-efficient road trips in Québec.

Rules:
1. Always call a tool when the user's intent clearly matches one of the four actions \
(submit_trip, add_waypoint, filter_stations_by_area, clear_filter).
2. If a required field is missing (origin or destination for submit_trip), ask one clarifying \
question — never call submit_trip with placeholder or fabricated values.
3. Respond in the same language the user writes in (French or English).
4. After calling a tool, confirm the action in 1–2 sentences maximum.
5. Do not invent station names, prices, or route details — you have no access to live data.\
"""


def submit_trip(
    origin: str,
    destination: str,
    range_km: float | None = None,
    waypoints: list[str] | None = None,
) -> dict:
    """Submit a trip planning request with origin, destination, optional range and waypoints."""
    return {"ok": True}


def add_waypoint(waypoint: str) -> dict:
    """Add a waypoint to the current trip route."""
    return {"ok": True}


def filter_stations_by_area(area_name: str, lat: float, lng: float) -> dict:
    """Filter visible gas stations to show only those near a specific area."""
    return {"ok": True}


def clear_filter() -> dict:
    """Remove the area filter and show all gas stations again."""
    return {"ok": True}


root_agent = Agent(
    name="chekov_assistant",
    model="gemini-2.5-flash-lite",
    instruction=SYSTEM_INSTRUCTION,
    tools=[submit_trip, add_waypoint, filter_stations_by_area, clear_filter],
)
