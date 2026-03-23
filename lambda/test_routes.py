"""Tests for routes.py"""

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import routes
from models import AppState, Location, Stop, Trip

TZ = ZoneInfo("Europe/Stockholm")


def _api_response(dep="2026-03-21T08:30:00+01:00", arr="2026-03-21T09:00:00+01:00",
                  line="17", product="Tunnelbana", interchanges=0):
    return {
        "journeys": [{
            "tripDuration": 600,
            "interchanges": interchanges,
            "legs": [{
                "origin": {"departureTimePlanned": dep},
                "destination": {"arrivalTimePlanned": arr},
                "transportation": {"disassembledName": line, "product": {"name": product}},
            }],
        }]
    }


def _fixed_now(time_str):
    fixed = datetime.fromisoformat(f"2026-03-21T{time_str}:00+01:00")
    original_now = datetime.now
    def mock_now(tz=None):
        return fixed if tz else original_now()
    return patch("routes.datetime", wraps=datetime, **{"now": mock_now})


def _state():
    return AppState(
        locations=[
            Location("loc_1", "A", 59, 18, stops=[
                Stop("s1", "S1", 3), Stop("s2", "S2", 5),
            ]),
            Location("loc_2", "B", 59, 18, stops=[Stop("d1", "D1", 2)]),
        ],
        trips=[Trip("t1", "Test", "loc_1", "loc_2")],
    )


class TestProcessRoute:
    def test_returns_route_when_catchable(self):
        origin = Stop(stop_id="123", name="Test", walk_minutes=5)
        dest = Stop(stop_id="456", name="Dest", walk_minutes=2)
        with patch.object(routes, "fetch_trip", return_value=_api_response()), _fixed_now("08:20"):
            result = routes.process_route(origin, dest)
        assert result is not None
        assert result["name"] == "Från Test"
        assert result["leave_by"] == "08:25"
        assert result["arrive_by"] == "09:02"

    def test_returns_none_when_past(self):
        origin = Stop(stop_id="123", name="Test", walk_minutes=5)
        dest = Stop(stop_id="456", name="Dest", walk_minutes=2)
        with patch.object(routes, "fetch_trip", return_value=_api_response()), _fixed_now("08:30"):
            result = routes.process_route(origin, dest)
        assert result is None

    def test_returns_none_on_error(self):
        origin = Stop(stop_id="123", name="Test", walk_minutes=5)
        dest = Stop(stop_id="456", name="Dest", walk_minutes=2)
        with patch.object(routes, "fetch_trip", side_effect=Exception("timeout")):
            result = routes.process_route(origin, dest)
        assert result is None

    def test_prefers_estimated_times(self):
        origin = Stop(stop_id="123", name="Test", walk_minutes=2)
        dest = Stop(stop_id="456", name="Dest", walk_minutes=0)
        api_resp = {
            "journeys": [{
                "tripDuration": 600, "interchanges": 0,
                "legs": [{
                    "origin": {
                        "departureTimePlanned": "2026-03-21T08:30:00+01:00",
                        "departureTimeEstimated": "2026-03-21T08:33:00+01:00",
                    },
                    "destination": {
                        "arrivalTimePlanned": "2026-03-21T09:00:00+01:00",
                        "arrivalTimeEstimated": "2026-03-21T09:05:00+01:00",
                    },
                    "transportation": {"disassembledName": "17", "product": {"name": "Tunnelbana"}},
                }],
            }]
        }
        with patch.object(routes, "fetch_trip", return_value=api_resp), _fixed_now("08:20"):
            result = routes.process_route(origin, dest)
        assert result["departure"] == "08:33"
        assert result["arrival"] == "09:05"


class TestGetRoutes:
    @patch("routes.state")
    def test_no_trips_configured(self, mock_state):
        mock_state.load_state.return_value = AppState()
        result = routes.get_routes()
        assert "error" in result

    @patch("routes.state")
    def test_trip_not_found(self, mock_state):
        mock_state.load_state.return_value = _state()
        result = routes.get_routes(trip_id="nope")
        assert "error" in result

    @patch("routes.state")
    def test_selects_fastest_and_next(self, mock_state):
        mock_state.load_state.return_value = _state()
        fast_resp = _api_response("2026-03-21T08:35:00+01:00", "2026-03-21T09:00:00+01:00")
        slow_resp = _api_response("2026-03-21T08:30:00+01:00", "2026-03-21T09:30:00+01:00")

        def mock_fetch(origin_id, dest_id):
            return fast_resp if origin_id == "s1" else slow_resp

        with patch.object(routes, "fetch_trip", side_effect=mock_fetch), _fixed_now("08:20"):
            result = routes.get_routes()

        assert len(result["routes"]) == 2
        assert result["routes"][0]["fastest"] is True
        assert result["routes"][0]["name"] == "Från S1"
        assert result["origin"] == "A"
        assert result["destination"] == "B"
