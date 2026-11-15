# Finite Automata and Pushdown Automata for Real-World Validation and Syntax Checking

Code companion to the course assignment report for **21CSC301T - Formal Language and Automata**
(CLA-2, Tasks 2 and 3, individual work).

- **Author:** Kanishkar S (RA2411026050169)
- **Guide:** Mr. P. Dinesh, Assistant Professor, Department of SOC
- **Institution:** School of Computing, SRM Institute of Science and Technology, Tiruchirappalli

Every automaton in the report is implemented here, runs from the command line, and is checked by tests
that compare it with an independently written reference. Pure Python 3.9+, **no third-party packages**.

## What is in the repository

| Part | Model | Report section | Module |
|---|---|---|---|
| Task 2 | Indian mobile number, 15-state DFA | 2.1, Table 2 | `task2/mobile.py` |
| Task 2 | Vehicle registration (RTO format), NFA -> 12-state DFA | 2.2, Table 4 | `task2/vehicle.py` |
| Task 2 | Date of birth DD/MM/YYYY, 15-state DFA | 2.3, Table 6 | `task2/dob.py` |
| Task 2 | Semantic stage (leap year, state codes, OTP note) | 1.2, 2.4 | `task2/semantic.py` |
| Task 3 | Nested HTML/XML tags, 3-state DPDA | 3.1, Table 9 | `task3/html_tags.py` |
| Task 3 | if-else / while, dangling-else grammar fix, top-down PDA | 3.2, Table 11 | `task3/stmt.py` |
| Task 3 | JSON-like objects/arrays, 8-state DPDA | 3.3, Table 13 | `task3/json_pda.py` |

The shared toolkit lives in `fla/`: `DFA` (character classifier, trap state, tracing, minimisation, Graphviz
export), `NFA` (epsilon moves, subset construction), `PDA` (instantaneous-description simulator, determinism
check) and `CFG` (text parser, CFG -> PDA, parse-tree counting, bounded string generation).

```
FLA-CLA2-Automata-Validators/
├── fla/                  # reusable automata library
├── task2/                # three DFAs + semantic checks + CLI
├── task3/                # three PDA case studies + CLI
├── tests/                # unittest suites (differential tests)
├── tools/                # diagram / browser-demo generator
└── docs/                 # generated diagrams (.dot/.png), dfa_tables.json, demo.html
```

## Quick start

```bash
git clone https://github.com/<your-username>/FLA-CLA2-Automata-Validators.git
cd FLA-CLA2-Automata-Validators
python3 -m unittest discover -s tests -t .      # 37 tests, a few seconds
```

### Task 2 - finite automata

```bash
python3 -m task2.cli mobile +919876543210
python3 -m task2.cli vehicle TN45ABC1234 --trace        # step-by-step state trace, ends in qD
python3 -m task2.cli dob 30/02/2026 --semantic          # DFA accepts, semantic stage rejects
python3 -m task2.cli table                              # accepted / rejected test tables
python3 -m task2.cli stats                              # state counts + NFA -> DFA subsets
```

### Task 3 - pushdown automata

```bash
python3 -m task3.cli html "<p><b></b><i></i></p>" --trace
python3 -m task3.cli html "<b><i></b></i>" --trace      # crossed tags: no move for </b> with I on top
python3 -m task3.cli stmt "if ( C ) if ( C ) a else a"
python3 -m task3.cli json '{"k":[1,{}]}' --trace        # reproduces the ID trace in the report
python3 -m task3.cli table
python3 -m task3.cli ambiguity                          # parse-tree counts: naive vs revised grammars
python3 -m task3.cli grammar                            # grammars + DPDA / NPDA determinism
```

Sample output (JSON trace, identical to the report's instantaneous descriptions):

```
JSON structure validator on { k : [ v , { } ] }
     (q0, { k : [ v , { } ] }, Z0)
  |- (qobj0, k : [ v , { } ] }, B Z0)
  |- (qkey, : [ v , { } ] }, B Z0)
  ...
  |- (qf, eps, Z0)
  ACCEPTED: input exhausted in an accepting state
```

### Diagrams and browser demo

```bash
python3 tools/export_diagrams.py     # writes docs/diagrams/*.dot (+ .png if Graphviz is installed)
```

Open `docs/demo.html` in any browser: pick an application, type a string, and watch the transition trace
update as you type (the transition tables are embedded in the page).

## How the three-stage architecture maps to the code

1. **Classifier** - each DFA has a `classify(char)` function (digits 6-9 -> `H6/N9`, `A-Z` -> `U`, ...).
2. **Automaton** - `DFA.accepts` / `PDA.accepts` decide syntactic well-formedness only.
3. **Semantic engine** - `task2/semantic.py` shows what must happen *after* acceptance: month lengths and leap
   years, state-code lookup, non-zero serial, OTP for live mobile lines. (The state-code table is an illustrative
   subset; real systems query the Vahan database.)

## Test strategy

| Check | How |
|---|---|
| DFAs vs regex | 40k mutated mobile numbers, 20k vehicle plates, 30k dates, every day/month pair 00-99, all short strings |
| NFA = subset DFA = hand DFA | vehicle NFA (11 states) -> 11 live subset states, `{n5,n6}` is the only merged subset |
| State counts | 15 / 12 / 15 asserted, and minimisation keeps them minimal |
| HTML DPDA vs stack checker | every token string up to length 6, plus mutated long strings |
| Grammar vs PDA | every string generated by `G_html`, `G_stmt`, `G_json` is accepted and has exactly one parse tree |
| Dangling else | `G_amb` has 2 trees for `if (C) if (C) a else a`, `G_stmt` has 1, and both grammars generate the same language |
| JSON DPDA vs recursive descent | every token string up to length 6; real JSON text and mutations compared with `json.loads` |
| Determinism | HTML and JSON machines are DPDAs; the top-down if-else PDA is reported as nondeterministic |

CFG ambiguity is undecidable in general, so the `ambiguity` command counts parse trees of every generated
string up to a length bound. That is evidence, not a proof; the proofs are in the report.

## Limitations (by design)

- The automata check **syntax** only. Active phone lines, valid RTO codes, calendar validity of DOB and
  duplicate JSON keys belong to the semantic stage.
- The HTML model covers `<b>`, `<i>`, `<p>` only; the statement checker works on the token notation of the
  report (`if ( C ) a else a`), not on raw source code.
- The JSON lexer maps any string followed by `:` to a key and every other primitive to `v`; it does not
  validate number or escape syntax beyond a basic pattern.

## References

1. Hopcroft, Motwani, Ullman, *Introduction to Automata Theory, Languages, and Computation*, 3rd ed., 2007.
2. Aho, Lam, Sethi, Ullman, *Compilers: Principles, Techniques, and Tools*, 2nd ed., 2007.
3. Sipser, *Introduction to the Theory of Computation*, 3rd ed., 2013.
4. DoT, *National Numbering Plan*; MoRTH, *Central Motor Vehicles Rules, 1989*, Rule 50.
5. ISO 8601-1:2019; W3C XML 1.0 (5th ed.); IETF RFC 8259 (JSON).

## License

MIT - see `LICENSE`.
