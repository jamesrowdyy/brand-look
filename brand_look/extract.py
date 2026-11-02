"""Read a live website's real design tokens with a headless browser."""
from __future__ import annotations

import colorsys
import re
from collections import Counter

JS_PROBE = r"""
() => {
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 2 && r.height > 2 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05; };
  const area = el => { const r = el.getBoundingClientRect(); return Math.min(r.width * r.height, 2e6); };
  const pick = (sel, n = 400) => [...document.querySelectorAll(sel)].filter(vis).slice(0, n);
  const out = { bg: [], text: [], fonts: [], radii: [], buttons: [], links: [], headings: [], inputs: [], borders: [] };
  const bodyBg = getComputedStyle(document.body).backgroundColor;
  const htmlBg = getComputedStyle(document.documentElement).backgroundColor;
  out.page_bg = bodyBg === 'rgba(0, 0, 0, 0)' ? htmlBg : bodyBg;
  for (const el of pick('body *', 3000)) {
    const s = getComputedStyle(el);
    if (s.backgroundColor && s.backgroundColor !== 'rgba(0, 0, 0, 0)') out.bg.push([s.backgroundColor, area(el)]);
    const own = [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim().length > 1);
    if (own) {
      const len = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('').length;
      out.text.push([s.color, len]);
      out.fonts.push([s.fontFamily, len]);
    }
    const r = parseFloat(s.borderTopLeftRadius);
    if (r > 0 && r < 60) out.radii.push([Math.round(r), el.tagName.toLowerCase()]);
    if (parseFloat(s.borderTopWidth) >= 0.5 && s.borderTopStyle !== 'none') out.borders.push(s.borderTopColor);
  }
  const btnSel = 'button, [role=button], a.btn, a.button, a[class*=btn], a[class*=button], input[type=submit]';
  for (const el of pick(btnSel, 60)) { const s = getComputedStyle(el); const r = el.getBoundingClientRect();
    out.buttons.push({ bg: s.backgroundColor, color: s.color, radius: parseFloat(s.borderTopLeftRadius), h: Math.round(r.height),
      weight: s.fontWeight, border: parseFloat(s.borderTopWidth) >= 1 && s.borderTopStyle !== 'none', size: parseFloat(s.fontSize), text: (el.innerText || el.value || '').trim().slice(0, 40) }); }
  for (const el of pick('a[href]', 200)) out.links.push(getComputedStyle(el).color);
  for (const el of pick('h1, h2, h3', 30)) { const s = getComputedStyle(el);
    out.headings.push({ tag: el.tagName.toLowerCase(), size: parseFloat(s.fontSize), weight: s.fontWeight,
      tracking: s.letterSpacing, family: s.fontFamily, color: s.color }); }
  for (const el of pick('input:not([type=hidden]):not([type=checkbox]):not([type=radio]), textarea, select', 20)) {
    const s = getComputedStyle(el); out.inputs.push({ h: Math.round(el.getBoundingClientRect().height), radius: parseFloat(s.borderTopLeftRadius) }); }
  const root = getComputedStyle(document.documentElement); const vars = {};
  for (const sheet of [...document.styleSheets]) { let rules; try { rules = sheet.cssRules; } catch (e) { continue; }
    for (const rule of [...rules]) { if (rule.selectorText === ':root' && rule.style) {
      for (const p of [...rule.style]) if (p.startsWith('--')) vars[p] = root.getPropertyValue(p).trim(); } } }
  out.css_vars = vars;
  out.title = document.title;
  return out;
}
"""


def parse_rgb(value: str):
    m = re.match(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)", value or "")
    if not m:
        return None
    r, g, b = (int(float(m.group(i))) for i in (1, 2, 3))
    a = float(m.group(4)) if m.group(4) is not None else 1.0
    return (r, g, b, a)


def to_hex(rgb) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb[:3])


def saturation(rgb) -> float:
    _, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb[:3]))
    return 0.0 if l < 0.08 or l > 0.95 else s


def luminance(rgb) -> float:
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


def first_family(stack: str) -> str:
    return (stack or "").split(",")[0].strip().strip("\"'") or "system-ui"


ACCENT_VAR_ORDER = (
    r"^--(color-)?(brand|primary|accent)(-color)?(-(500|600|base|default))?$",
    r"^--(ss-)?accent$",
    r"^--focus(-ring)?-colou?r$",
    r"(brand|primary|accent)",
)


def css_color_to_hex(value: str):
    v = (value or "").strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{6}|[0-9a-f]{3})", v)
    if m:
        h = m.group(1)
        h = "".join(ch * 2 for ch in h) if len(h) == 3 else h
        return "#" + h.upper()
    rgb = parse_rgb(v)
    return to_hex(rgb) if rgb and rgb[3] > 0.5 else None


def named_accent(css_vars: dict):
    for pattern in ACCENT_VAR_ORDER:
        for name, value in css_vars.items():
            if re.search(pattern, name):
                hx = css_color_to_hex(value)
                if hx and saturation(tuple(int(hx[i:i + 2], 16) for i in (1, 3, 5))) > 0.25:
                    return hx, f"CSS variable {name}"
    return None


def capture(url: str, width: int = 1280, timeout_ms: int = 30000) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        page.evaluate("document.fonts.ready")
        raw = page.evaluate(JS_PROBE)
        browser.close()
    raw["url"] = url
    return raw


def summarise(raw: dict) -> dict:
    """Turn the raw probe into a small, ranked token set."""
    page_bg = parse_rgb(raw.get("page_bg")) or (255, 255, 255, 1)
    if page_bg[3] == 0:
        page_bg = (255, 255, 255, 1)
    dark = luminance(page_bg) < 0.2

    text = Counter()
    for c, n in raw["text"]:
        rgb = parse_rgb(c)
        if rgb and rgb[3] > 0.5:
            text[to_hex(rgb)] += n
    ranked_text = [h for h, _ in text.most_common(12)]
    body_text = ranked_text[0] if ranked_text else ("#FFFFFF" if dark else "#111111")

    def hexrgb(h):
        return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

    # strongest text = highest contrast with the page among common text colours
    strong = max(ranked_text[:6] or [body_text], key=lambda h: contrast(hexrgb(h), page_bg))
    muted = [h for h in ranked_text if h != strong and saturation(hexrgb(h)) < 0.25]
    text_mid = muted[0] if muted else body_text
    text_faint = muted[1] if len(muted) > 1 else text_mid

    surfaces = Counter()
    for c, a in raw["bg"]:
        rgb = parse_rgb(c)
        # surfaces sit close to the page: light near light, dark near dark (skips black buttons, footers)
        if rgb and rgb[3] > 0.6 and saturation(rgb) < 0.2 and abs(luminance(rgb) - luminance(page_bg)) < 0.35:
            surfaces[to_hex(rgb)] += a
    ranked_surf = [h for h, _ in surfaces.most_common(8) if h != to_hex(page_bg)]

    # accent: saturated colour weighted toward buttons and links
    acc = Counter()
    for b in raw["buttons"]:
        for key, w in (("bg", 6), ("color", 1)):
            rgb = parse_rgb(b[key])
            if rgb and rgb[3] > 0.5 and saturation(rgb) > 0.3:
                acc[to_hex(rgb)] += w
    for c in raw["links"]:
        rgb = parse_rgb(c)
        if rgb and saturation(rgb) > 0.3:
            acc[to_hex(rgb)] += 2
    for h, n in text.items():
        if saturation(hexrgb(h)) > 0.35:
            acc[h] += min(n / 200, 3)
    accent = acc.most_common(1)[0][0] if acc else strong
    accent_source = "buttons and links"
    # A named brand variable beats a guess from usage (e.g. Linear: --color-indigo via --focus-ring-color).
    hint = named_accent(raw.get("css_vars", {}))
    if hint:
        accent, accent_source = hint

    # primary button: most common opaque button fill
    fills = Counter(to_hex(parse_rgb(b["bg"])) for b in raw["buttons"]
                    if parse_rgb(b["bg"]) and parse_rgb(b["bg"])[3] > 0.6
                    and to_hex(parse_rgb(b["bg"])) != to_hex(page_bg))
    button_fill = fills.most_common(1)[0][0] if fills else accent

    borders = Counter(to_hex(parse_rgb(c)) for c in raw["borders"] if parse_rgb(c) and parse_rgb(c)[3] > 0.05)
    line = next((h for h, _ in borders.most_common(6) if saturation(hexrgb(h)) < 0.2 and h != strong), None)

    fonts = Counter()
    for stack, n in raw["fonts"]:
        fonts[first_family(stack)] += n
    heading_fonts = Counter(first_family(h["family"]) for h in raw["headings"])
    body_font = fonts.most_common(1)[0][0] if fonts else "system-ui"
    head_font = heading_fonts.most_common(1)[0][0] if heading_fonts else body_font

    radii = Counter(r for r, _ in raw["radii"] if r < 40)
    solid = [b for b in raw["buttons"] if (parse_rgb(b["bg"]) or (0, 0, 0, 0))[3] > 0.05 or b.get("border")]
    btn_r = Counter(round(b["radius"]) for b in (solid or raw["buttons"]))
    btn_h = Counter(b["h"] for b in raw["buttons"] if 24 <= b["h"] <= 64)
    in_h = Counter(i["h"] for i in raw["inputs"] if 24 <= i["h"] <= 64)
    small = sorted(r for r, _ in radii.most_common(6)) or [6, 8, 12]
    button_radius = btn_r.most_common(1)[0][0] if btn_r else small[len(small) // 2]
    pill = button_radius >= 18

    h1 = next((h for h in raw["headings"] if h["tag"] == "h1"), raw["headings"][0] if raw["headings"] else None)

    return {
        "url": raw["url"],
        "title": raw.get("title", ""),
        "theme": "dark" if dark else "light",
        "colors": {
            "page": to_hex(page_bg),
            "surface": ranked_surf[0] if ranked_surf else to_hex(page_bg),
            "surface_alt": ranked_surf[1] if len(ranked_surf) > 1 else (ranked_surf[0] if ranked_surf else to_hex(page_bg)),
            "text_strong": strong,
            "text": text_mid,
            "text_faint": text_faint,
            "line": line or ("#2A2A2E" if dark else "#E5E5EA"),
            "accent": accent,
            "accent_source": accent_source,
            "button": button_fill,
        },
        "contrast": {
            "text_on_page": contrast(hexrgb(strong), page_bg),
            "muted_on_page": contrast(hexrgb(text_mid), page_bg),
            "accent_on_page": contrast(hexrgb(accent), page_bg),
        },
        "type": {
            "body": body_font,
            "heading": head_font,
            "h1_size": h1["size"] if h1 else None,
            "h1_weight": h1["weight"] if h1 else None,
            "h1_tracking": h1["tracking"] if h1 else None,
        },
        "shape": {
            "radius_sm": small[0],
            "radius_md": small[min(1, len(small) - 1)],
            "radius_lg": small[-1],
            "button_radius": 999 if pill else button_radius,
            "pill_buttons": pill,
        },
        "density": {
            "control": (in_h.most_common(1)[0][0] if in_h else (btn_h.most_common(1)[0][0] if btn_h else 36)),
            "button": btn_h.most_common(1)[0][0] if btn_h else None,
        },
        "css_vars_found": len(raw.get("css_vars", {})),
        "css_vars": dict(list(raw.get("css_vars", {}).items())[:60]),
        "counts": {
            "elements_with_text": len(raw["text"]),
            "buttons": len(raw["buttons"]),
            "links": len(raw["links"]),
            "headings": len(raw["headings"]),
        },
    }
