"""Deterministic finite automaton with a character-class front end and an explicit trap state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Hashable, Iterable, List, Set, Tuple

TRAP = "qD"


@dataclass
class DFA:
    """M = (Q, Sigma, delta, q0, F) over *character classes*.

    ``classify`` maps a raw character to a class symbol (the Stage-1 classifier of the report).
    ``delta`` is a partial table {(state, class): state}; any missing entry goes to the trap state.
    """

    name: str
    states: List[str]
    alphabet: List[str]
    delta: Dict[Tuple[str, str], str]
    start: str
    accepting: Set[str]
    classify: Callable[[str], str] = field(default=lambda c: c)
    trap: str = TRAP

    # ------------------------------------------------------------------ running
    def step(self, state: str, symbol: str) -> str:
        return self.delta.get((state, symbol), self.trap)

    def run(self, text: str) -> str:
        state = self.start
        for ch in text:
            state = self.step(state, self.classify(ch))
        return state

    def accepts(self, text: str) -> bool:
        return self.run(text) in self.accepting

    def trace(self, text: str) -> List[Tuple[str, str, str, str]]:
        """Return rows (state, char, class, next_state) for every character read."""
        rows = []
        state = self.start
        for ch in text:
            cls = self.classify(ch)
            nxt = self.step(state, cls)
            rows.append((state, ch, cls, nxt))
            state = nxt
        return rows

    def format_trace(self, text: str) -> str:
        lines = [f"{self.name} on {text!r}"]
        for i, (s, ch, cls, nxt) in enumerate(self.trace(text), 1):
            lines.append(f"  {i:>2}. d({s}, {ch!r} -> {cls}) = {nxt}")
        final = self.run(text)
        verdict = "ACCEPTED" if final in self.accepting else "REJECTED"
        lines.append(f"  final state {final} -> {verdict}")
        return "\n".join(lines)

    # ------------------------------------------------------------------ analysis
    @property
    def all_states(self) -> List[str]:
        """States including the trap (the report counts the trap in |Q|)."""
        return self.states + ([self.trap] if self.trap not in self.states else [])

    def total_table(self) -> Dict[Tuple[str, str], str]:
        return {(q, a): self.step(q, a) for q in self.all_states for a in self.alphabet}

    def reachable(self) -> Set[str]:
        seen, todo = {self.start}, [self.start]
        while todo:
            q = todo.pop()
            for a in self.alphabet:
                n = self.step(q, a)
                if n not in seen:
                    seen.add(n)
                    todo.append(n)
        return seen

    def minimize(self) -> "DFA":
        """Moore partition refinement on the reachable part. Returns an equivalent minimal DFA."""
        live = sorted(self.reachable())
        block = {q: (q in self.accepting) for q in live}
        while True:
            sig = {q: (block[q], tuple(block[self.step(q, a)] for a in self.alphabet)) for q in live}
            ids: Dict[Hashable, int] = {}
            new = {q: ids.setdefault(sig[q], len(ids)) for q in live}
            if len(set(new.values())) == len(set(block.values())):
                block = new
                break
            block = new
        rep: Dict[int, str] = {}
        for q in live:  # deterministic representative: first by sorted name, start preferred
            rep.setdefault(block[q], q)
        rep[block[self.start]] = self.start
        name = {q: rep[block[q]] for q in live}
        delta = {}
        for q in live:
            if name[q] != q:
                continue
            for a in self.alphabet:
                delta[(q, a)] = name[self.step(q, a)]
        states = sorted(set(name.values()))
        return DFA(self.name + " (min)", states, self.alphabet, delta, name[self.start],
                   {name[q] for q in live if q in self.accepting}, self.classify, self.trap)

    # ------------------------------------------------------------------ export
    def to_dot(self, hide_trap: bool = True) -> str:
        out = [f'digraph "{self.name}" {{', "  rankdir=LR;", '  node [shape=circle, fontname="Helvetica"];',
               '  __start [shape=point];', f'  __start -> "{self.start}";']
        for q in self.all_states:
            if hide_trap and q == self.trap:
                continue
            shape = "doublecircle" if q in self.accepting else "circle"
            out.append(f'  "{q}" [shape={shape}];')
        grouped: Dict[Tuple[str, str], List[str]] = {}
        for (q, a), n in self.delta.items():
            if hide_trap and n == self.trap:
                continue
            grouped.setdefault((q, n), []).append(a)
        for (q, n), syms in grouped.items():
            out.append(f'  "{q}" -> "{n}" [label="{",".join(syms)}"];')
        out.append("}")
        return "\n".join(out)

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "start": self.start,
            "accepting": sorted(self.accepting),
            "trap": self.trap,
            "alphabet": self.alphabet,
            "states": self.all_states,
            "delta": {f"{q}|{a}": n for (q, a), n in self.delta.items()},
        }
