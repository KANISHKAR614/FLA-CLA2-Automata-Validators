"""Task 2 tests: DFAs against independently written regular expressions, plus structural checks."""

import datetime
import itertools
import random
import re
import unittest

from task2 import build_dob_dfa, build_mobile_dfa, build_vehicle_dfa, build_vehicle_nfa
from task2 import semantic

MOBILE_RE = re.compile(r"(\+91|0)?[6-9][0-9]{9}")
VEHICLE_RE = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}")
DOB_RE = re.compile(r"(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/[0-9]{4}")


def mutate(rng: random.Random, s: str, alphabet: str) -> str:
    for _ in range(rng.randint(0, 2)):
        op = rng.choice("ids")
        i = rng.randrange(len(s) + 1)
        if op == "i":
            s = s[:i] + rng.choice(alphabet) + s[i:]
        elif op == "d" and s:
            i = min(i, len(s) - 1)
            s = s[:i] + s[i + 1:]
        elif s:
            i = min(i, len(s) - 1)
            s = s[:i] + rng.choice(alphabet) + s[i + 1:]
    return s


class MobileTests(unittest.TestCase):
    def setUp(self):
        self.dfa = build_mobile_dfa()

    def test_report_table_3(self):
        for s in ["9876543210", "+919876543210", "08123456789", "6000000000", "+917654321098", "06543210987"]:
            self.assertTrue(self.dfa.accepts(s), s)
        for s in ["5876543210", "+915876543210", "009876543210", "+929876543210", "987654321", "98765432105"]:
            self.assertFalse(self.dfa.accepts(s), s)

    def test_state_count(self):
        self.assertEqual(len(self.dfa.all_states), 15)

    def test_trace_matches_report(self):
        states = [r[0] for r in self.dfa.trace("09876543210")] + [self.dfa.run("09876543210")]
        self.assertEqual(states, ["q0", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10", "q11", "q12", "q13"])

    def test_against_regex(self):
        rng = random.Random(1)
        alphabet = "+0123456789a "
        seeds = ["9876543210", "+919876543210", "09876543210", "6000000000"]
        for _ in range(40000):
            s = mutate(rng, rng.choice(seeds), alphabet)
            self.assertEqual(self.dfa.accepts(s), bool(MOBILE_RE.fullmatch(s)), s)
        for n in range(0, 5):  # exhaustive short strings
            for t in itertools.product("+0159a", repeat=n):
                s = "".join(t)
                self.assertEqual(self.dfa.accepts(s), bool(MOBILE_RE.fullmatch(s)), s)


class VehicleTests(unittest.TestCase):
    def setUp(self):
        self.dfa = build_vehicle_dfa()
        self.nfa = build_vehicle_nfa()

    def test_report_table_5(self):
        for s in ["TN45AB1234", "DL01C9999", "KA53MZ0001", "MH12P4567", "PY05X0101", "KL07CD8888"]:
            self.assertTrue(self.dfa.accepts(s), s)
        for s in ["T45AB1234", "TN4AB1234", "TN451234", "TN45ABC1234", "TN45AB123", "TN45AB12345"]:
            self.assertFalse(self.dfa.accepts(s), s)

    def test_state_count(self):
        self.assertEqual(len(self.dfa.all_states), 12)

    def test_subset_construction_matches_hand_dfa(self):
        sub, subsets = self.nfa.to_dfa()
        self.assertEqual(len(sub.states), 11)
        self.assertEqual({tuple(sorted(v)) for v in subsets.values() if len(v) > 1}, {("n5", "n6")})
        rng = random.Random(2)
        for _ in range(20000):
            s = mutate(rng, rng.choice(["TN45AB1234", "DL01C9999"]), "AZ09a-")
            expected = bool(VEHICLE_RE.fullmatch(s))
            self.assertEqual(self.dfa.accepts(s), expected, s)
            self.assertEqual(sub.accepts(s), expected, s)
            self.assertEqual(self.nfa.accepts(s), expected, s)

    def test_minimal(self):
        self.assertEqual(len(self.dfa.minimize().all_states), 12)


class DobTests(unittest.TestCase):
    def setUp(self):
        self.dfa = build_dob_dfa()

    def test_report_table_7(self):
        for s in ["15/08/1947", "01/01/2000", "31/12/2026", "29/02/2024", "30/11/1999", "09/09/2026"]:
            self.assertTrue(self.dfa.accepts(s), s)
        for s in ["00/08/2026", "32/01/2026", "15/00/2026", "15/13/2026", "15-08-2026", "15/08/26"]:
            self.assertFalse(self.dfa.accepts(s), s)

    def test_state_count(self):
        self.assertEqual(len(self.dfa.all_states), 15)

    def test_every_day_month_pair_exhaustively(self):
        for dd in range(0, 100):
            for mm in range(0, 100):
                s = f"{dd:02d}/{mm:02d}/2026"
                self.assertEqual(self.dfa.accepts(s), bool(DOB_RE.fullmatch(s)), s)

    def test_random_against_regex(self):
        rng = random.Random(3)
        for _ in range(30000):
            s = mutate(rng, rng.choice(["15/08/1947", "31/12/2026", "01/01/2000"]), "0123/-a9")
            self.assertEqual(self.dfa.accepts(s), bool(DOB_RE.fullmatch(s)), s)

    def test_syntax_accepts_impossible_dates_semantic_rejects(self):
        for s in ["30/02/2026", "31/04/2026", "29/02/2025"]:
            self.assertTrue(self.dfa.accepts(s))
            self.assertFalse(semantic.check_dob(s, datetime.date(2026, 11, 15))[0], s)
        self.assertTrue(semantic.check_dob("29/02/2024", datetime.date(2026, 11, 15))[0])
        self.assertFalse(semantic.check_dob("01/01/2099", datetime.date(2026, 11, 15))[0])

    def test_leap_year_rule(self):
        self.assertTrue(semantic.is_leap(2000))
        self.assertFalse(semantic.is_leap(1900))
        self.assertTrue(semantic.is_leap(2024))
        self.assertFalse(semantic.is_leap(2025))


class SemanticTests(unittest.TestCase):
    def test_vehicle_semantic(self):
        self.assertTrue(semantic.check_vehicle("TN45AB1234")[0])
        self.assertFalse(semantic.check_vehicle("ZZ99AA0001")[0])
        self.assertFalse(semantic.check_vehicle("TN45AB0000")[0])
        self.assertTrue(build_vehicle_dfa().accepts("ZZ99AA0000"))  # syntax-only automaton accepts it


if __name__ == "__main__":
    unittest.main()
