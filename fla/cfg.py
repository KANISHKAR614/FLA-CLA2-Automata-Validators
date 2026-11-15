"""Context-free grammars: parsing from text, CFG -> PDA, parse-tree counting, bounded generation."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterator, List, Sequence, Set, Tuple

from .pda import PDA

Production = Tuple[str, ...]


@dataclass
class CFG:
    name: str
    start: str
    rules: Dict[str, List[Production]]

    @classmethod
    def from_text(cls, name: str, text: str, start: str | None = None) -> "CFG":
        """Parse lines like ``S -> S S | ( S ) | a``. Symbols are whitespace separated."""
        rules: Dict[str, List[Production]] = {}
        first = None
        for line in text.strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            lhs, rhs = line.split("->")
            lhs = lhs.strip()
            first = first or lhs
            for alt in rhs.split("|"):
                rules.setdefault(lhs, []).append(tuple(alt.split()))
        return cls(name, start or first, rules)

    @property
    def variables(self) -> Set[str]:
        return set(self.rules)

    @property
    def terminals(self) -> Set[str]:
        return {s for prods in self.rules.values() for p in prods for s in p if s not in self.rules}

    # ------------------------------------------------------------------ CFG -> PDA
    def to_pda(self) -> PDA:
        """Standard top-down construction (nondeterministic): expand variables, match terminals."""
        z0 = "Z0"
        pda = PDA(self.name + " (top-down PDA)", ["q0", "q1", "qf"], sorted(self.terminals),
                  sorted(self.variables | self.terminals | {z0}), {}, "q0", z0, {"qf"})
        pda.add("q0", None, z0, "q1", (self.start, z0))
        for var, prods in self.rules.items():
            for p in prods:
                pda.add("q1", None, var, "q1", p)
        for t in self.terminals:
            pda.add("q1", t, t, "q1", ())
        pda.add("q1", None, z0, "qf", (z0,))
        return pda

    def pda_prune(self):
        """Every symbol derives at least one token (no epsilon rules), so a stack longer than the
        remaining input can never be emptied. Used to keep the nondeterministic search finite."""
        z0 = "Z0"

        def prune(cfg, tokens):
            _, pos, stack = cfg
            return len(stack) - 1 > len(tokens) - pos if stack and stack[-1] == z0 else False

        return prune

    # ------------------------------------------------------------------ counting parse trees
    def count_trees(self, tokens: Sequence[str]) -> int:
        """Number of distinct parse trees of ``tokens`` (grammar must have no epsilon / unit-cycle rules)."""
        toks = tuple(tokens)
        n = len(toks)
        rules = {v: [tuple(p) for p in ps] for v, ps in self.rules.items()}

        @lru_cache(maxsize=None)
        def sym(s: str, i: int, j: int) -> int:
            if s not in rules:
                return 1 if j == i + 1 and toks[i] == s else 0
            return sum(seq(p, 0, i, j) for p in rules[s])

        @lru_cache(maxsize=None)
        def seq(p: Production, k: int, i: int, j: int) -> int:
            left = len(p) - k
            if left == 1:
                return sym(p[k], i, j)
            total = 0
            for m in range(i + 1, j - (left - 1) + 1):
                a = sym(p[k], i, m)
                if a:
                    total += a * seq(p, k + 1, m, j)
            return total

        if n == 0:
            return 0
        return sym(self.start, 0, n)

    # ------------------------------------------------------------------ generation
    def generate(self, max_len: int) -> Iterator[Tuple[str, ...]]:
        """All distinct terminal strings of length <= max_len (leftmost expansion with pruning)."""
        seen: Set[Tuple[str, ...]] = set()
        done: Set[Tuple[str, ...]] = set()
        todo: List[Tuple[str, ...]] = [(self.start,)]
        seen.add(todo[0])
        while todo:
            form = todo.pop()
            idx = next((k for k, s in enumerate(form) if s in self.rules), None)
            if idx is None:
                if form not in done:
                    done.add(form)
                    yield form
                continue
            for p in self.rules[form[idx]]:
                new = form[:idx] + p + form[idx + 1:]
                if len(new) <= max_len and new not in seen:
                    seen.add(new)
                    todo.append(new)
