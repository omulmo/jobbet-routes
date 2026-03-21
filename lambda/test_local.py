#!/usr/bin/env python3
"""Invoke the Lambda handler locally and pretty-print the response."""
import json
from handler import handler

result = handler({}, None)
body = json.loads(result["body"])
print(json.dumps(body, indent=2, ensure_ascii=False))
