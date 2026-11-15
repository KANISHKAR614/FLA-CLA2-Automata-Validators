"""Case study 3: JSON-like nested structure validator (report Section 3.3, Table 13).

Tokens: { } [ ] : , k v   (k = string key, v = primitive value).
8-state DPDA; stack alphabet {Z0, B (open object), K (open array)}.
"""

from __future__ import annotations

import re
from typing import List

from fla.cfg import CFG
from fla.pda import PDA

G_JSON = CFG.from_text("G_json", """
S -> O | A
O -> { } | { M }
M -> k : V , M | k : V
A -> [ ] | [ E ]
E -> V , E | V
V -> v | O | A
""")

_LEX = re.compile(r'''\s*(?:
    (?P<punct>[{}\[\]:,])
  | (?P<string>"(?:[^"\\]|\\.)*")
  | (?P<prim>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null)
)''', re.X)


def lex_json(text: str) -> List[str]:
    """Map real JSON text to the 7-token alphabet. A string followed by ':' is a key (k), else a value (v)."""
    tokens, pos, text = [], 0, text.rstrip()
    while pos < len(text):
        m = _LEX.match(text, pos)
        if not m or m.end() == pos:
            raise ValueError(f"unexpected input at position {pos}: {text[pos:pos + 10]!r}")
        if m.group("punct"):
            tokens.append(m.group("punct"))
        elif m.group("string"):
            rest = text[m.end():].lstrip()
            tokens.append("k" if rest.startswith(":") else "v")
        else:
            tokens.append("v")
        pos = m.end()
    return tokens


def build_json_pda() -> PDA:
    states = ["q0", "qobj0", "qkey", "qval", "qarr0", "qafter", "qobj_next", "qf"]
    pda = PDA("JSON structure validator", states, ["{", "}", "[", "]", ":", ",", "k", "v"],
              ["Z0", "B", "K"], {}, "q0", "Z0", {"qf"})
    pda.add("q0", "{", "Z0", "qobj0", ("B", "Z0"))              # 1
    pda.add("q0", "[", "Z0", "qarr0", ("K", "Z0"))              # 2
    pda.add("qobj0", "}", "B", "qafter", ())                    # 3  empty object
    pda.add("qobj0", "k", "B", "qkey", ("B",))                  # 4
    pda.add("qobj_next", "k", "B", "qkey", ("B",))              # 5
    pda.add("qkey", ":", "B", "qval", ("B",))                   # 6
    pda.add("qarr0", "]", "K", "qafter", ())                    # 7  empty array
    pda.add("qarr0", "v", "K", "qafter", ("K",))                # 8
    pda.add("qarr0", "{", "K", "qobj0", ("B", "K"))             # 9
    pda.add("qarr0", "[", "K", "qarr0", ("K", "K"))             # 10
    for x in ("B", "K"):
        pda.add("qval", "v", x, "qafter", (x,))                 # 11
        pda.add("qval", "{", x, "qobj0", ("B", x))              # 12
        pda.add("qval", "[", x, "qarr0", ("K", x))              # 13
    pda.add("qafter", ",", "B", "qobj_next", ("B",))            # 14
    pda.add("qafter", ",", "K", "qval", ("K",))                 # 15
    pda.add("qafter", "}", "B", "qafter", ())                   # 16
    pda.add("qafter", "]", "K", "qafter", ())                   # 17
    pda.add("qafter", None, "Z0", "qf", ("Z0",))                # 18
    return pda


def accepts(text: str) -> bool:
    try:
        tokens = lex_json(text)
    except ValueError:
        return False
    return build_json_pda().accepts(tokens)
