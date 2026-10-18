"""Combine every evaluation run in logs/ into one results report.

    python report.py

Writes results/results.md (tables), results/results.html (tables + ablation chart) and
results/review.html (a sheet for checking the automatic verdicts by hand).

Runs are grouped by (system version, scenario set, level, model, temperature); runs from several
log folders with the same group are pooled. Results of different system versions are never pooled
(see SYSTEM_VERSION in i_agent/__init__.py). logs/dev_iterations/ (development history) is ignored.

"Correct answer" = every answer check of the run passed. This is the fair comparison across
levels, since levels without memory tools cannot pass the tool or memory checks.
"All checks" = the run passed every check (answer, tools, memory, grounding).

Owner: Udit
"""
from __future__ import annotations

import html
import json
import math
import re
from collections import defaultdict
from pathlib import Path

LOGS = Path("logs")
OUT = Path("results")
LEVEL_ORDER = ["baseline", "sensors", "plain", "checks", "full"]
LEVEL_LABEL = {
    "baseline": "No tools (memory as text)",
    "sensors": "Sensor tools, no memory layer",
    "plain": "+ Memory layer, no safeguards",
    "checks": "+ Tool-layer checks",
    "full": "+ Self-check (full system)",
}
OLD_MODES = {"agent": "full", "agent-no-self-check": "checks"}
# Logs written before the version field existed: folders from this time on ran v2.
V2_SINCE = "20261018-200000"
SET_ORDER = ["dev", "heldout", "heldout2"]
SET_LABEL = {"dev": "Dev set (system was tuned on it)",
             "heldout": "Held-out set 1 (frozen 5 Oct; its v1 results were seen before v2)",
             "heldout2": "Held-out set 2 (frozen 18 Oct before any run)"}
SET_COLOUR = {"dev": "dev", "heldout": "held", "heldout2": "held2"}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def load_runs() -> list[dict]:
    runs = []
    for folder in sorted(LOGS.glob("2*")):
        if not folder.is_dir():
            continue
        temp = float(m.group(1)) if (m := re.search(r"_t([0-9.]+)$", folder.name)) else 0.0
        for f in sorted(folder.glob("*_run*.json")):
            rec = json.loads(f.read_text(encoding="utf-8"))
            rec["level"] = OLD_MODES.get(rec.get("mode"), rec.get("mode"))
            rec["set"] = rec.get("set") or "dev"
            rec["system"] = rec.get("system") or ("v2" if folder.name >= V2_SINCE else "v1")
            rec["temperature"] = temp
            rec["folder"] = folder.name
            rec["file"] = f.name
            checks = rec.get("checks", [])
            answer_checks = [c for c in checks if c["kind"] == "answer"]
            rec["answer_ok"] = bool(answer_checks) and all(c["passed"] for c in answer_checks)
            rec["errored"] = "error" in rec
            if rec["level"]:
                runs.append(rec)
    return runs


def group(runs: list[dict]) -> dict[tuple, list[dict]]:
    g: dict[tuple, list[dict]] = defaultdict(list)
    for r in runs:
        g[(r["system"], r["set"], r["level"], r.get("model", "?"), r["temperature"])].append(r)
    return g


def fmt_rate(k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({100 * k / n:.0f}%, 95% CI {100 * lo:.0f}–{100 * hi:.0f}%)" if n else "-"


def summary_rows(groups) -> list[dict]:
    rows = []
    for (system, set_name, level, model, temp), rs in groups.items():
        valid = [r for r in rs if not r["errored"]]
        n = len(valid)
        if not n:
            continue
        rows.append({"system": system, "set": set_name, "level": level, "model": model, "temperature": temp,
                     "runs": n, "errors": len(rs) - n,
                     "answer_k": sum(r["answer_ok"] for r in valid),
                     "all_k": sum(r["passed"] for r in valid),
                     "scenarios": len({r["scenario"] for r in valid})})
    key = lambda r: (r["model"], r["system"], r["temperature"], SET_ORDER.index(r["set"]),
                     LEVEL_ORDER.index(r["level"]) if r["level"] in LEVEL_ORDER else 99)
    return sorted(rows, key=key)


def per_scenario(groups, model: str, temp: float) -> dict[str, dict[str, str]]:
    """{(set, scenario): {"<level> <system>": "k/n"}}"""
    table: dict[str, dict[str, str]] = defaultdict(dict)
    for (system, set_name, level, m, t), rs in groups.items():
        if m != model or t != temp:
            continue
        by_s = defaultdict(list)
        for r in rs:
            if not r["errored"]:
                by_s[r["scenario"]].append(r)
        for s, lst in by_s.items():
            table[(set_name, s)][f"{level} {system}"] = f"{sum(r['answer_ok'] for r in lst)}/{len(lst)}"
    return table


def chart_groups(rows: list[dict], model: str) -> list[tuple[str, str]]:
    """(system, level) pairs with results for the model at temperature 0, in ladder order."""
    have = {(r["system"], r["level"]) for r in rows if r["model"] == model and r["temperature"] == 0}
    return [(sy, lv) for sy in sorted({sy for sy, _ in have}) for lv in LEVEL_ORDER if (sy, lv) in have]


def bar_chart(rows: list[dict], model: str) -> str:
    """Correct-answer rate per (system, level) and scenario set, temperature 0, with 95% CI whiskers."""
    data = {(r["system"], r["set"], r["level"]): r for r in rows
            if r["model"] == model and r["temperature"] == 0 and r["runs"]}
    groups = chart_groups(rows, model)
    if not groups:
        return ""
    sets = [s for s in SET_ORDER if any(k[1] == s for k in data)]
    w, h, left, top, bottom = 900, 340, 56, 24, 96
    plot_h = h - top - bottom
    group_w = (w - left - 16) / len(groups)
    bar_w = min(30, (group_w - 10) / len(sets))
    y = lambda v: top + plot_h * (1 - v)
    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Correct answer rate by level" '
             f'style="width:100%;height:auto;max-width:{w}px">']
    for t in (0, .25, .5, .75, 1):
        parts.append(f'<line x1="{left}" x2="{w - 8}" y1="{y(t):.1f}" y2="{y(t):.1f}" class="grid"/>'
                     f'<text x="{left - 8}" y="{y(t) + 4:.1f}" text-anchor="end" class="axis">{int(t * 100)}%</text>')
    for i, (system, lv) in enumerate(groups):
        cx = left + group_w * (i + .5)
        x0 = cx - bar_w * len(sets) / 2
        for j, set_name in enumerate(sets):
            r = data.get((system, set_name, lv))
            if not r:
                continue
            x = x0 + j * bar_w
            p = r["answer_k"] / r["runs"]
            lo, hi = wilson(r["answer_k"], r["runs"])
            parts.append(f'<rect x="{x + 1:.1f}" y="{y(p):.1f}" width="{bar_w - 2:.1f}" height="{plot_h * p:.1f}" '
                         f'class="{set_name}"><title>{system} · {set_name} · {LEVEL_LABEL[lv]}: '
                         f'{r["answer_k"]}/{r["runs"]}</title></rect>'
                         f'<line x1="{x + bar_w / 2:.1f}" x2="{x + bar_w / 2:.1f}" y1="{y(lo):.1f}" y2="{y(hi):.1f}" class="ci"/>'
                         f'<text x="{x + bar_w / 2:.1f}" y="{y(p) - 6:.1f}" text-anchor="middle" class="val">{100 * p:.0f}</text>')
        words = (system + " · " + LEVEL_LABEL[lv]).split(" ")
        lines, cur = [], ""
        for wd in words:
            if len(cur) + len(wd) > 14:
                lines.append(cur.strip())
                cur = ""
            cur += wd + " "
        lines.append(cur.strip())
        for k, ln in enumerate(lines[:4]):
            parts.append(f'<text x="{cx:.1f}" y="{h - bottom + 18 + 14 * k}" text-anchor="middle" '
                         f'class="axis">{html.escape(ln)}</text>')
    parts.append("</svg>")
    return "".join(parts)


CSS = """
:root{--bg:#F4F6F8;--surface:#fff;--ink:#16202B;--muted:#586473;--line:#D9DFE6;--soft:#EAEEF2;--dev:#0B7A70;--held:#A95A0B;--held2:#5B4FC4;--ok:#1E7B3A;--bad:#B3261E}
@media (prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#0F151C;--surface:#161E27;--ink:#E4E9EF;--muted:#9AA6B4;--line:#2A3542;--soft:#1C2530;--dev:#5CCFC2;--held:#F0AE62;--held2:#A99CF5;--ok:#7FD69A;--bad:#F28B82}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,"Segoe UI",sans-serif;padding:32px 16px 60px}
main{max-width:980px;margin:0 auto}h1{font-size:28px;margin:0 0 6px}h2{font-size:19px;margin:30px 0 10px}p{max-width:75ch}
.muted{color:var(--muted)}.tbl{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:13.5px;font-variant-numeric:tabular-nums}th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--soft);font-weight:600}tr:last-child td{border-bottom:0}
.chart{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px}
.grid{stroke:var(--line)}.axis{fill:var(--muted);font-size:11.5px}.val{fill:var(--ink);font-size:11px}
.dev{fill:var(--dev)}.heldout{fill:var(--held)}.heldout2{fill:var(--held2)}.ci{stroke:var(--ink);stroke-width:1.4;opacity:.6}
.legend{display:flex;gap:16px;font-size:13px;margin:6px 0 0}.legend span::before{content:"";display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:6px;vertical-align:-1px;background:var(--c)}
.ok{color:var(--ok);font-weight:600}.bad{color:var(--bad);font-weight:600}
.ans{max-width:460px;white-space:pre-wrap}
"""


def main() -> None:
    runs = load_runs()
    if not runs:
        print("no runs in logs/")
        return
    groups = group(runs)
    rows = summary_rows(groups)
    OUT.mkdir(exist_ok=True)
    main_model = max({r["model"] for r in rows}, key=lambda m: sum(x["runs"] for x in rows if x["model"] == m))

    md = ["# I, Agent: evaluation results", "",
          "Correct answer = every answer check passed (the fair comparison across levels).",
          "All checks = answer, tools, memory and grounding checks all passed.", "",
          "| System | Set | Level | Model | Temp | Runs | Correct answer | All checks | Errors |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['system']} | {r['set']} | {r['level']} | {r['model']} | {r['temperature']:g} | {r['runs']} | "
                  f"{fmt_rate(r['answer_k'], r['runs'])} | {fmt_rate(r['all_k'], r['runs'])} | {r['errors']} |")
    md += ["", f"## Correct answers per scenario ({main_model}, temperature 0)", ""]
    table = per_scenario(groups, main_model, 0.0)
    cols = [f"{lv} {sy}" for sy, lv in chart_groups(rows, main_model)]
    scen_header = "| Set | Scenario | " + " | ".join(cols) + " |"
    md.append(scen_header)
    md.append("|---|---|" + "---|" * len(cols))
    for (set_name, s) in sorted(table, key=lambda k: (SET_ORDER.index(k[0]), k[1])):
        md.append(f"| {set_name} | {s} | " + " | ".join(table[(set_name, s)].get(c, "-") for c in cols) + " |")
    (OUT / "results.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    def table_html(lines: list[str]) -> str:
        head = [c.strip() for c in lines[0].strip("|").split("|")]
        body = [[c.strip() for c in ln.strip("|").split("|")] for ln in lines[2:]]
        return ('<div class="tbl"><table><thead><tr>' + "".join(f"<th>{html.escape(c)}</th>" for c in head) +
                "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>"
                                                 for r in body) + "</tbody></table></div>")

    summary_lines = md[5:5 + len(rows) + 2]
    scen_start = md.index(scen_header)
    legend = "".join(f'<span style="--c:var(--{SET_COLOUR[s]})">{html.escape(SET_LABEL[s])}</span>'
                     for s in SET_ORDER if any(r["set"] == s for r in rows))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>I, Agent Results</title><style>{CSS}</style></head><body><main>
<h1>I, Agent: evaluation results</h1>
<p class="muted">Generated by <code>report.py</code> from every run in <code>logs/</code>. Ranges are 95% Wilson confidence intervals over runs.</p>
<h2>What each part of the architecture adds ({html.escape(main_model)}, temperature 0)</h2>
<div class="chart">{bar_chart(rows, main_model)}
<div class="legend">{legend}</div></div>
<p>Bars show the share of runs whose final answer passed every answer check. Each level adds one part of the architecture to the one on its left. v1 is the mid-semester system and v2 the current one; their results are never pooled.</p>
<h2>All groups</h2>{table_html(summary_lines)}
<h2>Correct answers per scenario</h2>{table_html(md[scen_start:])}
<p class="muted">Check the automatic verdicts by hand in <a href="review.html">review.html</a>.</p>
</main></body></html>"""
    (OUT / "results.html").write_text(page, encoding="utf-8")

    # Spot-check sheet: first run of each scenario for the main model at temperature 0, full and plain levels.
    latest = max(r["system"] for r in runs)
    seen, items = set(), []
    for r in sorted(runs, key=lambda r: (r["set"] != "dev", r["scenario"], LEVEL_ORDER.index(r["level"])
                                          if r["level"] in LEVEL_ORDER else 9, r["file"])):
        key = (r["set"], r["scenario"], r["level"])
        if r["system"] != latest or r["errored"] or r["model"] != main_model or r["temperature"] != 0 or r["level"] not in ("full", "plain") \
                or key in seen:
            continue
        seen.add(key)
        items.append(r)
    rows_html = []
    for i, r in enumerate(items):
        verdict = '<span class="ok">correct</span>' if r["answer_ok"] else '<span class="bad">wrong</span>'
        q = r["turns"][-1]["question"] if r.get("turns") else ""
        a = r["turns"][-1]["answer"] if r.get("turns") else ""
        rows_html.append(f'<tr><td>{r["set"]}<br>{html.escape(r["scenario"])}<br><span class="muted">{r["level"]} {r["system"]}</span></td>'
                         f'<td class="ans">{html.escape(q)}</td><td class="ans">{html.escape(a)}</td><td>{verdict}</td>'
                         f'<td><select id="h{i}" aria-label="Your verdict"><option value="">–</option>'
                         f'<option value="agree">agree</option><option value="disagree">disagree</option></select></td></tr>')
    review = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>I, Agent Answer Review</title><style>{CSS}</style></head><body><main>
<h1>Check the automatic verdicts by hand</h1>
<p>For each answer, decide whether it really answers the question correctly, then mark whether you <strong>agree</strong> with the automatic verdict. The counter shows how often the keyword checks match human judgement. Choices are saved in this browser only.</p>
<p><strong id="score">0 reviewed</strong></p>
<div class="tbl"><table><thead><tr><th>Scenario</th><th>Question</th><th>Agent's answer</th><th>Automatic</th><th>You</th></tr></thead>
<tbody>{''.join(rows_html)}</tbody></table></div></main>
<script>
var sels=document.querySelectorAll('select');
function upd(){{var n=0,a=0;sels.forEach(function(s){{if(s.value){{n++;if(s.value==='agree')a++;}}}});
document.getElementById('score').textContent=n+' reviewed · agreement '+(n?Math.round(100*a/n):0)+'% ('+a+'/'+n+')';}}
sels.forEach(function(s){{try{{var v=localStorage.getItem('iagent-review-'+s.id);if(v)s.value=v;}}catch(e){{}}
s.addEventListener('change',function(){{try{{localStorage.setItem('iagent-review-'+s.id,s.value);}}catch(e){{}}upd();}});}});upd();
</script></body></html>"""
    (OUT / "review.html").write_text(review, encoding="utf-8")
    print("\n".join(md[:5 + len(rows) + 2]))
    print(f"\nwrote {OUT / 'results.md'}, {OUT / 'results.html'}, {OUT / 'review.html'}")


if __name__ == "__main__":
    main()
