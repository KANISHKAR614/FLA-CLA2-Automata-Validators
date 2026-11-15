"""Application 3: date of birth DD/MM/YYYY (report Section 2.3, Table 6).

Only *independent field ranges* are checked (day 01-31, month 01-12, 4-digit year).
Month-length and leap-year rules are deliberately left to task2.semantic (state-explosion trade-off).
15 states: q0..q12, q14 and the trap qD (q13 is unused, as in the report's numbering).
"""

from fla.dfa import DFA


def classify(c: str) -> str:
    return {"0": "D0", "1": "D1", "2": "D2", "3": "D3", "/": "S"}.get(c, "D49" if c in "456789" else "O")


def build_dob_dfa() -> DFA:
    d = {}
    # Day tens digit
    d[("q0", "D0")] = "q1"
    d[("q0", "D1")] = "q2"
    d[("q0", "D2")] = "q2"
    d[("q0", "D3")] = "q3"
    for c in ["D1", "D2", "D3", "D49"]:        # 01-09: second digit 1-9
        d[("q1", c)] = "q4"
    for c in ["D0", "D1", "D2", "D3", "D49"]:  # 10-29: any second digit
        d[("q2", c)] = "q4"
    for c in ["D0", "D1"]:                     # 30, 31 only
        d[("q3", c)] = "q4"
    d[("q4", "S")] = "q5"
    # Month
    d[("q5", "D0")] = "q6"
    d[("q5", "D1")] = "q7"
    for c in ["D1", "D2", "D3", "D49"]:        # 01-09
        d[("q6", c)] = "q8"
    for c in ["D0", "D1", "D2"]:               # 10, 11, 12
        d[("q7", c)] = "q8"
    d[("q8", "S")] = "q9"
    # Year: four digits
    digits = ["D0", "D1", "D2", "D3", "D49"]
    for src, dst in [("q9", "q10"), ("q10", "q11"), ("q11", "q12"), ("q12", "q14")]:
        for c in digits:
            d[(src, c)] = dst
    return DFA(
        name="Date of birth DD/MM/YYYY",
        states=[f"q{i}" for i in range(13)] + ["q14"],
        alphabet=["D0", "D1", "D2", "D3", "D49", "S", "O"],
        delta=d,
        start="q0",
        accepting={"q14"},
        classify=classify,
    )
