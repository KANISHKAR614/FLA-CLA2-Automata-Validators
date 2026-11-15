"""Command-line demo for Task 2.

    python -m task2.cli mobile +919876543210
    python -m task2.cli vehicle TN45AB1234 --trace
    python -m task2.cli dob 29/02/2024 --semantic
    python -m task2.cli table           # accept/reject test tables
    python -m task2.cli stats           # state counts and the state-explosion examples
"""

from __future__ import annotations

import argparse
import sys

from . import ALL, build_vehicle_nfa
from . import semantic

SEMANTIC = {
    "mobile": semantic.check_mobile,
    "vehicle": semantic.check_vehicle,
    "dob": semantic.check_dob,
}

TABLES = {
    "mobile": (["9876543210", "+919876543210", "08123456789", "6000000000", "+917654321098"],
               ["5876543210", "+915876543210", "009876543210", "+929876543210", "987654321", "98765432105"]),
    "vehicle": (["TN45AB1234", "DL01C9999", "KA53MZ0001", "MH12P4567", "PY05X0101"],
                ["T45AB1234", "TN4AB1234", "TN451234", "TN45ABC1234", "TN45AB123", "TN45AB12345"]),
    "dob": (["15/08/1947", "01/01/2000", "31/12/2026", "29/02/2024", "30/11/1999"],
            ["00/08/2026", "32/01/2026", "15/00/2026", "15/13/2026", "15-08-2026", "15/08/26"]),
}


def show_tables() -> None:
    for key, build in ALL.items():
        dfa = build()
        good, bad = TABLES[key]
        print(f"\n== {dfa.name}  ({len(dfa.all_states)} states incl. trap) ==")
        for s in good:
            print(f"  {'ACCEPT' if dfa.accepts(s) else 'REJECT':7} {s}")
        for s in bad:
            print(f"  {'ACCEPT' if dfa.accepts(s) else 'REJECT':7} {s}")


def show_stats() -> None:
    print("Model                         |Q| (incl. trap)   |Sigma| classes   minimal |Q|")
    for key, build in ALL.items():
        dfa = build()
        print(f"{dfa.name:30}{len(dfa.all_states):>6}{len(dfa.alphabet):>20}{len(dfa.minimize().all_states):>14}")
    nfa = build_vehicle_nfa()
    dfa, subsets = nfa.to_dfa()
    print(f"\nVehicle NFA: {len(nfa.states)} states -> subset DFA: {len(dfa.states)} live states")
    for name, subset in subsets.items():
        print(f"  {name:>4} = {{{', '.join(sorted(subset, key=lambda s: int(s[1:])))}}}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("app", choices=[*ALL, "table", "stats"])
    p.add_argument("text", nargs="?", default="")
    p.add_argument("--trace", action="store_true", help="print the step-by-step state trace")
    p.add_argument("--semantic", action="store_true", help="run the post-DFA semantic check when accepted")
    a = p.parse_args(argv)

    if a.app == "table":
        show_tables()
        return 0
    if a.app == "stats":
        show_stats()
        return 0
    dfa = ALL[a.app]()
    if a.trace:
        print(dfa.format_trace(a.text))
    ok = dfa.accepts(a.text)
    print(f"{'ACCEPTED' if ok else 'REJECTED'}: {a.text!r} (final state {dfa.run(a.text)})")
    if ok and a.semantic:
        valid, why = SEMANTIC[a.app](a.text)
        print(f"semantic stage: {'OK' if valid else 'FAIL'} - {why}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
