# Brand Look

**Make your AI agent design in your brand, not in generic AI grey.**

**New to this?** Get the step-by-step setup and the copy-paste AI prompt at [jamesrowdy.com/tools/brand-look](https://jamesrowdy.com/tools/brand-look/?utm_source=github&utm_medium=readme&utm_campaign=brand-look).

Ask an AI agent for a landing page or an app screen and you get the same look every time: grey cards, purple buttons, a sparkle icon. It doesn't know your brand, so it guesses.

Brand Look fixes the guess. Give it any website. It opens the site in a real browser, reads the colours, fonts, corners and button sizes the site actually uses, and saves them as files your agent follows.

1. **Point it at a site.** Yours, or one whose look you like.
2. **It reads the real values.** Computed styles from the live page, plus the site's own CSS variables when it has them. No screenshots, no guessing from a picture.
3. **Your agent uses them.** Drop `LOOK.md` into your project and every page or mockup it builds uses your colours, your font and your corners.

No account, no API key, no cost.

## What you actually get

Real runs, 2 Nov 2026, about 3 to 10 seconds each:

| Site | Theme | Accent | Text | Font | Buttons |
|---|---|---|---|---|---|
| jamesrowdy.com | light | `#0066CC` | `#1D1D1F` | Inter | pill |
| stripe.com | light | `#533AFD` | `#061B31` | sohne-var | 4px |
| linear.app | dark | `#5E69D1` | `#F7F8F8` | Inter Variable | 16px |
| airbnb.com | light | `#FF385C` | `#222222` | Airbnb Cereal VF | 8px |
| notion.com | light | `#0075DE` | `#000000` | NotionInter | 8px |

```
$ brand-look jamesrowdy.com
{
  "site": "https://jamesrowdy.com",
  "theme": "light",
  "accent": "#0066CC",
  "text": "#1D1D1F",
  "font": "Inter",
  "buttons": "pill",
  "seconds": 3.2,
  "files": ["looks/jamesrowdy/LOOK.md", "looks/jamesrowdy/look.css", ...]
}
```

Each run writes five files to `looks/<site>/`:

| File | What it's for |
|---|---|
| `LOOK.md` | The brief your agent reads: every token, its contrast score, and the rules |
| `look.css` | CSS variables. Uses Stageshow's token names, works in any project |
| `tailwind.config.js` | The same values for Tailwind |
| `look.json` | The raw numbers |
| `preview.html` | A sample card in the look, to check it at a glance |

## Install

```sh
git clone https://github.com/jamesrowdyy/brand-look
cd brand-look
python3 -m venv .venv && .venv/bin/pip install -e .
.venv/bin/playwright install chromium   # skip if you have Google Chrome
.venv/bin/brand-look yoursite.com
```

## Use it with your agent

Copy `looks/<site>/LOOK.md` into your project and tell your agent:

> Read LOOK.md. Use only those colours, fonts and corner sizes for every UI you build.

Works with Claude Code, Codex, Cursor, Gemini and Hermes Agent.

### Pairs well with Stageshow

[Stageshow](https://github.com/benjitaylor/skills/tree/main/stageshow) by Benji Taylor is a free agent skill that makes product UI mockups look production-grade. Its looks are a set of `--ss-*` CSS variables. `look.css` uses the same names, so you can load it straight in:

```tsx
<Stage className="look-yoursite" theme="light">
```

Brand Look is a separate project and is not affiliated with Stageshow.

## How it decides

- **Accent**: a named brand variable in the site's CSS first (`--brand`, `--primary`, `--accent`, the focus ring colour). If there is none, the most-used saturated colour on buttons and links.
- **Text**: the three most-used text colours, ranked by how much text uses them, with contrast against the page.
- **Surfaces**: the largest background colours close to the page colour.
- **Font**: the family covering the most text, and the heading font separately.
- **Corners and sizes**: the most common radius and height on real, visible buttons and inputs.

## Limits

- It reads one page (the URL you give it). A homepage can differ from the app.
- Sites that block headless browsers return little or nothing.
- Fonts are named, not downloaded. Use the font under its own licence.
- Read colours from a site you own or have permission to imitate. Copying another brand's look for your own product can confuse customers.

## Licence

MIT
