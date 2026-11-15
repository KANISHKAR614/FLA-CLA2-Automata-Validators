"""Task 3 tests: PDAs against independent checkers and against the grammars they were built from."""

import itertools
import json
import random
import unittest

from task3 import G_AMB, G_HTML, G_JSON, G_STMT, build_html_pda, build_json_pda, build_stmt_pda, lex_html, lex_json, lex_stmt
from task3.html_tags import G_HTML_AMBIGUOUS
from task3 import html_tags, json_pda, stmt


# ---------------------------------------------------------------- independent reference checkers
def ref_html(tokens):
    st = []
    for t in tokens:
        if t.endswith("o"):
            st.append(t[0])
        elif not st or st.pop() != t[0]:
            return False
    return bool(tokens) and not st


def ref_json(tokens):
    """Recursive descent over the 7-token alphabet."""
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def eat(t):
        nonlocal pos
        if peek() != t:
            raise ValueError
        pos += 1

    def value():
        t = peek()
        if t == "v":
            eat("v")
        elif t == "{":
            obj()
        elif t == "[":
            arr()
        else:
            raise ValueError

    def obj():
        eat("{")
        if peek() == "}":
            eat("}")
            return
        while True:
            eat("k")
            eat(":")
            value()
            if peek() == ",":
                eat(",")
            else:
                break
        eat("}")

    def arr():
        eat("[")
        if peek() == "]":
            eat("]")
            return
        while True:
            value()
            if peek() == ",":
                eat(",")
            else:
                break
        eat("]")

    try:
        if peek() == "{":
            obj()
        elif peek() == "[":
            arr()
        else:
            return False
        return pos == len(tokens)
    except ValueError:
        return False


class HtmlTests(unittest.TestCase):
    def setUp(self):
        self.pda = build_html_pda()

    def test_report_table_10(self):
        for s in ["<b></b>", "<p><b><i></i></b></p>", "<p></p><p></p>", "<p><b></b><i></i></p>",
                  "<b><b></b></b>", "<i><p></p></i><b></b>"]:
            self.assertTrue(html_tags.accepts(s), s)
        for s in ["<b><i></b></i>", "<p><b></b>", "</b><b>", "<b></b></b>", "<p></i>", ""]:
            self.assertFalse(html_tags.accepts(s), s)

    def test_is_dpda(self):
        self.assertEqual(self.pda.nondeterminism(), [])
        self.assertEqual(len(self.pda.states), 3)

    def test_id_trace_matches_report(self):
        ids, ok, _ = self.pda.trace(lex_html("<p><b></b></p>"))
        self.assertTrue(ok)
        self.assertEqual([(q, "".join(st)) for q, _, st in ids],
                         [("q0", "Z0"), ("q1", "PZ0"), ("q1", "BPZ0"), ("q1", "PZ0"), ("q1", "Z0"), ("qf", "Z0")])

    def test_exhaustive_against_stack_checker(self):
        toks = ["bo", "bc", "io", "ic", "po", "pc"]
        for n in range(0, 7):
            for t in itertools.product(toks, repeat=n):
                self.assertEqual(self.pda.accepts(list(t)), ref_html(list(t)), t)

    def test_random_long_strings(self):
        rng = random.Random(4)
        pool = sorted(G_HTML.generate(10))
        for _ in range(3000):
            toks = list(rng.choice(pool))
            if rng.random() < 0.5:
                toks[rng.randrange(len(toks))] = rng.choice(["bo", "bc", "io", "ic", "po", "pc"])
            self.assertEqual(self.pda.accepts(toks), ref_html(toks), toks)

    def test_grammar_and_pda_agree_and_unique_tree(self):
        for s in G_HTML.generate(10):
            self.assertTrue(self.pda.accepts(list(s)), s)
            self.assertEqual(G_HTML.count_trees(s), 1, s)

    def test_naive_grammar_is_ambiguous(self):
        self.assertEqual(G_HTML_AMBIGUOUS.count_trees(["po", "pc"] * 3), 2)
        self.assertEqual(G_HTML_AMBIGUOUS.count_trees(["po", "pc"] * 4), 5)  # Catalan numbers
        self.assertEqual(G_HTML.count_trees(["po", "pc"] * 4), 1)

    def test_pumping_witness(self):
        k = 6
        s = ["bo"] * k + ["bc"] * k
        self.assertTrue(self.pda.accepts(s))
        self.assertFalse(self.pda.accepts(["bo"] * (k - 2) + ["bc"] * k))  # pumping i=0 leaves the language

    def test_lexer_rejects_other_tags(self):
        with self.assertRaises(ValueError):
            lex_html("<div></div>")
        self.assertFalse(html_tags.accepts("<b>text</b>"))


class StmtTests(unittest.TestCase):
    def setUp(self):
        self.pda = build_stmt_pda()
        self.prune = G_STMT.pda_prune()

    def test_report_table_12(self):
        for s in ["if ( C ) a else a", "if ( C ) if ( C ) a else a", "if ( C ) { if ( C ) a } else a",
                  "while ( C ) { a ; if ( C ) a }", "{ a ; { a ; a } }", "while ( C ) if ( C ) a else a"]:
            self.assertTrue(stmt.accepts(s), s)
        for s in ["else a", "if ( C ) a else a else a", "if C ) a", "while ( C ) { a ; }", "while ( ) a", "{ a ; a"]:
            self.assertFalse(stmt.accepts(s), s)

    def test_dangling_else_ambiguity(self):
        w = lex_stmt("if ( C ) if ( C ) a else a")
        self.assertEqual(G_AMB.count_trees(w), 2)
        self.assertEqual(G_STMT.count_trees(w), 1)

    def test_revised_grammar_never_ambiguous_and_same_language(self):
        amb = set(G_AMB.generate(13))
        fixed = set(G_STMT.generate(13))
        self.assertEqual(amb, fixed)
        self.assertTrue(all(G_STMT.count_trees(s) == 1 for s in fixed))
        self.assertTrue(any(G_AMB.count_trees(s) > 1 for s in amb))

    def test_pda_accepts_exactly_the_language(self):
        for s in G_STMT.generate(12):
            self.assertTrue(self.pda.accepts(list(s), self.prune), s)
        toks = ["if", "else", "while", "(", ")", "{", "}", ";", "C", "a"]
        rng = random.Random(5)
        for _ in range(1500):
            w = [rng.choice(toks) for _ in range(rng.randint(1, 9))]
            self.assertEqual(self.pda.accepts(w, self.prune), G_STMT.count_trees(w) > 0, w)

    def test_top_down_pda_is_nondeterministic(self):
        self.assertTrue(self.pda.nondeterminism())

    def test_lexer(self):
        self.assertEqual(lex_stmt("if(C) a else a"), ["if", "(", "C", ")", "a", "else", "a"])
        with self.assertRaises(ValueError):
            lex_stmt("if (x) a")


class JsonTests(unittest.TestCase):
    def setUp(self):
        self.pda = build_json_pda()

    def test_report_table_14(self):
        for s in ["{ }", "[ ]", "{ k : v , k : v }", "[ v , [ v , v ] , { } ]", "{ k : { k : [ v ] } }",
                  "[ { k : v } , { k : v } ]"]:
            self.assertTrue(self.pda.accepts(s.replace("k", "k").split()), s)
        for s in ["{ k : v , }", "[ v , ]", "{ v }", "[ k : v ]", "{ k : [ v } ]", "{ k : v"]:
            self.assertFalse(self.pda.accepts(s.split()), s)

    def test_is_dpda_with_8_states(self):
        self.assertEqual(self.pda.nondeterminism(), [])
        self.assertEqual(len(self.pda.states), 8)

    def test_trace_matches_report(self):
        ids, ok, _ = self.pda.trace(["{", "k", ":", "[", "v", ",", "{", "}", "]", "}"])
        self.assertTrue(ok)
        self.assertEqual([q for q, _, _ in ids],
                         ["q0", "qobj0", "qkey", "qval", "qarr0", "qafter", "qval", "qobj0", "qafter", "qafter", "qafter", "qf"])

    def test_exhaustive_against_recursive_descent(self):
        toks = ["{", "}", "[", "]", ":", ",", "k", "v"]
        for n in range(0, 7):
            for t in itertools.product(toks, repeat=n):
                self.assertEqual(self.pda.accepts(list(t)), ref_json(list(t)), t)

    def test_grammar_and_pda_agree(self):
        for s in G_JSON.generate(11):
            self.assertTrue(self.pda.accepts(list(s)), s)
            self.assertEqual(G_JSON.count_trees(s), 1, s)

    def test_real_json_text_and_mutations_against_json_loads(self):
        rng = random.Random(6)

        def gen(depth):
            r = rng.random()
            if depth == 0 or r < 0.35:
                return rng.choice([1, "s", True, None, 2.5])
            if r < 0.7:
                return {f"k{i}": gen(depth - 1) for i in range(rng.randint(0, 3))}
            return [gen(depth - 1) for _ in range(rng.randint(0, 3))]

        for _ in range(3000):
            obj = gen(4)
            if not isinstance(obj, (dict, list)):
                obj = [obj]
            text = json.dumps(obj)
            self.assertTrue(json_pda.accepts(text), text)
            i = rng.randrange(len(text) + 1)
            op = rng.choice("ids")
            if op == "i":
                mutated = text[:i] + rng.choice("{}[],:") + text[i:]
            elif op == "d" and i < len(text) and text[i] in "{}[],:":
                mutated = text[:i] + text[i + 1:]
            else:
                continue
            try:
                parsed = json.loads(mutated)
                expected = isinstance(parsed, (dict, list))
            except ValueError:
                expected = False
            self.assertEqual(json_pda.accepts(mutated), expected, mutated)

    def test_lexer_key_vs_value(self):
        self.assertEqual(lex_json('{"a": "b", "c": [1, null]}'),
                         ["{", "k", ":", "v", ",", "k", ":", "[", "v", ",", "v", "]", "}"])


if __name__ == "__main__":
    unittest.main()
