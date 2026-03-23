#!/usr/bin/env python3
"""Local dev server: serves frontend and proxies /api/* to the Lambda handler."""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Use in-memory state for local dev
import state
from models import dict_to_state, state_to_dict

_state_file = os.path.join(os.path.dirname(__file__), "default_state.json")
with open(_state_file) as f:
    _mem_state = dict_to_state(json.load(f))

_original_load = state.load_state
_original_save = state.save_state

def _mock_load():
    return _mem_state

def _mock_save(s):
    global _mem_state
    _mem_state = s

state.load_state = _mock_load
state.save_state = _mock_save

import handler


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            super().do_GET()

    def do_POST(self):
        self._proxy()

    def do_PUT(self):
        self._proxy()

    def do_DELETE(self):
        self._proxy()

    def _proxy(self):
        path = self.path.split("?")[0]
        qs = self.path.split("?")[1] if "?" in self.path else ""
        params = dict(p.split("=", 1) for p in qs.split("&") if "=" in p) if qs else None

        body = None
        length = int(self.headers.get("Content-Length", 0))
        if length:
            body = self.rfile.read(length).decode()

        event = {
            "requestContext": {"http": {"method": self.command}},
            "rawPath": path,
            "queryStringParameters": params,
            "body": body,
        }

        result = handler.handler(event, None)
        self.send_response(result["statusCode"])
        for k, v in result.get("headers", {}).items():
            self.send_header(k, v)
        self.end_headers()
        if "body" in result:
            self.wfile.write(result["body"].encode())


os.chdir(os.path.join(os.path.dirname(__file__), "..", "frontend"))
print("Serving on http://localhost:8000")
HTTPServer(("", 8000), Handler).serve_forever()
