"""Domain model for the Trips app.

All user state is a single JSON document (AppState) stored in S3.
"""

from dataclasses import dataclass, field
import math
import uuid

from jsonschema import validate, ValidationError


# --- Entities ---

@dataclass
class Stop:
    stop_id: str
    name: str
    walk_minutes: int


@dataclass
class Location:
    id: str
    name: str
    lat: float
    lon: float
    address: str = ""
    stops: list[Stop] = field(default_factory=list)


@dataclass
class Trip:
    id: str
    name: str
    origin_id: str
    destination_id: str


# --- State ---

@dataclass
class AppState:
    locations: list[Location] = field(default_factory=list)
    trips: list[Trip] = field(default_factory=list)


# --- ID generation ---

def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# --- Serialization ---

def state_to_dict(state: AppState) -> dict:
    return {
        "locations": [_loc_to_dict(loc) for loc in state.locations],
        "trips": [_trip_to_dict(t) for t in state.trips],
    }


def dict_to_state(data: dict) -> AppState:
    return AppState(
        locations=[_dict_to_loc(d) for d in data.get("locations", [])],
        trips=[_dict_to_trip(d) for d in data.get("trips", [])],
    )


def _loc_to_dict(loc: Location) -> dict:
    d = {
        "id": loc.id,
        "name": loc.name,
        "lat": loc.lat,
        "lon": loc.lon,
        "stops": [{"stop_id": s.stop_id, "name": s.name, "walk_minutes": s.walk_minutes} for s in loc.stops],
    }
    if loc.address:
        d["address"] = loc.address
    return d


def _dict_to_loc(d: dict) -> Location:
    return Location(
        id=d["id"],
        name=d["name"],
        lat=float(d["lat"]),
        lon=float(d["lon"]),
        address=d.get("address", ""),
        stops=[Stop(s["stop_id"], s["name"], int(s["walk_minutes"])) for s in d.get("stops", [])],
    )


def _trip_to_dict(t: Trip) -> dict:
    return {"id": t.id, "name": t.name, "origin_id": t.origin_id, "destination_id": t.destination_id}


def _dict_to_trip(d: dict) -> Trip:
    return Trip(id=d["id"], name=d["name"], origin_id=d["origin_id"], destination_id=d["destination_id"])


# --- Lookup helpers ---

def find_location(state: AppState, location_id: str) -> Location | None:
    return next((l for l in state.locations if l.id == location_id), None)


def find_trip(state: AppState, trip_id: str) -> Trip | None:
    return next((t for t in state.trips if t.id == trip_id), None)


# --- Walking time calculation ---

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


WALK_SPEED_KMH = 5.0
DETOUR_FACTOR = 1.3


def estimate_walk_minutes(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    km = haversine_km(lat1, lon1, lat2, lon2)
    hours = (km * DETOUR_FACTOR) / WALK_SPEED_KMH
    return max(1, round(hours * 60))


# --- Transfer station deduplication (FR-10) ---

def deduplicate_transfers(stations: list[str]) -> list[str]:
    result: list[str] = []
    for station in stations:
        if not result:
            result.append(station)
            continue
        prev = result[-1]
        if station == prev:
            continue
        if station in prev:
            result[-1] = station
        elif prev in station:
            pass
        else:
            result.append(station)
    return result


# --- JSON Schemas ---

LOCATION_SCHEMA = {
    "type": "object",
    "required": ["name", "lat", "lon"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "lat": {"type": "number", "minimum": -90, "maximum": 90},
        "lon": {"type": "number", "minimum": -180, "maximum": 180},
        "address": {"type": "string"},
    },
    "additionalProperties": False,
}

STOP_SCHEMA = {
    "type": "object",
    "required": ["stop_id", "name", "walk_minutes"],
    "properties": {
        "stop_id": {"type": "string", "minLength": 1},
        "name": {"type": "string", "minLength": 1},
        "walk_minutes": {"type": "integer", "minimum": 0},
    },
    "additionalProperties": False,
}

TRIP_SCHEMA = {
    "type": "object",
    "required": ["name", "origin_id", "destination_id"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "origin_id": {"type": "string", "minLength": 1},
        "destination_id": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}

REORDER_SCHEMA = {
    "type": "object",
    "required": ["trip_ids"],
    "properties": {
        "trip_ids": {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1},
    },
    "additionalProperties": False,
}


def validate_json(data: dict, schema: dict) -> str | None:
    try:
        validate(instance=data, schema=schema)
        return None
    except ValidationError as e:
        return e.message
