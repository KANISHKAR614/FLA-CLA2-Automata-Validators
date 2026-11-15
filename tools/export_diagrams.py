"""Write Graphviz .dot files (and PNGs when `dot` is installed) for every automaton, plus the JSON
tables used by the browser demo.

    python tools/export_diagrams.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from task2 import ALL  # noqa: E402
from task3 import build_html_pda, build_json_pda, build_stmt_pda  # noqa: E402

OUT = ROOT / "docs" / "diagrams"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = {}
    for key, build in ALL.items():
        jobs[f"task2_{key}_dfa"] = build().to_dot()
    jobs["task3_html_dpda"] = build_html_pda().to_dot()
    jobs["task3_stmt_pda"] = build_stmt_pda().to_dot()
    jobs["task3_json_dpda"] = build_json_pda().to_dot()
    have_dot = shutil.which("dot") is not None
    for name, dot in jobs.items():
        path = OUT / f"{name}.dot"
        path.write_text(dot, encoding="utf-8")
        if have_dot:
            subprocess.run(["dot", "-Tpng", str(path), "-o", str(OUT / f"{name}.png")], check=True)
    tables = {key: build().to_json() for key, build in ALL.items()}
    (ROOT / "docs" / "dfa_tables.json").write_text(json.dumps(tables, indent=1), encoding="utf-8")
    template = (ROOT / "tools" / "demo_template.html").read_text(encoding="utf-8")
    (ROOT / "docs" / "demo.html").write_text(template.replace("/*TABLES*/", json.dumps(tables)), encoding="utf-8")
    print(f"wrote {len(jobs)} diagrams to {OUT.relative_to(ROOT)}"
          f"{'' if have_dot else ' (Graphviz not found: .dot only)'} and docs/dfa_tables.json")


if __name__ == "__main__":
    main()
