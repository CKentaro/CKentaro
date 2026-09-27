#!/usr/bin/env python3
"""Generate the neofetch-style profile cards (dark_mode.svg / light_mode.svg).

Standard library only, so it runs as-is on GitHub Actions.
Edit INFO below and run `python3 generate.py` to rebuild both SVGs.
"""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
JST = timezone(timedelta(hours=9))

# "Uptime" counts from when I started programming (around July 2022).
UPTIME_SINCE = date(2022, 7, 1)

# Same ramp the ASCII art was generated with: sparse -> dense.
RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

# Layout (px)
PAD = 26
GAP = 30
ART_CELL_W, ART_LINE_H, ART_FONT = 5.8, 11.6, 9.8
INFO_CELL_W, INFO_LINE_H, INFO_FONT = 9.4, 19.5, 15.5
BLANK_H = 10
INFO_COLS = 54

FONT_STACK = ("ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, "
              "'Liberation Mono', 'DejaVu Sans Mono', monospace")

THEMES = {
    "dark": {
        "bg": "#161b22", "border": "#30363d",
        "art1": "#3b3a5a", "art2": "#8d84c7", "art3": "#ebe7ff",
        "text": "#c9d1d9", "dim": "#4d5561",
        "key": "#d2a8ff", "value": "#a5d6ff", "accent": "#f2e56b",
    },
    "light": {
        "bg": "#f6f8fa", "border": "#d0d7de",
        "art1": "#d6d3ea", "art2": "#8b80c4", "art3": "#3f3480",
        "text": "#24292f", "dim": "#b3bcc6",
        "key": "#8250df", "value": "#0a3069", "accent": "#9a6700",
    },
}


def uptime(since: date, today: date) -> str:
    years = today.year - since.year
    months = today.month - since.month
    days = today.day - since.day
    if days < 0:
        months -= 1
        days += (today.replace(day=1) - timedelta(days=1)).day
    if months < 0:
        years -= 1
        months += 12

    def unit(n, word):
        return f"{n} {word}" + ("" if n == 1 else "s")

    return ", ".join([unit(years, "year"), unit(months, "month"), unit(days, "day")])


def build_info(today: date):
    return [
        ("header", "ckentaro", "github"),
        ("kv", "OS", "macOS, iOS"),
        ("kv", "Uptime", uptime(UPTIME_SINCE, today)),
        ("kv", "Host", "Sansan, Inc. (joining Apr 2027)"),
        ("kv", "Role", "Software Engineer, Data Engineer"),
        ("kv", "IDE", "VS Code, Xcode"),
        ("kv", "AI.Tools", "Claude Code"),
        ("kv", "Hobbies", "Weight training, Gaming"),
        ("blank",),
        ("kv", "Languages.Backend", "Python, TypeScript, Ruby, Go"),
        ("kv", "Languages.Real", "Japanese, English (learning)"),
        ("kv", "Cloud", "Google Cloud"),
        ("blank",),
        ("section", "Now"),
        ("kv", "Learning", "Data Engineering on Google Cloud"),
        ("kv", "Studying.For", "GCP Professional Data Engineer"),
        ("blank",),
        ("section", "Contact"),
        ("kv", "Email.Personal", "cliffkentaro.shimada@gmail.com"),
        ("kv", "Email.Work", "cliffkentaro.shimada@sansan.com"),
        ("kv", "LinkedIn", "Cliffkentaro Shimada"),
    ]


def span(cls, s):
    return f'<tspan class="{cls}">{escape(s)}</tspan>'


def info_line(item):
    """Return (tspans, char_count) for one row of the info panel."""
    kind = item[0]
    if kind == "header":
        _, user, host = item
        head = f"{user}@{host} "
        rule = "─" * (INFO_COLS - len(head))
        return (span("accent", user) + span("text", "@") + span("accent", host)
                + span("text", " ") + span("dim", rule)), INFO_COLS
    if kind == "section":
        head = f"- {item[1]} "
        rule = "─" * (INFO_COLS - len(head))
        return span("dim", "- ") + span("text", item[1] + " ") + span("dim", rule), INFO_COLS
    _, key, value = item
    left, right = f". {key}: ", f" {value}"
    dots = "." * max(3, INFO_COLS - len(left) - len(right))
    return (span("dim", ". ") + span("key", key) + span("text", ": ")
            + span("dim", dots) + span("value", right)), len(left) + len(dots) + len(right)


def art_tier(ch):
    i = RAMP.find(ch)
    if i < 0:
        return "art2"
    t = i / (len(RAMP) - 1)
    return "art1" if t < 0.3 else "art2" if t < 0.82 else "art3"


def art_line(line):
    """Group characters into colored runs; spaces join the current run."""
    runs, cls, buf = [], None, ""
    for ch in line:
        c = cls if ch == " " and cls else art_tier(ch)
        if c != cls and buf:
            runs.append(span(cls, buf))
            buf = ""
        cls = c
        buf += ch
    if buf:
        runs.append(span(cls, buf))
    return "".join(runs)


def text_el(cls, x, y, n_chars, cell_w, body):
    return (f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" textLength="{n_chars * cell_w:.1f}" '
            f'lengthAdjust="spacing">{body}</text>')


def render(theme, art, info):
    art_cols = max(len(l) for l in art)
    art_w, art_h = art_cols * ART_CELL_W, len(art) * ART_LINE_H
    heights = [BLANK_H if item[0] == "blank" else INFO_LINE_H for item in info]
    info_w, info_h = INFO_COLS * INFO_CELL_W, sum(heights)
    width = PAD * 2 + art_w + GAP + info_w
    height = PAD * 2 + max(art_h, info_h)

    art_x, art_y = PAD, PAD + (height - PAD * 2 - art_h) / 2
    info_x, info_y = PAD + art_w + GAP, PAD + (height - PAD * 2 - info_h) / 2

    rows = []
    for i, line in enumerate(art):
        if line.strip():
            y = art_y + (i + 0.8) * ART_LINE_H
            rows.append(text_el("art", art_x, y, len(line), ART_CELL_W, art_line(line)))
    y = info_y
    for item, h in zip(info, heights):
        if item[0] != "blank":
            body, n = info_line(item)
            rows.append(text_el("info", info_x, y + 0.75 * h, n, INFO_CELL_W, body))
        y += h

    c = THEMES[theme]
    colors = "\n".join(f".{k}{{fill:{c[k]}}}" for k in
                       ("art1", "art2", "art3", "text", "dim", "key", "value", "accent"))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}" xml:space="preserve">
<style>
text{{font-family:{FONT_STACK};white-space:pre}}
.art{{font-size:{ART_FONT}px}}
.info{{font-size:{INFO_FONT}px}}
{colors}
</style>
<rect x="0.5" y="0.5" width="{width - 1:.0f}" height="{height - 1:.0f}" rx="12" fill="{c['bg']}" stroke="{c['border']}"/>
{chr(10).join(rows)}
</svg>
"""


def main():
    art = [l.rstrip() for l in (ROOT / "ascii_art.txt").read_text(encoding="utf-8").splitlines()]
    info = build_info(datetime.now(JST).date())
    for theme in THEMES:
        (ROOT / f"{theme}_mode.svg").write_text(render(theme, art, info), encoding="utf-8")


if __name__ == "__main__":
    main()
