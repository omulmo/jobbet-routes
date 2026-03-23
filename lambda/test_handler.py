"""Tests for handler.py (HTTP routing)"""

import json
from unittest.mock import patch
import handler


def _event(method="GET", path="/api/routes", params=None):
    return {
        "requestContext": {"http": {"method": method}},
        "rawPath": path,
        "queryStringParameters": params,
    }


class TestRouting:
    @patch("handler.routes")
    def test_get_routes(self, mock_routes):
        mock_routes.get_routes.return_value = {"routes": []}
        resp = handler.handler(_event(), None)
        assert resp["statusCode"] == 200
        mock_routes.get_routes.assert_called_once_with(None, False)

    @patch("handler.routes")
    def test_get_routes_with_params(self, mock_routes):
        mock_routes.get_routes.return_value = {"routes": []}
        resp = handler.handler(_event(params={"trip": "t1", "reverse": "true"}), None)
        mock_routes.get_routes.assert_called_once_with("t1", True)

    def test_unknown_path(self):
        resp = handler.handler(_event(path="/api/unknown"), None)
        assert resp["statusCode"] == 404

    @patch("handler.routes")
    def test_internal_error(self, mock_routes):
        mock_routes.get_routes.side_effect = RuntimeError("boom")
        resp = handler.handler(_event(), None)
        assert resp["statusCode"] == 500
