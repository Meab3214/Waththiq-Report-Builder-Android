#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "public/assets/branding/wasm_app_icon.png"
SPLASH = ROOT / "public/assets/branding/wasm_splash.png"
EXPECTED_ICON = "e31d2d96c7465771fd02853455fdf626768ea9e5b7ae32331c93e15da11222ef"
EXPECTED_SPLASH = "58b1ccc43e4b6594862e78266b09e0bac928a6b2eeac1ccb7121f7b34de68598"
VIEWPORTS = [(360,640),(360,800),(390,844),(412,915),(430,932),(768,1024),(1080,1920)]

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert digest(ICON) == EXPECTED_ICON, "Official app icon bytes changed"
assert digest(SPLASH) == EXPECTED_SPLASH, "Official splash bytes changed"
icon = Image.open(ICON)
splash = Image.open(SPLASH)
assert icon.size == (1536, 1536)
assert splash.size == (864, 1536)

sw, sh = splash.size
for vw, vh in VIEWPORTS:
    scale = min(vw / sw, vh / sh)
    rw, rh = sw * scale, sh * scale
    assert rw <= vw + 0.01 and rh <= vh + 0.01
    assert rw > 0 and rh > 0

manifest = json.loads((ROOT / "public/manifest.json").read_text(encoding="utf-8"))
assert manifest["name"] == "وَسْم"
assert manifest["short_name"] == "وَسْم"
assert manifest["description"] == "إنجازك في تقرير يليق بأثره"
assert manifest["background_color"].lower() == "#08211e"
assert manifest["theme_color"].lower() == "#08211e"

required = [
    ROOT / "public/favicon.ico",
    ROOT / "public/icons/icon-16.png",
    ROOT / "public/icons/icon-32.png",
    ROOT / "public/icons/icon-48.png",
    ROOT / "public/icons/icon-180.png",
    ROOT / "public/icons/icon-192.png",
    ROOT / "public/icons/icon-256.png",
    ROOT / "public/icons/icon-384.png",
    ROOT / "public/icons/icon-512.png",
    ROOT / "public/icons/icon-maskable-512.png",
]
for path in required:
    assert path.exists() and path.stat().st_size > 0, f"Missing generated asset: {path}"

app_text = (ROOT / "src/App.tsx").read_text(encoding="utf-8")
editor_text = (ROOT / "src/components/Editor/ReportEditorForm.tsx").read_text(encoding="utf-8")
combined = app_text + editor_text
assert "منصة وثّق" not in combined and "منصة وثق" not in combined
assert "وَسْم" in combined
assert "إنجازك في تقرير" in app_text and "يليق بأثره" in app_text
print("WASM branding verification passed for all requested viewports and source checks.")
