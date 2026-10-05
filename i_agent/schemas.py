"""Shared data contracts between the three layers.

Owned by the whole team: change this file only after agreeing as a group.
Every value that crosses a layer boundary is one of these models, serialised to JSON.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

# Perspectives a belief can belong to.
#   "self"         what the agent itself currently believes / perceives (egocentric)
#   "map"          the static baseline layout file (historical abstraction)
#   "user"         what the human user believes or has said
#   "agent:<id>"   a report logged by another agent, e.g. "agent:bot_02"
SELF = "self"
MAP = "map"
USER = "user"
AGENT_PREFIX = "agent:"


def agent_perspective(agent_id: str) -> str:
    return f"{AGENT_PREFIX}{agent_id}"


class Belief(BaseModel):
    """One edge of the belief graph: (subject) --predicate--> (obj)."""

    subject: str = Field(description="Entity the belief is about, e.g. 'route_A', 'box_01'")
    predicate: str = Field(description="Property or relation, e.g. 'status', 'color', 'located_at'")
    obj: str = Field(description="Value, e.g. 'clear', 'blue', 'Room_101'")
    perspective: str = Field(default=SELF, description="Whose belief this is")
    source: str = Field(description="Where it came from, e.g. 'Default_Map', 'lidar_front', 'bot_02_log'")
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: float = Field(description="Simulation time (seconds) when the belief was recorded")


class ProvenanceRecord(BaseModel):
    """One row of the SQLite provenance log: every change to the belief graph."""

    id: int
    subject: str
    predicate: str
    perspective: str
    old_obj: Optional[str]
    new_obj: str
    old_confidence: Optional[float]
    new_confidence: float
    source: str
    timestamp: float
    reason: str


class SensorReading(BaseModel):
    """Payload returned by the sensorimotor layer."""

    sensor: str = Field(description="'lidar_front', 'camera', ...")
    t: float
    payload: dict[str, Any]


class ActionResult(BaseModel):
    """Result of a motor primitive such as move()."""

    action: str
    t: float
    success: bool
    detail: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Envelope every tool returns to the LLM."""

    ok: bool
    data: Any = None
    error: Optional[str] = None
