"""Static dependency contract for the complete canonical V2 frontend."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "frontend"
ROUTES = {
    "index.html": "js/pages/landing.js", "login.html": "js/pages/login.js",
    "register.html": "js/pages/register.js", "forgot-password.html": "js/pages/forgot-password.js",
    "reset-password.html": "js/pages/reset-password.js",
    **{f"pages/{name}.html": f"js/pages/{name}.js" for name in (
        "dashboard", "ml-analysis", "dl-analysis", "multimodal", "research", "model-comparison",
        "datasets", "explainability", "calibration", "patients", "patient-detail", "history",
        "reports", "advisor", "model-status", "profile")},
}
LEGACY = ("app.js", "styles.css", "premium.css")

def fail(message): raise SystemExit(f"FRONTEND V2 STATIC VALIDATION: FAIL\n{message}")
def local_target(source, ref): return (source.parent / ref.split("?", 1)[0].split("#", 1)[0]).resolve()

for legacy in LEGACY:
    if (ROOT / legacy).exists(): fail(f"legacy frontend file still exists: {legacy}")

controllers = set()
for relative, controller in ROUTES.items():
    page = ROOT / relative
    if not page.exists(): fail(f"missing canonical page: {relative}")
    content = page.read_text(encoding="utf-8")
    if "/Users/" in content or any(name in content for name in LEGACY): fail(f"legacy or local path reference in {relative}")
    scripts = re.findall(r'<script[^>]+type="module"[^>]+src="([^"]+)"', content)
    expected = local_target(page, ("../" if relative.startswith("pages/") else "") + controller)
    if len(scripts) != 1 or local_target(page, scripts[0]) != expected: fail(f"canonical controller mismatch in {relative}")
    controllers.add(expected)
    ids = set(re.findall(r'id="([^"]+)"', content))
    for ref in re.findall(r'(?:src|href)="([^"]+)"', content):
        if ref.startswith(("http://", "https://", "mailto:")): continue
        if ref.startswith("#"):
            if ref[1:] not in ids: fail(f"missing anchor {ref} in {relative}")
            continue
        if not local_target(page, ref).exists(): fail(f"missing reference {ref} in {relative}")

modules = set((ROOT / "js").rglob("*.js"))
for module in modules:
    content = module.read_text(encoding="utf-8")
    if "/Users/" in content or any(name in content for name in LEGACY): fail(f"legacy or local path reference in {module.relative_to(ROOT)}")
    for ref in re.findall(r"from\s*['\"]([^'\"]+)['\"]", content):
        if ref.startswith(".") and not (module.parent / ref).resolve().exists(): fail(f"missing import {ref} in {module.relative_to(ROOT)}")

reachable, pending = set(controllers), list(controllers)
while pending:
    module = pending.pop()
    for ref in re.findall(r"from\s*['\"]([^'\"]+)['\"]", module.read_text(encoding="utf-8")):
        if ref.startswith("."):
            target = (module.parent / ref).resolve()
            if target not in reachable: reachable.add(target); pending.append(target)
dead = sorted(path.relative_to(ROOT) for path in modules - reachable)
if dead: fail(f"unreachable JS modules: {', '.join(map(str, dead))}")

app_css = ROOT / "css/app.css"
for stylesheet in (ROOT / "css").glob("*.css"):
    content = stylesheet.read_text(encoding="utf-8")
    if "/Users/" in content: fail(f"local path in {stylesheet.relative_to(ROOT)}")
    for ref in re.findall(r"@import\s+['\"]([^'\"]+)['\"]", content):
        if not (stylesheet.parent / ref).resolve().exists(): fail(f"missing CSS import {ref}")
imported = {local_target(app_css, ref) for ref in re.findall(r"@import\s+['\"]([^'\"]+)['\"]", app_css.read_text())}
dead_css = sorted(path.relative_to(ROOT) for path in set((ROOT / "css").glob("*.css")) - imported - {ROOT / "css/public.css", app_css})
if dead_css: fail(f"unreachable CSS modules: {', '.join(map(str, dead_css))}")

shell = (ROOT / "js/components/shell.js").read_text(encoding="utf-8")
nav_targets = re.findall(r"\['([^']+\.html)'\s*,", shell)
if len(nav_targets) != len(set(nav_targets)): fail("duplicate authenticated navigation target")
for target in nav_targets:
    if not (ROOT / "pages" / target).exists(): fail(f"dead navigation target: {target}")
if re.search(r"href\s*=\s*['\"]#[^'\"]+", shell): fail("legacy hash route in authenticated navigation")

print("FRONTEND V2 STATIC VALIDATION: PASS")
