"""Tests for models.py"""

import json
from models import (
    Location, Stop, Trip, AppState,
    state_to_dict, dict_to_state, find_location, find_trip,
    _loc_to_dict, _trip_to_dict,
    estimate_walk_minutes, deduplicate_transfers,
    validate_json, LOCATION_SCHEMA, STOP_SCHEMA, TRIP_SCHEMA, REORDER_SCHEMA,
    new_id,
)


class TestStateRoundTrip:
    def test_full_roundtrip(self):
        state = AppState(
            locations=[
                Location("l1", "Hemma", 59.27, 18.11, address="Gata 1",
                         stops=[Stop("s1", "Skarpnäck", 12)]),
                Location("l2", "Jobbet", 59.36, 18.00),
            ],
            trips=[Trip("t1", "Jobbet", "l1", "l2")],
        )
        d = state_to_dict(state)
        back = dict_to_state(d)
        assert len(back.locations) == 2
        assert back.locations[0].address == "Gata 1"
        assert back.locations[0].stops[0].stop_id == "s1"
        assert back.locations[1].address == ""
        assert back.trips[0].name == "Jobbet"

    def test_empty_state(self):
        state = AppState()
        d = state_to_dict(state)
        back = dict_to_state(d)
        assert back.locations == []
        assert back.trips == []

    def test_address_omitted_when_empty(self):
        loc = Location("l1", "X", 59, 18)
        d = _loc_to_dict(loc)
        assert "address" not in d


class TestLookupHelpers:
    def test_find_location(self):
        s = AppState(locations=[Location("l1", "A", 0, 0)])
        assert find_location(s, "l1").name == "A"
        assert find_location(s, "nope") is None

    def test_find_trip(self):
        s = AppState(trips=[Trip("t1", "X", "a", "b")])
        assert find_trip(s, "t1").name == "X"
        assert find_trip(s, "nope") is None


class TestDefaultState:
    def test_loads_and_roundtrips(self):
        import os
        path = os.path.join(os.path.dirname(__file__), "default_state.json")
        with open(path) as f:
            data = json.load(f)
        state = dict_to_state(data)
        assert len(state.locations) == 2
        assert len(state.trips) == 1
        assert state_to_dict(state) == data


class TestWalkingTime:
    def test_short_distance(self):
        mins = estimate_walk_minutes(59.270, 18.110, 59.274, 18.114)
        assert 2 <= mins <= 10

    def test_minimum_one_minute(self):
        assert estimate_walk_minutes(59.0, 18.0, 59.0, 18.0) == 1


class TestDeduplicateTransfers:
    def test_removes_consecutive_duplicates(self):
        assert deduplicate_transfers(["A", "A", "B"]) == ["A", "B"]

    def test_collapses_near_duplicates(self):
        assert deduplicate_transfers(["Stockholm Odenplan", "Odenplan"]) == ["Odenplan"]
        assert deduplicate_transfers(["Odenplan", "Stockholm Odenplan"]) == ["Odenplan"]

    def test_keeps_different_stations(self):
        assert deduplicate_transfers(["A", "B", "C"]) == ["A", "B", "C"]

    def test_empty(self):
        assert deduplicate_transfers([]) == []


class TestValidation:
    def test_valid_location(self):
        assert validate_json({"name": "X", "lat": 59.0, "lon": 18.0}, LOCATION_SCHEMA) is None

    def test_location_missing_name(self):
        assert validate_json({"lat": 59.0, "lon": 18.0}, LOCATION_SCHEMA) is not None

    def test_location_empty_name(self):
        assert validate_json({"name": "", "lat": 59.0, "lon": 18.0}, LOCATION_SCHEMA) is not None

    def test_location_extra_field(self):
        assert validate_json({"name": "X", "lat": 59.0, "lon": 18.0, "extra": 1}, LOCATION_SCHEMA) is not None

    def test_valid_stop(self):
        assert validate_json({"stop_id": "s1", "name": "S", "walk_minutes": 5}, STOP_SCHEMA) is None

    def test_stop_negative_walk(self):
        assert validate_json({"stop_id": "s1", "name": "S", "walk_minutes": -1}, STOP_SCHEMA) is not None

    def test_valid_trip(self):
        assert validate_json({"name": "X", "origin_id": "a", "destination_id": "b"}, TRIP_SCHEMA) is None

    def test_trip_missing_name(self):
        assert validate_json({"origin_id": "a", "destination_id": "b"}, TRIP_SCHEMA) is not None

    def test_valid_reorder(self):
        assert validate_json({"trip_ids": ["a", "b"]}, REORDER_SCHEMA) is None

    def test_reorder_empty(self):
        assert validate_json({"trip_ids": []}, REORDER_SCHEMA) is not None


class TestIdGeneration:
    def test_prefix(self):
        assert new_id("loc").startswith("loc_")
        assert new_id("trip").startswith("trip_")

    def test_unique(self):
        assert new_id("x") != new_id("x")
