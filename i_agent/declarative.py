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
from .schemas import MAP, SELF, Belief, ProvenanceRecord

# Conflict rule: when the agent's own belief is updated from a source of this kind, any
# disagreeing belief held by a *lower* ranked perspective is downgraded. Only the static map is
# ever downgraded automatically: user and third-party beliefs are other minds' views, which the
# agent must keep (Theory of Mind), not overwrite.
SOURCE_RANK = {"sensor": 3, "agent": 2, "map": 1, "user": 0}
SENSOR_SOURCES = ("lidar", "camera", "sensor", "bumper")
MAP_DOWNGRADE_FACTOR = 0.3

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
        self.db = sqlite3.connect(db_path)
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
        """Write a belief and apply the conflict rule. Returns a summary of what changed."""
        old = self._write(belief, reason)
        downgraded = []
        if belief.perspective == SELF:
            downgraded = self._apply_conflict_rule(belief)
        return {
            "written": belief.model_dump(),
            "replaced": old.model_dump() if old else None,
            "downgraded": downgraded,
        }

    def _apply_conflict_rule(self, new: Belief) -> list[dict]:
        new_rank = SOURCE_RANK[source_kind(new.source)]
        changed = []
        for other in self.query(new.subject, new.predicate, MAP):
            if other.obj == new.obj or SOURCE_RANK["map"] >= new_rank:
                continue
            lowered = round(other.confidence * MAP_DOWNGRADE_FACTOR, 3)
            self._write(other.model_copy(update={"confidence": lowered}),
                        reason=f"contradicted by {new.source} ({new.obj}); map confidence downgraded")
            changed.append({"subject": other.subject, "predicate": other.predicate, "perspective": MAP,
                            "value": other.obj, "old_confidence": other.confidence, "new_confidence": lowered})
        return changed

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
