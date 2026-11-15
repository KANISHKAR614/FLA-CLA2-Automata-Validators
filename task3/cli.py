"""Command-line demo for Task 3.

    python -m task3.cli html "<p><b></b><i></i></p>" --trace
    python -m task3.cli stmt "if ( C ) if ( C ) a else a"
    python -m task3.cli json '{"k":[1,{}]}' --trace
    python -m task3.cli table
    python -m task3.cli ambiguity       # parse-tree counts: ambiguous vs revised grammars
    python -m task3.cli grammar         # show every grammar and its CFG->PDA determinism
"""

from __future__ import annotations

import argparse
import sys

from fla.cfg import CFG
from .html_tags import G_HTML, G_HTML_AMBIGUOUS, build_html_pda, lex_html
from .json_pda import G_JSON, build_json_pda, lex_json
from .stmt import G_AMB, G_STMT, accepts as stmt_accepts, build_stmt_pda, lex_stmt

TABLES = {
    "html": (["<b></b>", "<p><b><i></i></b></p>", "<p></p><p></p>", "<b><b></b></b>"],
             ["<b><i></b></i>", "<p><b></b>", "</b><b>", "<b></b></b>", "<p></i>", ""]),
    "stmt": (["if ( C ) a else a", "if ( C ) if ( C ) a else a", "if ( C ) { if ( C ) a } else a",
              "while ( C ) { a ; if ( C ) a }", "{ a ; { a ; a } }"],
             ["else a", "if ( C ) a else a else a", "if C ) a", "while ( C ) { a ; }", "while ( ) a", "{ a ; a"]),
    "json": (["{ }", "[ ]", '{"k": 1, "j": 2}', '[1, [2, 3], {}]', '{"a": {"b": [1]}}', '[{"a": 1}, {"b": 2}]'],
             ['{"k": 1,}', "[1,]", "{1}", '[ "k": 1 ]', '{"k": [1} ]', '{"k": 1']),
}


def _runner(kind: str):
    if kind == "html":
        return build_html_pda(), lex_html, None
    if kind == "stmt":
        return build_stmt_pda(), lex_stmt, G_STMT.pda_prune()
    return build_json_pda(), lex_json, None


def verdict(kind: str, text: str) -> bool:
    pda, lex, prune = _runner(kind)
    try:
        tokens = lex(text)
    except ValueError:
        return False
    return bool(tokens) and pda.accepts(tokens, prune=prune)


def show_tables() -> None:
    for kind, (good, bad) in TABLES.items():
        print(f"\n== {kind} ==")
        for s in good + bad:
            print(f"  {'ACCEPT' if verdict(kind, s) else 'REJECT':7} {s or '(empty)'}")


def show_ambiguity(html_len: int = 9, stmt_len: int = 13) -> None:
    print(f"Parse trees per generated string (HTML strings up to {html_len} tokens, "
          f"statements up to {stmt_len} tokens; the dangling else first appears at 11 tokens)")
    pairs = [("HTML tags", G_HTML_AMBIGUOUS, G_HTML, html_len), ("if-else / while", G_AMB, G_STMT, stmt_len)]
    for label, amb, fixed, bound in pairs:
        for g in (amb, fixed):
            strings = list(g.generate(bound))
            counts = [g.count_trees(s) for s in strings]
            multi = sum(1 for c in counts if c > 1)
            worst = max(zip(counts, strings), key=lambda t: t[0])
            print(f"  {label:16} {g.name:20} strings={len(strings):>6}  with >1 tree={multi:>5}  "
                  f"max trees={worst[0]} e.g. {' '.join(worst[1])}")
    s = "if ( C ) if ( C ) a else a".split()
    print(f"\nDangling else: G_amb gives {G_AMB.count_trees(s)} trees, G_stmt gives {G_STMT.count_trees(s)} tree")
    print("(Ambiguity is undecidable in general; this is bounded evidence, not a proof.)")


def show_grammars() -> None:
    for g in (G_HTML, G_AMB, G_STMT, G_JSON):
        print(f"\n{g.name}  (start {g.start})")
        for v, prods in g.rules.items():
            print(f"  {v} -> " + " | ".join(" ".join(p) for p in prods))
    print("\nDeterminism:")
    for name, pda in (("HTML DPDA", build_html_pda()), ("JSON DPDA", build_json_pda()),
                      ("if-else/while top-down PDA", build_stmt_pda())):
        problems = pda.nondeterminism()
        print(f"  {name:28} {'deterministic' if not problems else 'NONDETERMINISTIC (' + str(len(problems)) + ' conflicts)'}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("app", choices=["html", "stmt", "json", "table", "ambiguity", "grammar"])
    p.add_argument("text", nargs="?", default="")
    p.add_argument("--trace", action="store_true", help="print the instantaneous-description trace")
    p.add_argument("--html-len", type=int, default=9, help="token bound for the HTML ambiguity check")
    p.add_argument("--stmt-len", type=int, default=13, help="token bound for the if-else ambiguity check")
    a = p.parse_args(argv)
    if a.app == "table":
        show_tables()
        return 0
    if a.app == "ambiguity":
        show_ambiguity(a.html_len, a.stmt_len)
        return 0
    if a.app == "grammar":
        show_grammars()
        return 0
    pda, lex, prune = _runner(a.app)
    try:
        tokens = lex(a.text)
    except ValueError as e:
        print(f"REJECTED (lexical error): {e}")
        return 1
    if a.trace:
        if pda.is_deterministic():
            print(pda.format_trace(tokens))
        else:
            print("(PDA is nondeterministic as built; showing the verdict only)")
    ok = bool(tokens) and pda.accepts(tokens, prune=prune)
    print(f"{'ACCEPTED' if ok else 'REJECTED'}: {a.text!r}  tokens: {' '.join(tokens) or '(none)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
