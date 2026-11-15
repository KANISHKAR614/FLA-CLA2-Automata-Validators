"""Application 2: Indian vehicle registration number (report Section 2.2, Table 4).

Language: U^2 D^2 (U | U^2) D^4 over U = A-Z, D = 0-9.
The NFA has 11 states with an epsilon move for the optional 2nd series letter;
subset construction gives the 12-state DFA (11 live states + trap).
"""

from fla.dfa import DFA
from fla.nfa import NFA


def classify(c: str) -> str:
    if "A" <= c <= "Z":
        return "U"
    if "0" <= c <= "9":
        return "D"
    return "O"


def build_vehicle_nfa() -> NFA:
    d = {
        ("n0", "U"): {"n1"},
        ("n1", "U"): {"n2"},
        ("n2", "D"): {"n3"},
        ("n3", "D"): {"n4"},
        ("n4", "U"): {"n5"},
        ("n5", ""): {"n6"},      # one-letter series: epsilon skips the second letter
        ("n5", "U"): {"n6"},     # two-letter series
        ("n6", "D"): {"n7"},
        ("n7", "D"): {"n8"},
        ("n8", "D"): {"n9"},
        ("n9", "D"): {"n10"},
    }
    return NFA("Vehicle registration", [f"n{i}" for i in range(11)], ["U", "D", "O"], d, "n0", {"n10"}, classify)


def build_vehicle_dfa() -> DFA:
    """Hand-built DFA exactly as in Table 4 of the report."""
    d = {
        ("q0", "U"): "q1",
        ("q1", "U"): "q2",
        ("q2", "D"): "q3",
        ("q3", "D"): "q4",
        ("q4", "U"): "q5",
        ("q5", "U"): "q6",   # second series letter
        ("q5", "D"): "q7",   # one-letter series: straight to first serial digit
        ("q6", "D"): "q7",
        ("q7", "D"): "q8",
        ("q8", "D"): "q9",
        ("q9", "D"): "q10",
    }
    return DFA("Vehicle registration", [f"q{i}" for i in range(11)], ["U", "D", "O"], d, "q0", {"q10"}, classify)
