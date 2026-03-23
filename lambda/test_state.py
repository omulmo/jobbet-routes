"""Tests for state.py"""

import json
from unittest.mock import patch, MagicMock
from models import AppState, Location, Stop, Trip
import state


class TestLoadState:
    @patch("state._get_s3")
    def test_loads_from_s3(self, mock_get_s3):
        s3 = MagicMock()
        mock_get_s3.return_value = s3
        s3.get_object.return_value = {
            "Body": MagicMock(read=lambda: json.dumps({
                "locations": [{"id": "l1", "name": "X", "lat": 59, "lon": 18, "stops": []}],
                "trips": [],
            }).encode())
        }
        with patch.object(state, "_bucket", "test-bucket"):
            result = state.load_state()
        assert len(result.locations) == 1
        assert result.locations[0].name == "X"

    @patch("state._get_s3")
    def test_falls_back_to_default(self, mock_get_s3):
        s3 = MagicMock()
        mock_get_s3.return_value = s3
        error = type(s3).exceptions = MagicMock()
        error.NoSuchKey = type("NoSuchKey", (Exception,), {})
        s3.get_object.side_effect = error.NoSuchKey()
        with patch.object(state, "_bucket", "test-bucket"):
            result = state.load_state()
        assert len(result.locations) > 0  # default_state.json has data


class TestSaveState:
    @patch("state._get_s3")
    def test_saves_to_s3(self, mock_get_s3):
        s3 = MagicMock()
        mock_get_s3.return_value = s3
        app_state = AppState(locations=[Location("l1", "X", 59, 18)], trips=[])
        with patch.object(state, "_bucket", "test-bucket"):
            state.save_state(app_state)
        s3.put_object.assert_called_once()
        call_kwargs = s3.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == "state.json"
        body = json.loads(call_kwargs["Body"])
        assert body["locations"][0]["name"] == "X"
