"""Simulation clock shared by the declarative and sensorimotor layers.

Using simulated time (instead of wall-clock time) keeps every scenario run reproducible.
"""


class SimClock:
    START = 1_000_000.0

    def __init__(self, start: float = START):
        self.t = start

    def now(self) -> float:
        return self.t

    def tick(self, seconds: float = 1.0) -> float:
        self.t += seconds
        return self.t
