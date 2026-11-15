"""Pushdown automaton simulator working on instantaneous descriptions (state, remaining input, stack)."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple

Config = Tuple[str, int, Tuple[str, ...]]  # (state, input position, stack with top at index 0)
Move = Tuple[str, Tuple[str, ...]]  # (next state, symbols pushed in place of the top, leftmost = new top)


@dataclass
class PDA:
    """M = (Q, Sigma, Gamma, delta, q0, Z0, F), acceptance by final state with all input consumed.

    delta[(state, input_token_or_None, stack_top)] -> list of (next_state, push_tuple).
    ``None`` as input token means an epsilon move.
    """

    name: str
    states: List[str]
    input_alphabet: List[str]
    stack_alphabet: List[str]
    delta: Dict[Tuple[str, Optional[str], str], List[Move]]
    start: str
    z0: str
    accepting: Set[str]

    # ------------------------------------------------------------ construction helpers
    def add(self, state: str, token: Optional[str], top: str, nxt: str, push: Sequence[str] = ()) -> None:
        self.delta.setdefault((state, token, top), []).append((nxt, tuple(push)))

    # ------------------------------------------------------------ simulation
    def initial(self) -> Config:
        return (self.start, 0, (self.z0,))

    def moves(self, cfg: Config, tokens: Sequence[str]) -> List[Tuple[str, Config]]:
        q, pos, stack = cfg
        if not stack:
            return []
        top, rest = stack[0], stack[1:]
        out: List[Tuple[str, Config]] = []
        if pos < len(tokens):
            for nxt, push in self.delta.get((q, tokens[pos], top), []):
                out.append((f"read {tokens[pos]}", (nxt, pos + 1, tuple(push) + rest)))
        for nxt, push in self.delta.get((q, None, top), []):
            out.append(("eps", (nxt, pos, tuple(push) + rest)))
        return out

    def is_accepting(self, cfg: Config, tokens: Sequence[str]) -> bool:
        return cfg[0] in self.accepting and cfg[1] == len(tokens)

    def accepts(self, tokens: Sequence[str], prune: Optional[Callable[[Config, Sequence[str]], bool]] = None,
                max_configs: int = 200_000) -> bool:
        return self.search(tokens, prune, max_configs)[0]

    def search(self, tokens: Sequence[str], prune: Optional[Callable[[Config, Sequence[str]], bool]] = None,
               max_configs: int = 200_000) -> Tuple[bool, int]:
        """Breadth-first exploration of all configurations. Returns (accepted, configurations explored)."""
        start = self.initial()
        seen = {start}
        queue = deque([start])
        while queue:
            cfg = queue.popleft()
            if self.is_accepting(cfg, tokens):
                return True, len(seen)
            for _, nxt in self.moves(cfg, tokens):
                if nxt in seen or (prune and prune(nxt, tokens)):
                    continue
                if len(seen) >= max_configs:
                    return False, len(seen)
                seen.add(nxt)
                queue.append(nxt)
        return False, len(seen)

    # ------------------------------------------------------------ determinism
    def nondeterminism(self) -> List[str]:
        """List the reasons this PDA is not a DPDA (empty list = deterministic)."""
        problems = []
        keys = {(q, t) for (q, _, t) in self.delta}
        for q, t in sorted(keys):
            eps = self.delta.get((q, None, t), [])
            if len(eps) > 1:
                problems.append(f"({q}, eps, {t}) has {len(eps)} moves")
            if eps and any(tok is not None and k_q == q and k_t == t
                           for (k_q, tok, k_t) in self.delta):
                problems.append(f"({q}, {t}): eps move competes with an input move")
        for (q, tok, t), mv in sorted(self.delta.items(), key=lambda kv: (kv[0][0], str(kv[0][1]), kv[0][2])):
            if tok is not None and len(mv) > 1:
                problems.append(f"({q}, {tok}, {t}) has {len(mv)} moves")
        return problems

    def is_deterministic(self) -> bool:
        return not self.nondeterminism()

    # ------------------------------------------------------------ deterministic trace
    def trace(self, tokens: Sequence[str], limit: int = 100_000) -> Tuple[List[Config], bool, str]:
        """Follow the unique path of a DPDA. Returns (IDs, accepted, reason)."""
        cfg = self.initial()
        ids = [cfg]
        for _ in range(limit):
            options = self.moves(cfg, tokens)
            if not options:
                break
            # a DPDA never has two applicable moves; prefer the input move if it exists
            cfg = options[0][1]
            ids.append(cfg)
        ok = self.is_accepting(cfg, tokens)
        if ok:
            return ids, True, "input exhausted in an accepting state"
        q, pos, stack = cfg
        if pos < len(tokens):
            return ids, False, f"no move in state {q} on {tokens[pos]!r} with stack top {stack[0] if stack else '-'!r}"
        return ids, False, f"input exhausted in state {q} (not accepting) with stack {''.join(stack)}"

    def format_trace(self, tokens: Sequence[str]) -> str:
        ids, ok, why = self.trace(tokens)
        lines = [f"{self.name} on {' '.join(tokens) if tokens else 'epsilon'}"]
        for i, (q, pos, stack) in enumerate(ids):
            rest = " ".join(tokens[pos:]) or "eps"
            lines.append(f"  {'|-' if i else '  '} ({q}, {rest}, {' '.join(stack)})")
        lines.append(f"  {'ACCEPTED' if ok else 'REJECTED'}: {why}")
        return "\n".join(lines)

    # ------------------------------------------------------------ export
    def to_dot(self) -> str:
        out = [f'digraph "{self.name}" {{', "  rankdir=LR;", '  node [shape=circle, fontname="Helvetica"];',
               '  __start [shape=point];', f'  __start -> "{self.start}";']
        for q in self.states:
            out.append(f'  "{q}" [shape={"doublecircle" if q in self.accepting else "circle"}];')
        grouped: Dict[Tuple[str, str], List[str]] = {}
        for (q, tok, top), mv in self.delta.items():
            for nxt, push in mv:
                label = f'{tok if tok is not None else "ε"}, {top} / {"".join(push) if push else "ε"}'
                grouped.setdefault((q, nxt), []).append(label)
        for (q, n), labels in grouped.items():
            joined = "\\n".join(sorted(labels))
            out.append(f'  "{q}" -> "{n}" [label="{joined}", fontsize=9];')
        out.append("}")
        return "\n".join(out)
