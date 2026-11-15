"""NFA with epsilon moves and Rabin-Scott subset construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, FrozenSet, List, Set, Tuple

from .dfa import DFA, TRAP

EPS = ""


@dataclass
class NFA:
    name: str
    states: List[str]
    alphabet: List[str]
    delta: Dict[Tuple[str, str], Set[str]]  # symbol "" = epsilon
    start: str
    accepting: Set[str]
    classify: Callable[[str], str] = lambda c: c

    def eps_closure(self, qs: Set[str]) -> FrozenSet[str]:
        out, todo = set(qs), list(qs)
        while todo:
            q = todo.pop()
            for n in self.delta.get((q, EPS), ()):
                if n not in out:
                    out.add(n)
                    todo.append(n)
        return frozenset(out)

    def move(self, qs: FrozenSet[str], a: str) -> Set[str]:
        out: Set[str] = set()
        for q in qs:
            out |= self.delta.get((q, a), set())
        return out

    def accepts(self, text: str) -> bool:
        cur = self.eps_closure({self.start})
        for ch in text:
            cur = self.eps_closure(self.move(cur, self.classify(ch)))
            if not cur:
                return False
        return bool(cur & self.accepting)

    def to_dfa(self, naming: Callable[[FrozenSet[str]], str] | None = None) -> Tuple[DFA, Dict[str, FrozenSet[str]]]:
        """Subset construction. Returns the DFA and the map DFA-state -> NFA subset."""
        start = self.eps_closure({self.start})
        order: List[FrozenSet[str]] = [start]
        names: Dict[FrozenSet[str], str] = {start: "q0"}
        delta: Dict[Tuple[str, str], str] = {}
        i = 0
        while i < len(order):
            cur = order[i]
            i += 1
            for a in self.alphabet:
                nxt = self.eps_closure(self.move(cur, a))
                if not nxt:
                    continue  # goes to trap implicitly
                if nxt not in names:
                    names[nxt] = f"q{len(names)}"
                    order.append(nxt)
                delta[(names[cur], a)] = names[nxt]
        if naming:
            names = {s: naming(s) for s in names}
            delta = {(names[o_s], a): names[o_t] for o_s in order for a in self.alphabet
                     for o_t in [self.eps_closure(self.move(o_s, a))] if o_t}
        accepting = {names[s] for s in order if s & self.accepting}
        subsets = {names[s]: s for s in order}
        dfa = DFA(self.name + " (subset DFA)", [names[s] for s in order], self.alphabet, delta,
                  names[start], accepting, self.classify, TRAP)
        return dfa, subsets
