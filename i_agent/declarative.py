"""Tier 1: the Declarative layer (beliefs and provenance).

Owner: Siddh

- Belief graph: a NetworkX MultiDiGraph. Nodes are entities and values; each edge is one
  belief (subject --predicate--> obj), keyed by "predicate|perspective" so different
  perspectives on the same fact can coexist side by side.
- Provenance log: SQLite. Every write to the graph is logged with the old value, new value,
  source, confidence, time and a reason.
- Snapshots: the epistemic state is a sequence of graphs. snapshot() stores the whole graph
  as JSON with a version number, so any two moments can be compared.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Iterable, Optional

import networkx as nx

from .clock import SimClock
from .schemas import AGENT_PREFIX, MAP, SELF, USER, Belief, ProvenanceRecord

SOURCE_RANK = {"sensor": 3, "agent": 2, "map": 1, "user": 0}
SENSOR_SOURCES = ("lidar", "camera", "sensor", "bumper", "odometry")

# Weighted confidence (v4).
#
# 1. Evidence. Every live sensor reading is evidence about the static map's belief for the same
#    fact. The map's confidence is updated in log-odds by the reading's likelihood ratio
#    r / (1 - r), where r is the sensor's reliability: up if the reading agrees, down if it
#    contradicts. One reading barely moves a confident map; consistent readings move it a lot;
#    a single spike is undone by the readings after it. Only the map is updated: user and other
#    robots' beliefs are other minds' views (Theory of Mind) and are kept as they are.
# 2. Age. When records are compared, each counts with confidence * 0.5 ** (age / half-life),
#    with a half-life that depends on where it came from. The user's beliefs do not decay: they
#    are a record of what the user thinks, not evidence about the world.
SENSOR_RELIABILITY = {"lidar": 0.95, "camera": 0.95, "bumper": 0.99, "odometry": 0.99}
CONFIDENCE_BOUNDS = (0.01, 0.99)   # so a single belief can never become certain or impossible
HALF_LIFE_S = {"sensor": 1800, "agent": 7200, "map": 7 * 86400}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    perspective TEXT NOT NULL,
    old_obj TEXT,
    new_obj TEXT NOT NULL,
    old_confidence REAL,
    new_confidence REAL NOT NULL,
    source TEXT NOT NULL,
    timestamp REAL NOT NULL,
    reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS snapshots (
    version INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    timestamp REAL NOT NULL,
    graph_json TEXT NOT NULL
);
"""


def source_kind(source: str) -> str:
    s = source.lower()
    if any(k in s for k in SENSOR_SOURCES):
        return "sensor"
    if "map" in s:
        return "map"
    if "user" in s:
        return "user"
    return "agent"


def _edge_key(predicate: str, perspective: str) -> str:
    return f"{predicate}|{perspective}"


class BeliefStore:
    def __init__(self, clock: Optional[SimClock] = None, db_path: str = ":memory:"):
        self.clock = clock or SimClock()
        self.graph = nx.MultiDiGraph()
        # check_same_thread=False: the web server builds a session in one thread and runs the agent in
        # another. Access is still one thread at a time (each session has a lock).
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(_SCHEMA)

    # ------------------------------------------------------------------ reads
    def _find_edge(self, subject: str, predicate: str, perspective: str):
        if subject not in self.graph:
            return None
        key = _edge_key(predicate, perspective)
        for _, obj, k, data in self.graph.out_edges(subject, keys=True, data=True):
            if k == key:
                return obj, data
        return None

    def get(self, subject: str, predicate: str, perspective: str = SELF) -> Optional[Belief]:
        found = self._find_edge(subject, predicate, perspective)
        if not found:
            return None
        obj, data = found
        return Belief(subject=subject, predicate=predicate, obj=obj, perspective=perspective,
                      source=data["source"], confidence=data["confidence"], timestamp=data["timestamp"])

    def query(self, subject: Optional[str] = None, predicate: Optional[str] = None,
              perspective: Optional[str] = None) -> list[Belief]:
        results = []
        for s, obj, key, data in self.graph.edges(keys=True, data=True):
            pred, persp = key.split("|", 1)
            if subject and s != subject:
                continue
            if predicate and pred != predicate:
                continue
            if perspective and persp != perspective:
                continue
            results.append(Belief(subject=s, predicate=pred, obj=obj, perspective=persp,
                                  source=data["source"], confidence=data["confidence"],
                                  timestamp=data["timestamp"]))
        return sorted(results, key=lambda b: (b.subject, b.predicate, b.perspective))

    def subjects(self) -> list[str]:
        return sorted({s for s, _, _ in self.graph.edges(keys=True)})

    def get_provenance(self, subject: str, predicate: Optional[str] = None) -> list[ProvenanceRecord]:
        sql = "SELECT * FROM provenance WHERE subject = ?"
        args: list = [subject]
        if predicate:
            sql += " AND predicate = ?"
            args.append(predicate)
        rows = self.db.execute(sql + " ORDER BY id", args).fetchall()
        return [ProvenanceRecord(**dict(r)) for r in rows]

    # ----------------------------------------------------------------- writes
    def _write(self, belief: Belief, reason: str) -> Optional[Belief]:
        """Put a belief in the graph and log it. Returns the belief it replaced, if any."""
        old = self.get(belief.subject, belief.predicate, belief.perspective)
        if old:
            self.graph.remove_edge(belief.subject, old.obj, key=_edge_key(belief.predicate, belief.perspective))
        self.graph.add_edge(belief.subject, belief.obj, key=_edge_key(belief.predicate, belief.perspective),
                            source=belief.source, confidence=belief.confidence, timestamp=belief.timestamp)
        self.db.execute(
            "INSERT INTO provenance (subject, predicate, perspective, old_obj, new_obj, old_confidence,"
            " new_confidence, source, timestamp, reason) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (belief.subject, belief.predicate, belief.perspective, old.obj if old else None, belief.obj,
             old.confidence if old else None, belief.confidence, belief.source, belief.timestamp, reason))
        self.db.commit()
        return old

    def assert_belief(self, belief: Belief, reason: str = "asserted") -> dict:
        """Write a belief. Returns a summary of what changed."""
        old = self._write(belief, reason)
        return {"written": belief.model_dump(), "replaced": old.model_dump() if old else None}

    def update_with_evidence(self, subject: str, predicate: str, observed: str, reliability: float,
                             source: str) -> list[dict]:
        """A live reading observed subject.predicate = observed. Update the static map's belief about
        the same fact by Bayes' rule in log-odds, weighted by the sensor's reliability, and log it.
        Returns the confidence changes."""
        lo, hi = CONFIDENCE_BOUNDS
        ratio = reliability / (1 - reliability)
        changes = []
        for b in self.query(subject, predicate, MAP):
            p = min(hi, max(lo, b.confidence))
            agrees = _same(b.obj, observed)
            odds = p / (1 - p) * (ratio if agrees else 1 / ratio)
            new = round(min(hi, max(lo, odds / (1 + odds))), 3)
            if new == b.confidence:
                continue
            verb = "confirmed" if agrees else "contradicted"
            self._write(b.model_copy(update={"confidence": new}),
                        reason=f"{source} (reliability {reliability}) read {observed}, which {verb} "
                               f"'{b.obj}': confidence {b.confidence} -> {new}")
            changes.append({"subject": b.subject, "predicate": b.predicate, "perspective": MAP, "value": b.obj,
                            "observed": observed, "old_confidence": b.confidence, "new_confidence": new})
        return changes

    def weighted_confidence(self, b: Belief) -> float:
        """Confidence discounted by age, for comparing records: confidence * 0.5 ** (age / half-life)."""
        half_life = _half_life(b)
        if half_life is None:
            return b.confidence
        age = max(0.0, self.clock.now() - b.timestamp)
        return round(b.confidence * 0.5 ** (age / half_life), 3)

    def load(self, beliefs: Iterable[Belief], reason: str = "initial load") -> None:
        for b in beliefs:
            self._write(b, reason)

    # -------------------------------------------------------------- snapshots
    def to_dict(self) -> list[dict]:
        return [b.model_dump() for b in self.query()]

    def snapshot(self, label: str) -> int:
        cur = self.db.execute("INSERT INTO snapshots (label, timestamp, graph_json) VALUES (?,?,?)",
                              (label, self.clock.now(), json.dumps(self.to_dict())))
        self.db.commit()
        return cur.lastrowid

    def get_snapshot(self, version: int) -> list[dict]:
        row = self.db.execute("SELECT graph_json FROM snapshots WHERE version = ?", (version,)).fetchone()
        return json.loads(row["graph_json"]) if row else []

    def diff(self, v_old: int, v_new: int) -> list[str]:
        """Human-readable changes between two snapshots."""
        def index(rows):
            return {(r["subject"], r["predicate"], r["perspective"]): r for r in rows}
        a, b = index(self.get_snapshot(v_old)), index(self.get_snapshot(v_new))
        lines = []
        for k in sorted(set(a) | set(b)):
            before, after = a.get(k), b.get(k)
            label = f"{k[0]}.{k[1]} [{k[2]}]"
            if before is None:
                lines.append(f"+ {label} = {after['obj']} (conf {after['confidence']}, {after['source']})")
            elif after is None:
                lines.append(f"- {label} removed")
            elif (before["obj"], before["confidence"]) != (after["obj"], after["confidence"]):
                lines.append(f"~ {label}: {before['obj']} ({before['confidence']}) -> "
                             f"{after['obj']} ({after['confidence']}, {after['source']})")
        return lines

    def describe(self) -> str:
        rows = self.query()
        if not rows:
            return "(empty)"
        return "\n".join(f"  {b.subject}.{b.predicate} [{b.perspective}] = {b.obj}"
                         f"  (conf {b.confidence}, src {b.source})" for b in rows)


def _same(a: str, b: str) -> bool:
    norm = lambda x: "_".join(str(x).lower().split())
    return norm(a) == norm(b)


def _half_life(b: Belief):
    if b.perspective == USER:
        return None
    if b.perspective == MAP:
        return HALF_LIFE_S["map"]
    if b.perspective.startswith(AGENT_PREFIX):
        return HALF_LIFE_S["agent"]
    # The robot's own beliefs: sensor readings go stale; plans (e.g. mission_plan) do not.
    return HALF_LIFE_S["sensor"] if source_kind(b.source) == "sensor" else None
