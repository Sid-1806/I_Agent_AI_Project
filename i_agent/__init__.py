"""I, Agent: a three-layer epistemic architecture for grounded LLM agents.

    declarative.py   Tier 1, beliefs and provenance         (Siddh)
    procedural.py    Tier 2, LLM ReAct orchestrator         (Rudraksh)
    tools.py         the tool doorway between the layers    (Rudraksh)
    sensorimotor.py  Tier 3, mock environment                (Udit)
    scenario.py, evaluation.py   test data and checks        (Udit)
    schemas.py       shared data contracts                   (whole team)
"""

# Version of the whole system, written into every evaluation log so results from different
# versions are never pooled.
#   v1  the mid-semester system (6 Oct 2026, commit b09a5df)
#   v2  18 Oct 2026: stricter grounded writes, self-check for disagreeing records and unread
#       memory, parsing of tool calls written as JSON or Python-style text
#   v3  19 Oct 2026: exact tool calls in self-check messages, planned route must be scanned,
#       unnamed robot sources rejected, get_provenance recovers from a wrong property, LiDAR
#       names the routes that exist. Driven partly by held-out set 2 failures (see README).
#   v4  18 Nov 2026: weighted confidence. Each live reading updates the static map's confidence
#       by Bayes' rule weighted by the sensor's reliability (replacing the fixed x0.3), and
#       records are compared by confidence discounted by age.
#   v4.1 24 Nov 2026: the system records a user-stated belief itself when the user's words fully
#       determine it (the model kept claiming it had), and the self-check sends back an answer that says
#       what is in a room nothing has seen ("no objects in Room 309"), and an answer that reports a
#       colour seen under yellow or dim light without the lighting and the other recorded colours, and
#       one that answers while robots disagree about a route it faces without a LiDAR reading of it.
#       Replies are capped at 1024 tokens (a runaway reply once timed out; no saved reply is near it).
#       Driven by v4 failures on dev B2 and H2, held-out 1 HB2 and held-out 3 (see README).
SYSTEM_VERSION = "v4.1"
