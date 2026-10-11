#!/usr/bin/env python3
"""Render results/ as SVG charts for the README (no dependencies).

    python3 visualize.py [results-dir] [out-dir]   # default: results/ -> docs/
"""
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import report

ROOT = Path(__file__).parent
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
# Light palette, then dark. Each chart has its own background, so it reads on any GitHub theme.
STYLE = f"""<style>
  .bg {{ fill: #ffffff; stroke: #d0d7de; }}
  text {{ font-family: {FONT}; font-size: 13px; fill: #57606a; }}
  .ink {{ fill: #1f2328; font-weight: 600; }}
  .mono {{ font-family: {MONO}; font-size: 12px; }}
  .grid {{ stroke: #eaeef2; }}
  .axis {{ stroke: #d0d7de; }}
  .opus {{ fill: #34409a; }} .sonnet {{ fill: #b8691a; }}
  .haiku-medium {{ fill: #7cc4b4; }} .haiku-high {{ fill: #2c9883; }} .haiku-xhigh {{ fill: #11655a; }}
  .miss {{ fill: #cf222e; }}
  .heat {{ fill: #34409a; }}
  @media (prefers-color-scheme: dark) {{
    .bg {{ fill: #0d1117; stroke: #30363d; }}
    text {{ fill: #8d96a0; }} .ink {{ fill: #e6edf3; }}
    .grid {{ stroke: #21262d; }} .axis {{ stroke: #30363d; }}
    .opus {{ fill: #8f9bff; }} .sonnet {{ fill: #e5a24c; }}
    .haiku-medium {{ fill: #2f7b6c; }} .haiku-high {{ fill: #4fb59f; }} .haiku-xhigh {{ fill: #9be3d2; }}
    .miss {{ fill: #ff7b72; }} .heat {{ fill: #8f9bff; }}
  }}
</style>"""


def arm_class(model: str, effort: str) -> str:
    return f"haiku-{effort}" if model == "haiku" else model


def name(a: dict) -> str:
    return f"{a['model'].capitalize()} {a['effort']}"


def svg(w: int, h: int, body: list[str], label: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{label}">{STYLE}<rect class="bg" x="0.5" y="0.5" width="{w - 1}" '
            f'height="{h - 1}" rx="8"/>' + "".join(body) + "</svg>\n")


def build_data(results: Path) -> dict:
    runs = report.load_runs(results, include_smoke=False)
    if not runs:
        sys.exit(f"no finished runs in {results}")
    by_arm = defaultdict(list)
    for r in runs:
        by_arm[r["arm"]].append(r)
    tasks = sorted({t for r in runs for t in r["scores"]})
    arms = []
    for a in sorted(by_arm):
        rs = by_arm[a]
        cfg = rs[0]["config"]
        models = sorted({m for r in rs for m in r["claude"].get("modelUsage", {})})
        arms.append({
            "key": a.upper(), "model": cfg["WORKER_MODEL"], "effort": cfg["WORKER_EFFORT"], "runs": rs,
            "accuracy": statistics.mean(r["accuracy"] * 100 for r in rs),
            "wall": statistics.mean(r["wall_seconds"] / 60 for r in rs),
            "cost": statistics.mean(r["cost"] for r in rs),
            "costByModel": {report.short(m): statistics.mean(
                r["claude"].get("modelUsage", {}).get(m, {}).get("costUSD", 0) for r in rs) for m in models},
            "tasks": {t: {
                "accuracy": statistics.mean(r["scores"][t]["score"] * 100 for r in rs if t in r["scores"]),
                "seconds": statistics.mean(sum(s["seconds"] for s in r["subagents"] if s["task"] == t) for r in rs),
            } for t in tasks},
        })
    return {"arms": arms, "tasks": tasks}


def tradeoff(d: dict) -> str:
    """Cost vs wall time: one small dot per run, a large lettered dot per arm mean, legend on the right."""
    W, H, m = 880, 400, {"l": 60, "r": 290, "t": 24, "b": 52}
    runs = [r for a in d["arms"] for r in a["runs"]]
    x_max = int(max(r["cost"] for r in runs) + 1.5)
    y_max = int((max(r["wall_seconds"] / 60 for r in runs) + 1) // 2 + 1) * 2
    x = lambda v: m["l"] + v / x_max * (W - m["l"] - m["r"])
    y = lambda v: H - m["b"] - v / y_max * (H - m["t"] - m["b"])
    b = []
    for v in range(x_max + 1):
        b += [f'<line class="grid" x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{m["t"]}" y2="{H - m["b"]}"/>',
              f'<text class="mono" x="{x(v):.1f}" y="{H - m["b"] + 18}" text-anchor="middle">${v}</text>']
    for v in range(0, y_max + 1, 2):
        b += [f'<line class="grid" x1="{m["l"]}" x2="{W - m["r"]}" y1="{y(v):.1f}" y2="{y(v):.1f}"/>',
              f'<text class="mono" x="{m["l"] - 8}" y="{y(v) + 4:.1f}" text-anchor="end">{v}</text>']
    cy = (m["t"] + H - m["b"]) / 2
    b += [f'<text x="{(m["l"] + W - m["r"]) / 2}" y="{H - 12}" text-anchor="middle">cost per run (API-equivalent $) →</text>',
          f'<text x="18" y="{cy}" text-anchor="middle" transform="rotate(-90 18 {cy})">wall time (min) →</text>',
          f'<text x="{m["l"] + 8}" y="{m["t"] + 16}">↙ cheaper and faster</text>']
    for a in d["arms"]:
        c = arm_class(a["model"], a["effort"])
        b += [f'<circle class="{c}" cx="{x(r["cost"]):.1f}" cy="{y(r["wall_seconds"] / 60):.1f}" r="4.5" fill-opacity="0.45"/>'
              for r in a["runs"]]
        b += [f'<circle class="{c}" cx="{x(a["cost"]):.1f}" cy="{y(a["wall"]):.1f}" r="11"/>',
              f'<text class="ink" x="{x(a["cost"]) + 15:.1f}" y="{y(a["wall"]) + 5:.1f}">{a["key"]}</text>']
    lx = W - m["r"] + 24
    b.append(f'<text class="ink" x="{lx}" y="{m["t"] + 16}">Worker · accuracy</text>')
    for i, a in enumerate(d["arms"]):
        ly = m["t"] + 50 + i * 46
        b += [f'<circle class="{arm_class(a["model"], a["effort"])}" cx="{lx + 8}" cy="{ly - 4}" r="8"/>',
              f'<text class="ink" x="{lx + 24}" y="{ly}">{a["key"]} · {name(a)}</text>',
              f'<text class="mono" x="{lx + 24}" y="{ly + 18}">{a["accuracy"]:.1f}% · ${a["cost"]:.2f} · {a["wall"]:.1f} min</text>']
    b.append(f'<text class="mono" x="{lx}" y="{H - 30}">small dots: single runs</text>')
    b.append(f'<text class="mono" x="{lx}" y="{H - 12}">large dots: mean of 3</text>')
    return svg(W, H, b, "Cost versus wall time per setup")


def cost(d: dict) -> str:
    """Stacked cost per run by model; Opus first because it is the boss in every arm."""
    row, m = 44, {"l": 190, "r": 80, "t": 20, "b": 64}
    W, H = 820, m["t"] + m["b"] + row * len(d["arms"])
    totals = [sum(a["costByModel"].values()) for a in d["arms"]]
    x_max = int(max(totals)) + 1
    x = lambda v: m["l"] + v / x_max * (W - m["l"] - m["r"])
    b = []
    for v in range(x_max + 1):
        b += [f'<line class="grid" x1="{x(v):.1f}" x2="{x(v):.1f}" y1="{m["t"]}" y2="{H - m["b"]}"/>',
              f'<text class="mono" x="{x(v):.1f}" y="{H - m["b"] + 18}" text-anchor="middle">${v}</text>']
    for i, a in enumerate(d["arms"]):
        y0 = m["t"] + i * row + 8
        b.append(f'<text class="ink" x="{m["l"] - 12}" y="{y0 + 18}" text-anchor="end">{a["key"]} · {name(a)} workers</text>')
        acc = 0.0
        parts = sorted(((k, v) for k, v in a["costByModel"].items() if v > 0.005), key=lambda kv: not kv[0].startswith("opus"))
        for k, v in parts:
            fam = k.split("-")[0]
            c = arm_class(a["model"], a["effort"]) if fam == a["model"] else arm_class(fam, "high")
            b.append(f'<rect class="{c}" x="{x(acc):.1f}" y="{y0}" width="{x(acc + v) - x(acc):.1f}" height="26" rx="3"/>')
            acc += v
        b.append(f'<text class="mono" x="{x(acc) + 8:.1f}" y="{y0 + 18}">${acc:.2f}</text>')
    ly, lx = H - 22, m["l"]
    for c, label in [("opus", "Opus (boss; also the workers in A)"), ("haiku-high", "Haiku workers"),
                     ("sonnet", "Sonnet workers")]:
        b += [f'<rect class="{c}" x="{lx}" y="{ly - 11}" width="12" height="12" rx="2"/>',
              f'<text x="{lx + 18}" y="{ly}">{label}</text>']
        lx += 18 + len(label) * 7.5 + 28  # shortcut: estimated text width, fine for these fixed labels
    return svg(W, H, b, "Cost per run by model")


def tasks(d: dict) -> str:
    """Worker time per task and arm; a red dot marks a task where the arm lost points."""
    row, col, m = 30, 112, {"l": 200, "t": 56, "b": 40}
    W, H = m["l"] + col * len(d["arms"]) + 20, m["t"] + m["b"] + row * len(d["tasks"])
    secs = [a["tasks"][t]["seconds"] for a in d["arms"] for t in d["tasks"]]
    lo, hi = min(secs), max(secs)
    b = []
    for j, a in enumerate(d["arms"]):
        cx = m["l"] + j * col + col / 2
        b += [f'<text class="ink" x="{cx}" y="{m["t"] - 28}" text-anchor="middle">{a["key"]}</text>',
              f'<text x="{cx}" y="{m["t"] - 10}" text-anchor="middle">{name(a)}</text>']
    for i, t in enumerate(d["tasks"]):
        y0 = m["t"] + i * row
        b.append(f'<text class="ink" x="16" y="{y0 + 20}">{t}</text>')
        for j, a in enumerate(d["arms"]):
            v = a["tasks"][t]["seconds"]
            x0 = m["l"] + j * col
            b += [f'<rect class="heat" x="{x0 + 2}" y="{y0 + 2}" width="{col - 4}" height="{row - 4}" rx="3" '
                  f'fill-opacity="{0.06 + 0.6 * (v - lo) / (hi - lo or 1):.2f}"/>',
                  f'<text class="mono" x="{x0 + col / 2}" y="{y0 + 19}" text-anchor="middle">{v:.0f}s</text>']
            if a["tasks"][t]["accuracy"] < 99.95:
                b.append(f'<circle class="miss" cx="{x0 + col - 12}" cy="{y0 + 10}" r="4"/>')
    ly = H - 14
    b += [f'<text x="16" y="{ly}">Mean worker time per task (s), darker = slower.</text>',
          f'<circle class="miss" cx="{W - 236}" cy="{ly - 4}" r="4"/>',
          f'<text x="{W - 226}" y="{ly}">lost points in at least one run</text>']
    return svg(W, H, b, "Worker time per task and setup")


def main() -> None:
    args = sys.argv[1:]
    results = Path(args[0]) if args else ROOT / "results"
    out = Path(args[1]) if len(args) > 1 else ROOT / "docs"
    out.mkdir(parents=True, exist_ok=True)
    d = build_data(results)
    for fname, render in [("tradeoff.svg", tradeoff), ("cost.svg", cost), ("tasks.svg", tasks)]:
        (out / fname).write_text(render(d))
        print(f"wrote {out / fname}")


if __name__ == "__main__":
    main()
