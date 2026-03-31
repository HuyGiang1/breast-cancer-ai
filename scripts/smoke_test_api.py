#!/usr/bin/env python3
"""Quick API smoke test for local development.

Usage:
  source venv/bin/activate
  python scripts/smoke_test_api.py
"""

from __future__ import annotations

import json
import sys
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

BASE_URL = "http://localhost:8000/api/v1"


def get_json(path: str):
    req = Request(f"{BASE_URL}{path}", method="GET")
    with urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(f"GET {path} failed with status {resp.status}")
        data = resp.read().decode("utf-8")
        return json.loads(data)


def main() -> int:
    try:
        models = get_json("/models/")
        dl_models = get_json("/models/dl/")
        benchmarks = get_json("/models/benchmarks/")

        print("API smoke test passed")
        print(f"- ML models: {len(models)} -> {models}")
        print(f"- DL models: {len(dl_models)} -> {dl_models}")
        print(f"- Benchmarks: {len(benchmarks)} entries")

        try:
            research = get_json("/research/summary/")
            source = research.get("source", "unknown")
            print(f"- Research summary: available ({source})")
        except Exception:
            print("- Research summary: not available yet (run notebook export to generate JSON)")

        return 0
    except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
        print("API smoke test failed")
        print(f"- Error: {exc}")
        print("- Ensure backend is running: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        return 1


if __name__ == "__main__":
    sys.exit(main())
