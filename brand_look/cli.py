"""brand-look <url>: read a website's real look and save it for your AI agent."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from .extract import capture, summarise
from .write import write_all


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="brand-look", description=__doc__)
    ap.add_argument("url", help="website to read, e.g. https://stripe.com")
    ap.add_argument("--out", help="output folder (default: looks/<site>)")
    ap.add_argument("--name", help="look name (default: from the domain)")
    ap.add_argument("--raw", action="store_true", help="also save the raw probe")
    a = ap.parse_args(argv)

    url = a.url if re.match(r"^https?://", a.url) else "https://" + a.url
    host = urlparse(url).hostname or "site"
    name = a.name or re.sub(r"[^a-z0-9]+", "-", host.removeprefix("www.").split(".")[0].lower()).strip("-")
    out = Path(a.out or f"looks/{name}")

    t0 = time.time()
    raw = capture(url)
    look = summarise(raw)
    paths = write_all(look, out, name)
    if a.raw:
        (out / "raw.json").write_text(json.dumps(raw, indent=1))

    c = look["colors"]
    print(json.dumps({
        "site": url, "theme": look["theme"], "accent": c["accent"], "accent_from": c["accent_source"], "text": c["text_strong"],
        "page": c["page"], "font": look["type"]["body"],
        "buttons": "pill" if look["shape"]["pill_buttons"] else f"{look['shape']['button_radius']}px",
        "css_vars_found": look["css_vars_found"], "seconds": round(time.time() - t0, 1),
        "files": [str(p) for p in paths],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
