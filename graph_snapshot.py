"""Draw the belief graph before and after a run, from its log.

    python graph_snapshot.py logs/<run folder>/A1_route_blocked_run1.json [out.png]

"Before" is the scenario's starting memory; "after" is the final_beliefs saved in the run log.
Grey edges are map beliefs, teal edges the robot's own, other perspectives indigo/amber.
A belief whose confidence dropped is drawn dashed; a new belief is drawn thick.

Owner: Siddh
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402

from i_agent.scenario import load_scenario  # noqa: E402

COLOR = {"map": "#7C8794", "self": "#0B7A70", "user": "#3A4AA6"}
AGENT = "#A95A0B"


def layered_layout(beliefs: list[dict]) -> dict:
    """Left-to-right columns by distance from the graph's sources (e.g. robot -> route_A -> values)."""
    g = nx.DiGraph()
    for b in beliefs:
        g.add_edge(b["subject"], b["obj"])
    depth = {}
    for n in nx.topological_sort(g) if nx.is_directed_acyclic_graph(g) else g.nodes:
        preds = list(g.predecessors(n))
        depth[n] = 1 + max((depth.get(p, 0) for p in preds), default=-1)
    cols: dict[int, list] = {}
    for n, d in depth.items():
        cols.setdefault(d, []).append(n)
    pos = {}
    for d, ns in cols.items():
        for i, n in enumerate(ns):
            pos[n] = (d, (len(ns) - 1) / 2 - i)
    return pos


def key(b: dict) -> tuple:
    return b["subject"], b["predicate"], b["perspective"]


def draw(ax, beliefs: list[dict], before: dict, title: str, pos: dict, lim: tuple) -> None:
    g = nx.MultiDiGraph()
    for b in beliefs:
        g.add_edge(b["subject"], b["obj"], **b)
    ax.set_title(title, fontsize=11, fontweight="bold", color="#16202B", loc="left", pad=2)
    entities = {b["subject"] for b in beliefs}
    leaves = {n for n in g.nodes if g.out_degree(n) == 0}
    for n in g.nodes:
        ax.text(*pos[n], n, ha="center", va="center", fontsize=11, fontweight="bold", color="#16202B", zorder=3,
                bbox=dict(boxstyle="round,pad=0.45", fc="#EEF1F5" if n in entities else "white", ec="#9AA6B4", lw=1.2))
    for u, v, b in g.edges(data=True):
        old = before.get(key(b))
        new = old is None and bool(before)        # a belief that did not exist before this run
        dropped = old is not None and b["confidence"] < old["confidence"]
        color = COLOR.get(b["perspective"], AGENT)
        ax.annotate("", xy=pos[v], xytext=pos[u], zorder=2,
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=3.2 if new else 1.8, alpha=0.6 if dropped else 1,
                                    linestyle=(0, (4, 3)) if dropped else "-", shrinkA=26, shrinkB=30, mutation_scale=14))
        conf = f"{old['confidence']:g} → {b['confidence']:g}" if dropped else f"{b['confidence']:g}"
        label = f"{b['predicate']} [{b['perspective']}]\nconf {conf}\n{b['source']}"
        style = dict(fontsize=10, color=color, fontweight="bold" if new else "normal", linespacing=1.2, zorder=4)
        if v in leaves:      # label beside the value it points to
            ax.text(pos[v][0] + 0.25 + 0.09 * len(v), pos[v][1], label, ha="left", va="center", **style)
        else:                # label above the arrow
            ax.text((pos[u][0] + pos[v][0]) / 2, pos[u][1] + 0.28, label, ha="center", va="bottom", **style)
    ax.set_xlim(*lim[0])
    ax.set_ylim(*lim[1])
    ax.set_axis_off()


def main() -> None:
    log = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else log.with_suffix(".png")
    rec = json.loads(log.read_text(encoding="utf-8"))
    scenario = load_scenario(rec["scenario"].split("_")[0])
    start = [{**m, "perspective": m.get("perspective", "self"), "confidence": m.get("confidence", 1.0)}
             for m in scenario["memory"]]
    end = rec["final_beliefs"]
    before = {key(b): b for b in start}

    pos = {n: (x * 1.75, y * 1.25) for n, (x, y) in layered_layout(start + end).items()}
    xs, ys = [p[0] for p in pos.values()], [p[1] for p in pos.values()]
    lim = ((min(xs) - 0.75, max(xs) + 1.75), (min(ys) - 0.5, max(ys) + 0.6))

    fig, axes = plt.subplots(1, 2, figsize=(7.3, 2.15), dpi=300)
    draw(axes[0], start, {}, "Before: starting memory", pos, lim)
    draw(axes[1], end, before, "After: saved at end of run", pos, lim)
    fig.tight_layout(w_pad=0.6, pad=0.2)
    fig.savefig(out, facecolor="white", bbox_inches="tight", pad_inches=0.05)
    print("wrote", out)


if __name__ == "__main__":
    main()
