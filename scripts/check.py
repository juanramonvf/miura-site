#!/usr/bin/env python3
"""Validate generated pages, local navigation and published product assets."""

from pathlib import Path
import re
import sys
from urllib.parse import urlsplit


root = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
required = [
    "index.html", "panel/index.html", "help/index.html", "news/index.html",
    "help.html", "ayuda.html", "news.html", "novedades.html", "changelog.html", "README.txt",
    "CNAME", "assets/screenshots/panel-desktop.png", "assets/screenshots/panel-tablet.png",
]
missing = [path for path in required if not (root / path).is_file()]
if missing:
    raise SystemExit("Faltan rutas o recursos: " + ", ".join(missing))
if (root / "CNAME").read_text(encoding="ascii").strip() != "miura.srtgateway.ovh":
    raise SystemExit("CNAME no coincide con el dominio oficial")

pages = list(root.rglob("*.html"))
for page in pages:
    source = page.read_text(encoding="utf-8")
    if not re.search(r"<html\s+lang=[\"']es[\"]", source, re.I):
        raise SystemExit(f"Falta idioma español: {page}")
    if not re.search(r"<meta\s+name=[\"']viewport[\"]", source, re.I):
        raise SystemExit(f"Falta viewport móvil: {page}")
    if not re.search(r"<main\b", source, re.I):
        raise SystemExit(f"Falta contenido principal semántico: {page}")
    for value in re.findall(r"(?:href|src)=[\"']([^\"']+)[\"']", source, re.I):
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc:
            if parsed.scheme != "https" or parsed.hostname not in {"github.com"}:
                raise SystemExit(f"Enlace externo no permitido en {page}: {value}")
            if parsed.username or parsed.password:
                raise SystemExit(f"URL con credenciales no permitida en {page}: {value}")
            continue
        if value.startswith("#"):
            continue
        target_path = (root / parsed.path.lstrip("/")).resolve()
        if root.resolve() not in target_path.parents and target_path != root.resolve():
            raise SystemExit(f"Ruta local fuera del sitio en {page}: {value}")
        if target_path.is_dir():
            target_path = target_path / "index.html"
        if not target_path.is_file():
            raise SystemExit(f"Enlace local roto {page}: {value}")

print(f"OK: {len(pages)} páginas, aliases, enlaces locales, capturas y CNAME")
