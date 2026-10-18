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
SYSTEM_VERSION = "v2"
