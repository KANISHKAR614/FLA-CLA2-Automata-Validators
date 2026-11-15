"""Application 1: Indian mobile number validator (report Section 2.1, Table 2).

Language: (eps | 0 | +91) . [6-9] . [0-9]^9      15-state DFA (q0..q13 + trap qD).
Classes : P '+', Z '0', N1 '1', L2 '2-5', N9 '9', H6 '6-8', O other.
"""

from fla.dfa import DFA


def classify(c: str) -> str:
    if c == "+":
        return "P"
    if c == "0":
        return "Z"
    if c == "1":
        return "N1"
    if c in "2345":
        return "L2"
    if c == "9":
        return "N9"
    if c in "678":
        return "H6"
    return "O"


def build_mobile_dfa() -> DFA:
    d = {}
    d[("q0", "P")] = "q1"
    d[("q0", "Z")] = "q3"
    d[("q0", "N9")] = "q4"
    d[("q0", "H6")] = "q4"
    d[("q1", "N9")] = "q2"          # '+9'
    d[("q2", "N1")] = "q3"          # '+91'
    d[("q3", "N9")] = "q4"          # first subscriber digit must be in H
    d[("q3", "H6")] = "q4"
    digits = ["Z", "N1", "L2", "N9", "H6"]
    for i in range(4, 13):          # q4..q12 -> next of the counting chain
        for c in digits:
            d[(f"q{i}", c)] = f"q{i + 1}"
    return DFA(
        name="Indian mobile number",
        states=[f"q{i}" for i in range(14)],
        alphabet=["P", "Z", "N1", "L2", "N9", "H6", "O"],
        delta=d,
        start="q0",
        accepting={"q13"},
        classify=classify,
    )
