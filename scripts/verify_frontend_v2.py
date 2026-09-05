"""Lightweight static contract for the canonical V2 frontend routes."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "frontend"
PAGES = ["index.html", "login.html", "register.html", "forgot-password.html", "reset-password.html", "pages/dashboard.html", "pages/research.html", "pages/model-comparison.html", "pages/datasets.html", "pages/explainability.html", "pages/calibration.html"]

def fail(message):
    raise SystemExit(f"FRONTEND V2 STATIC VALIDATION: FAIL\n{message}")

for relative in PAGES:
    page = ROOT / relative
    if not page.exists(): fail(f"missing page: {relative}")
    content = page.read_text(encoding="utf-8")
    if "/Users/" in content: fail(f"absolute local path in {relative}")
    for ref in re.findall(r'(?:src|href)="([^"]+)"', content):
        if ref.startswith(("#", "http://", "https://", "mailto:")): continue
        target = (page.parent / ref).resolve()
        if not target.exists(): fail(f"missing reference {ref} in {relative}")

for module in (ROOT / "js").rglob("*.js"):
    content = module.read_text(encoding="utf-8")
    if "/Users/" in content: fail(f"absolute local path in {module.relative_to(ROOT)}")
    for ref in re.findall(r"from\s+['\"]([^'\"]+)['\"]", content):
        if ref.startswith(".") and not (module.parent / ref).resolve().exists(): fail(f"missing import {ref} in {module.relative_to(ROOT)}")

print("FRONTEND V2 STATIC VALIDATION: PASS")
