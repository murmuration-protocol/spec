#!/usr/bin/env python3
"""check-refs.py - verify every "Section N" / "Section N.M" cross-reference in
the docs resolves to a real heading in spec.md. The extensions and the primer
state their section references are to the core, so they are checked against
spec.md's headings too. This guards the renumber-debt the spec's section
numbering would otherwise accumulate silently. Runs from anywhere."""
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent

valid = set()
for line in (root / "spec.md").read_text().splitlines():
    m = re.match(r"^#{2,4} (\d+(?:\.\d+)*)\.? ", line)
    if m:
        valid.add(m.group(1))

ref_run = re.compile(r"\bSections?\s+(\d+(?:\.\d+)*(?:\s*(?:,\s*and|,|and|to)\s*\d+(?:\.\d+)*)*)")
num_tok = re.compile(r"\d+(?:\.\d+)*")

bad = []
paths = ["spec.md", "primer.md", "README.md"]
paths += sorted(str(p.relative_to(root)) for p in (root / "extensions").glob("*.md"))
for rel in paths:
    for n, line in enumerate((root / rel).read_text().splitlines(), 1):
        for run in ref_run.finditer(line):
            for tok in num_tok.findall(run.group(1)):
                if tok not in valid:
                    bad.append((rel, n, tok))

if bad:
    print("FAIL: section references with no matching heading in spec.md:\n")
    for rel, n, tok in bad:
        print(f"  {rel}:{n}  Section {tok}")
    sys.exit(1)
print(f"OK: every section reference resolves ({len(valid)} headings indexed).")
