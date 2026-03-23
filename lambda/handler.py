"""HTTP router for the Trips Lambda function."""

import json
import logging

import routes

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "")
    params = event.get("queryStringParameters") or {}

    try:
        return _route(method, path, params)
    except Exception:
        logger.exception("Unhandled error")
        return _json_response(500, {"error": "Internal server error"})


def _route(method, path, params):
    if path == "/api/routes" and method == "GET":
        trip_id = params.get("trip")
        reverse = params.get("reverse", "").lower() == "true"
        return _json_response(200, routes.get_routes(trip_id, reverse))

    return _json_response(404, {"error": "Not found"})


def _json_response(status, body):
    resp = {"statusCode": status, "headers": {"Content-Type": "application/json"}}
    if body is not None:
        resp["body"] = json.dumps(body, ensure_ascii=False)
    return resp
