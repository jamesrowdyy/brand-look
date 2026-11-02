"""Write the look as files an AI agent can use."""
from __future__ import annotations

import json
from pathlib import Path


def stageshow_css(t: dict, name: str) -> str:
    c, s, d, ty = t["colors"], t["shape"], t["density"], t["type"]
    return f"""/* {name} look, read from {t['url']} by brand-look.
   Drop into a Stageshow project and use <Stage className="look-{name}">.
   Works as plain CSS variables in any other project too. */
.look-{name} .ss-stage, .look-{name} {{
  --ss-canvas: {c['page']};
  --ss-surface: {c['surface']};
  --ss-chrome: {c['surface_alt']};
  --ss-well: {c['surface_alt']};
  --ss-line: {c['line']};
  --ss-text-strong: {c['text_strong']};
  --ss-text: {c['text']};
  --ss-text-faint: {c['text_faint']};
  --ss-accent: {c['accent']};
  --ss-font: "{ty['body']}", system-ui, sans-serif;
  --ss-radius-sm: {s['radius_sm']}px;
  --ss-radius-md: {s['radius_md']}px;
  --ss-radius-lg: {s['radius_lg']}px;
  --ss-radius-pill: 999px;
  --ss-control: {d['control']}px;
}}
"""


def tailwind(t: dict) -> str:
    c, s, ty = t["colors"], t["shape"], t["type"]
    cfg = {
        "theme": {"extend": {
            "colors": {
                "page": c["page"], "surface": c["surface"], "ink": c["text_strong"],
                "muted": c["text"], "faint": c["text_faint"], "line": c["line"],
                "accent": c["accent"], "button": c["button"],
            },
            "fontFamily": {"sans": [ty["body"], "system-ui", "sans-serif"],
                           "display": [ty["heading"], "system-ui", "sans-serif"]},
            "borderRadius": {"sm": f"{s['radius_sm']}px", "md": f"{s['radius_md']}px",
                             "lg": f"{s['radius_lg']}px",
                             "button": "9999px" if s["pill_buttons"] else f"{s['button_radius']}px"},
        }}
    }
    return "// brand-look: paste into tailwind.config.js\nmodule.exports = " + json.dumps(cfg, indent=2) + "\n"


def brief(t: dict, name: str) -> str:
    c, s, d, ty, k = t["colors"], t["shape"], t["density"], t["type"], t["contrast"]
    btn = "pill (fully round)" if s["pill_buttons"] else f"{s['button_radius']}px corners"
    warn = []
    if k["muted_on_page"] < 4.5:
        warn.append(f"- Muted text {c['text']} is {k['muted_on_page']}:1 on the page. Use it for large or secondary text only.")
    if k["accent_on_page"] < 3:
        warn.append(f"- Accent {c['accent']} is {k['accent_on_page']}:1 on the page. Do not use it for small text.")
    warn_txt = "\n".join(warn) or "- All main text colours pass WCAG AA on the page colour."
    return f"""# {name} look

Read from {t['url']} by brand-look. Every value below came from the live site's computed styles.

## Rules for the agent

Build any UI for this brand with these values only. Do not invent colours, fonts or corner sizes.
One accent colour, used sparingly: buttons, links, the one thing the viewer should look at.
Everything else is the page colour, the surface colour, the line colour and the three text greys.

| Token | Value |
|---|---|
| Theme | {t['theme']} |
| Page | `{c['page']}` |
| Surface (cards, windows) | `{c['surface']}` |
| Second surface | `{c['surface_alt']}` |
| Hairline borders | `{c['line']}` |
| Headings, strong text | `{c['text_strong']}` ({k['text_on_page']}:1) |
| Body and secondary text | `{c['text']}` ({k['muted_on_page']}:1) |
| Faint text | `{c['text_faint']}` |
| Accent | `{c['accent']}` ({k['accent_on_page']}:1) |
| Primary button fill | `{c['button']}` |
| Body font | {ty['body']} |
| Heading font | {ty['heading']} (h1 {ty['h1_size']}px, weight {ty['h1_weight']}, tracking {ty['h1_tracking']}) |
| Corners | small {s['radius_sm']}px, medium {s['radius_md']}px, large {s['radius_lg']}px |
| Buttons | {btn}, about {d['button']}px tall |
| Inputs and controls | about {d['control']}px tall |

## Watch out

{warn_txt}

## Files

- `look.css`: CSS variables (Stageshow token names, works anywhere)
- `tailwind.config.js`: the same values for Tailwind
- `look.json`: the raw numbers
- `preview.html`: a sample product card in this look, so you can check it at a glance
"""


def preview(t: dict, name: str) -> str:
    c, s, ty = t["colors"], t["shape"], t["type"]
    br = "999px" if s["pill_buttons"] else f"{s['button_radius']}px"
    return f"""<!doctype html><meta charset="utf-8"><title>{name} look</title>
<style>
body{{margin:0;background:{c['page']};font-family:"{ty['body']}",system-ui,sans-serif;color:{c['text']};
display:grid;place-items:center;min-height:100vh}}
.card{{width:420px;background:{c['surface']};border:1px solid {c['line']};border-radius:{s['radius_lg']}px;padding:28px;
box-shadow:0 12px 40px rgba(0,0,0,.08)}}
h1{{font-family:"{ty['heading']}",system-ui,sans-serif;color:{c['text_strong']};font-size:24px;margin:0 0 6px;letter-spacing:-.02em}}
p{{margin:0 0 20px;font-size:15px}}
.f{{height:{t['density']['control']}px;border:1px solid {c['line']};border-radius:{s['radius_md']}px;background:{c['page']};
margin-bottom:12px;display:flex;align-items:center;padding:0 14px;color:{c['text_faint']};font-size:14px}}
.b{{display:inline-flex;align-items:center;height:{t['density']['button'] or 40}px;padding:0 20px;border-radius:{br};
background:{c['button']};color:#fff;font-weight:600;font-size:15px}}
a{{color:{c['accent']};font-size:14px;margin-left:14px}}
</style>
<div class="card"><h1>Invite your team</h1><p>Read from {t['url']}</p>
<div class="f">name@company.com</div><span class="b">Send invite</span><a>Copy link</a></div>
"""


def write_all(t: dict, out: Path, name: str) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "look.json": json.dumps(t, indent=2) + "\n",
        "look.css": stageshow_css(t, name),
        "tailwind.config.js": tailwind(t),
        "LOOK.md": brief(t, name),
        "preview.html": preview(t, name),
    }
    paths = []
    for fname, body in files.items():
        p = out / fname
        p.write_text(body)
        paths.append(p)
    return paths
