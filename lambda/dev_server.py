#!/usr/bin/env python3
"""Local dev server: serves frontend static files and mocks /api/routes."""
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

MOCK_RESPONSE = {
    "generated_at": "2026-03-21T13:24:00+01:00",
    "routes": [
        {
            "name": "T-bana från Skarpnäck",
            "walk_minutes": 12,
            "leave_home_by": "13:13",
            "departure": "13:25",
            "arrival": "14:05",
            "transfers": 2,
            "legs": ["17", "11", "🚶‍♂️‍➡️", "177"],
            "fastest": True,
        },
        {
            "name": "T-bana från Skogskyrkogården",
            "walk_minutes": 15,
            "leave_home_by": "13:10",
            "departure": "13:25",
            "arrival": "14:05",
            "transfers": 2,
            "legs": ["18", "11", "🚶‍♂️‍➡️", "177"],
            "fastest": False,
        },
        {
            "name": "Buss från Koloniområdet",
            "walk_minutes": 3,
            "leave_home_by": "13:26",
            "departure": "13:29",
            "arrival": "14:07",
            "transfers": 2,
            "legs": ["816", "🚶‍♂️‍➡️", "17", "🚶‍♂️‍➡️", "41"],
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
