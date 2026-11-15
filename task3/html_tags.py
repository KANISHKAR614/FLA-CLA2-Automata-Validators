"""Case study 1: nested HTML/XML tag matching (report Section 3.1, Table 9).

Tokens: bo bc io ic po pc for <b> </b> <i> </i> <p> </p>.
3-state DPDA: q0 start, q1 processing, qf accepting; stack alphabet {Z0, B, I, P}.
"""

from __future__ import annotations

import re
from typing import List

from fla.cfg import CFG
from fla.pda import PDA

OPEN = {"bo": "B", "io": "I", "po": "P"}
CLOSE = {"bc": "B", "ic": "I", "pc": "P"}

# Unambiguous grammar: S is a sequence of blocks, T is one balanced block.
G_HTML = CFG.from_text("G_html", """
S -> T S | T
T -> bo S bc | bo bc | io S ic | io ic | po S pc | po pc
""")

# The naive grammar the report warns about (S -> SS is ambiguous).
G_HTML_AMBIGUOUS = CFG.from_text("G_html_ambiguous", """
S -> S S | bo S bc | bo bc | io S ic | io ic | po S pc | po pc
""")

_TAG = re.compile(r"<(/?)([bip])>")
_NAME = {("", "b"): "bo", ("/", "b"): "bc", ("", "i"): "io", ("/", "i"): "ic", ("", "p"): "po", ("/", "p"): "pc"}


def lex_html(text: str) -> List[str]:
    """Turn markup into tag tokens. Anything but <b> <i> <p> and their closers is a lexical error."""
    text = text.strip()
    tokens, pos = [], 0
    for m in _TAG.finditer(text):
        if text[pos:m.start()].strip():
            raise ValueError(f"unsupported content {text[pos:m.start()]!r} (only <b>, <i>, <p> tags are modelled)")
        tokens.append(_NAME[(m.group(1), m.group(2))])
        pos = m.end()
    if text[pos:].strip():
        raise ValueError(f"unsupported content {text[pos:]!r} (only <b>, <i>, <p> tags are modelled)")
    return tokens


def build_html_pda() -> PDA:
    pda = PDA("HTML tag matcher", ["q0", "q1", "qf"], ["bo", "bc", "io", "ic", "po", "pc"],
              ["Z0", "B", "I", "P"], {}, "q0", "Z0", {"qf"})
    for tok, sym in OPEN.items():
        pda.add("q0", tok, "Z0", "q1", (sym, "Z0"))            # rules 1-3
        for top in ("B", "I", "P"):
            pda.add("q1", tok, top, "q1", (sym, top))          # rules 4-6
        pda.add("qf", tok, "Z0", "q1", (sym, "Z0"))            # rules 11-13: sibling top-level block
    for tok, sym in CLOSE.items():
        pda.add("q1", tok, sym, "q1", ())                      # rules 7-9: pop on matching closer
    pda.add("q1", None, "Z0", "qf", ("Z0",))                   # rule 10: all tags closed
    return pda


def accepts(text: str) -> bool:
    try:
        tokens = lex_html(text)
    except ValueError:
        return False
    return bool(tokens) and build_html_pda().accepts(tokens)
