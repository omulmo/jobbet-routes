#!/usr/bin/env python3
"""Local dev server: serves frontend static files and mocks /api/routes."""
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

MOCK_RESPONSE = {
    "generated_at": "2026-03-21T07:45:00+01:00",
    "routes": [
        {
            "name": "Buss från Koloniområdet",
            "walk_minutes": 3,
            "leave_home_by": "07:48",
            "departure": "07:51",
            "arrival": "08:37",
            "transfers": 2,
            "legs": ["816", "17", "41"],
            "fastest": True,
        },
        {
            "name": "T-bana från Skarpnäck",
            "walk_minutes": 12,
            "leave_home_by": "07:40",
            "departure": "07:52",
            "arrival": "08:42",
            "transfers": 1,
            "legs": ["17", "41"],
            "fastest": False,
        },
        {
            "name": "T-bana från Skogskyrkogården",
            "walk_minutes": 15,
            "leave_home_by": "07:35",
            "departure": "07:50",
            "arrival": "08:44",
            "transfers": 1,
            "legs": ["17", "41"],
            "fastest": False,
        },
    ],
}

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/routes":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(MOCK_RESPONSE, ensure_ascii=False).encode())
        else:
            super().do_GET()

os.chdir(os.path.join(os.path.dirname(__file__), "..", "frontend"))
print("Serving on http://localhost:8000")
HTTPServer(("", 8000), Handler).serve_forever()
