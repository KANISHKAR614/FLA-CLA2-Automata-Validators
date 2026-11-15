"""Case study 2: if-else / while statement syntax (report Section 3.2, Table 11).

Tokens: if else while ( ) { } ; C a   (C = boolean condition, a = atomic statement).
G_AMB  has the classic dangling-else ambiguity; G_STMT splits statements into matched (M) and
unmatched (U) so an else always binds to the closest unmatched if.
"""

from __future__ import annotations

import re
from typing import List

from fla.cfg import CFG
from fla.pda import PDA

G_AMB = CFG.from_text("G_amb", """
S -> if ( C ) S | if ( C ) S else S | while ( C ) S | { L } | a
L -> S ; L | S
""")

G_STMT = CFG.from_text("G_stmt", """
S -> M | U
M -> if ( C ) M else M | while ( C ) M | { L } | a
U -> if ( C ) S | if ( C ) M else U | while ( C ) U
L -> S ; L | S
""")

_TOKEN = re.compile(r"\s*(?:(if|else|while|C|a)(?![A-Za-z0-9_])|([(){};]))")


def lex_stmt(text: str) -> List[str]:
    """Tokenise a statement written in the report's token notation, e.g. ``if (C) a else a``."""
    tokens, pos = [], 0
    text = text.strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m:
            raise ValueError(f"unexpected input at position {pos}: {text[pos:pos + 10]!r}")
        tokens.append(m.group(1) or m.group(2))
        pos = m.end()
    return tokens


def build_stmt_pda() -> PDA:
    """Top-down predictive PDA (q0 push S, q1 expand/match, qf accept). Nondeterministic as built."""
    return G_STMT.to_pda()


def accepts(text: str) -> bool:
    try:
        tokens = lex_stmt(text)
    except ValueError:
        return False
    if not tokens:
        return False
    pda = build_stmt_pda()
    return pda.accepts(tokens, prune=G_STMT.pda_prune())
