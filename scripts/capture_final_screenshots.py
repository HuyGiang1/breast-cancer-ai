#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import json
import os
import time
import urllib.request
from pathlib import Path

import websocket


ROUTES = {
    "01-landing.jpg": "/",
    "02-dashboard.jpg": "/pages/dashboard.html",
    "03-ml-analysis.jpg": "/pages/ml-analysis.html",
    "04-dl-analysis.jpg": "/pages/dl-analysis.html",
    "05-research-center.jpg": "/pages/research.html",
    "06-dataset-explorer.jpg": "/pages/datasets.html",
    "07-explainability.jpg": "/pages/explainability.html",
    "08-model-status.jpg": "/pages/model-status.html",
}


class DevTools:
    def __init__(self, websocket_url: str) -> None:
        self.socket = websocket.create_connection(websocket_url, suppress_origin=True)
        self.message_id = 0

    def close(self) -> None:
        self.socket.close()

    def call(self, method: str, params: dict | None = None) -> dict:
        self.message_id += 1
        request_id = self.message_id
        self.socket.send(
            json.dumps({"id": request_id, "method": method, "params": params or {}})
        )
        while True:
            response = json.loads(self.socket.recv())
            if response.get("id") == request_id:
                if "error" in response:
                    raise RuntimeError(f"Chrome DevTools error: {response['error']}")
                return response.get("result", {})


def page_websocket(debug_url: str) -> str:
    with urllib.request.urlopen(f"{debug_url}/json", timeout=5) as response:
        pages = json.load(response)
    page = next(item for item in pages if item.get("type") == "page")
    return page["webSocketDebuggerUrl"]


def wait_until_ready(client: DevTools, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = client.call(
            "Runtime.evaluate",
            {"expression": "document.readyState", "returnByValue": True},
        )
        if result.get("result", {}).get("value") == "complete":
            time.sleep(1.2)
            return
        time.sleep(0.2)
    raise TimeoutError("Page did not reach document.readyState=complete")


def navigate(client: DevTools, url: str) -> None:
    client.call("Page.navigate", {"url": url})
    wait_until_ready(client)


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture the final public report screenshots.")
    parser.add_argument("--base-url", default="http://127.0.0.1")
    parser.add_argument("--debug-url", default="http://127.0.0.1:9222")
    parser.add_argument("--output-dir", default="docs/assets/screenshots")
    args = parser.parse_args()

    token = os.environ.get("BCAI_SCREENSHOT_TOKEN")
    if not token:
        raise SystemExit("BCAI_SCREENSHOT_TOKEN is required")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = DevTools(page_websocket(args.debug_url))
    try:
        client.call("Page.enable")
        client.call("Runtime.enable")
        client.call(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": 1440,
                "height": 900,
                "deviceScaleFactor": 1,
                "mobile": False,
            },
        )

        navigate(client, f"{args.base_url}/")
        landing = client.call(
            "Page.captureScreenshot",
            {"format": "jpeg", "quality": 82, "fromSurface": True},
        )
        (output_dir / "01-landing.jpg").write_bytes(base64.b64decode(landing["data"]))

        user = {
            "id": 12,
            "email": "release-demo@example.invalid",
            "full_name": "Research Demo",
            "role": "doctor",
        }
        expression = (
            f"localStorage.setItem('bcai_token', {json.dumps(token)});"
            f"localStorage.setItem('bcai_user', {json.dumps(json.dumps(user))});"
        )
        client.call("Runtime.evaluate", {"expression": expression})

        for filename, route in list(ROUTES.items())[1:]:
            navigate(client, f"{args.base_url}{route}")
            screenshot = client.call(
                "Page.captureScreenshot",
                {"format": "jpeg", "quality": 82, "fromSurface": True},
            )
            (output_dir / filename).write_bytes(base64.b64decode(screenshot["data"]))
            print(f"captured {filename}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
