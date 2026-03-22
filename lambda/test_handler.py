import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import handler as h

TZ = h.TZ

def _make_api_response(dep_planned, arr_planned, line_name="17", product="Tunnelbana", interchanges=0):
    """Build a minimal SL API response for one journey with one transit leg."""
    return {
        "journeys": [{
            "tripDuration": 600,
            "interchanges": interchanges,
            "legs": [{
                "origin": {"departureTimePlanned": dep_planned},
                "destination": {"arrivalTimePlanned": arr_planned},
                "transportation": {
                    "disassembledName": line_name,
                    "product": {"name": product},
                },
            }],
        }]
    }


def _fixed_now(time_str):
    """Return a patcher that fixes datetime.now to a given HH:MM in TZ."""
    fixed = datetime.fromisoformat(f"2026-03-21T{time_str}:00+01:00")
    original_now = datetime.now

    def mock_now(tz=None):
        return fixed if tz else original_now()

    return patch("handler.datetime", wraps=datetime, **{"now": mock_now})


class TestProcessRoute:
    def test_returns_route_when_leave_by_in_future(self):
        route = {"name": "Test", "walk_minutes": 5, "origin_id": "123"}
        api_resp = _make_api_response(
            "2026-03-21T08:30:00+01:00", "2026-03-21T09:00:00+01:00", "41", "Tåg"
        )
        with patch.object(h, "fetch_trip", return_value=api_resp), _fixed_now("08:20"):
            result = h.process_route(route)

        assert result is not None
        assert result["name"] == "Test"
        assert result["leave_home_by"] == "08:25"
        assert result["departure"] == "08:30"
        assert result["arrival"] == "09:00"
        assert result["legs"] == ["🚆 41"]
        assert result["transfer_stations"] == []

    def test_returns_none_when_leave_by_in_past(self):
        route = {"name": "Test", "walk_minutes": 5, "origin_id": "123"}
        api_resp = _make_api_response(
            "2026-03-21T08:30:00+01:00", "2026-03-21T09:00:00+01:00"
        )
        with patch.object(h, "fetch_trip", return_value=api_resp), _fixed_now("08:30"):
            result = h.process_route(route)

        assert result is None

    def test_returns_none_on_api_error(self):
        route = {"name": "Test", "walk_minutes": 5, "origin_id": "123"}
        with patch.object(h, "fetch_trip", side_effect=Exception("timeout")):
            result = h.process_route(route)

        assert result is None

    def test_includes_walking_legs_as_emoji(self):
        route = {"name": "Test", "walk_minutes": 2, "origin_id": "123"}
        api_resp = {
            "journeys": [{
                "tripDuration": 600,
                "interchanges": 1,
                "legs": [
                    {
                        "origin": {"parent": {"disassembledName": "Skarpnäcks koloniområde"}, "departureTimePlanned": "2026-03-21T08:30:00+01:00"},
                        "destination": {"arrivalTimePlanned": "2026-03-21T08:35:00+01:00"},
                        "transportation": {"disassembledName": "816", "product": {"name": "Buss"}},
                    },
                    {
                        "origin": {"parent": {"disassembledName": "Skarpnäck"}, "departureTimePlanned": "2026-03-21T08:35:00+01:00"},
                        "destination": {"arrivalTimePlanned": "2026-03-21T08:40:00+01:00"},
                        "transportation": {"product": {"name": "footpath"}},
                    },
                    {
                        "origin": {"parent": {"disassembledName": "Skarpnäck"}, "departureTimePlanned": "2026-03-21T08:40:00+01:00"},
                        "destination": {"arrivalTimePlanned": "2026-03-21T09:00:00+01:00"},
                        "transportation": {"disassembledName": "17", "product": {"name": "Tunnelbana"}},
                    },
                ],
            }]
        }
        with patch.object(h, "fetch_trip", return_value=api_resp), _fixed_now("08:20"):
            result = h.process_route(route)

        assert result["legs"] == ["🚌 816", "🚶‍♂️‍➡️", "🚇 17"]
        assert result["transfer_stations"] == ["Skarpnäck"]

class TestHandler:
    def test_marks_fastest_route(self):
        routes = [
            {"name": "Slow", "walk_minutes": 5, "origin_id": "1"},
            {"name": "Fast", "walk_minutes": 3, "origin_id": "2"},
        ]
        slow_resp = _make_api_response("2026-03-21T08:30:00+01:00", "2026-03-21T09:30:00+01:00")
        fast_resp = _make_api_response("2026-03-21T08:35:00+01:00", "2026-03-21T09:10:00+01:00")

        def mock_fetch(origin_id):
            return fast_resp if origin_id == "2" else slow_resp

        with patch.object(h, "ROUTES", routes), \
             patch.object(h, "fetch_trip", side_effect=mock_fetch), \
             _fixed_now("08:20"):
            result = h.handler({}, None)

        body = json.loads(result["body"])
        assert len(body["routes"]) == 2
        assert body["routes"][0]["name"] == "Fast"
        assert body["routes"][0]["fastest"] is True
        assert body["routes"][1]["fastest"] is False

    def test_returns_error_when_no_routes(self):
        with patch.object(h, "ROUTES", []), _fixed_now("08:00"):
            result = h.handler({}, None)

        body = json.loads(result["body"])
        assert body["routes"] == []
        assert "error" in body

    def test_prefers_estimated_over_planned(self):
        route = {"name": "Test", "walk_minutes": 2, "origin_id": "1"}
        api_resp = {
            "journeys": [{
                "tripDuration": 600,
                "interchanges": 0,
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
        with patch.object(h, "fetch_trip", return_value=api_resp), _fixed_now("08:20"):
            result = h.process_route(route)

        assert result["departure"] == "08:33"
        assert result["arrival"] == "09:05"
        assert result["leave_home_by"] == "08:31"
