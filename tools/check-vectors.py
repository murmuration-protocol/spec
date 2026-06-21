#!/usr/bin/env python3
"""check-vectors.py - validate the conformance vector corpus under vectors/.

Each vector is one JSON file. This lint enforces the corpus contract so the
files stay legible in diffs and self-describing when read alone:

  - the file parses as JSON and uses LF line endings;
  - it carries a known "kind" that matches its directory;
  - it has a non-empty "description" and a "spec" reference;
  - its first three fields are "kind", "description", "spec", in that order;
  - the fields a given kind requires are present;
  - every byte-valued field is lowercase hexadecimal of even length;
  - the file is already in the canonical 2-space form, so re-serializing it is
    a no-op and a regeneration never churns unrelated lines.

Standard library only, by design, matching the other lints in tools/. Runs from
anywhere."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VECTORS = ROOT / "vectors"

# A directory name maps to the set of kinds allowed to live in it.
DIR_KINDS = {
    "encode": {"encode"},
    "content-id": {"content-id"},
    "envelope": {"envelope-sign", "envelope-verify"},
    "reject": {"reject"},
}

# Fields each kind must carry, on top of the common kind/description/spec.
REQUIRED = {
    "encode": ["value", "cbor"],
    "content-id": ["cbor", "sha256"],
    "envelope-sign": ["seed", "claims_cbor", "public_key", "signature"],
    "envelope-verify": ["public_key", "claims_cbor", "signature", "valid"],
    "reject": ["bytes", "reason"],
}

# Every field whose value is raw bytes, expressed as lowercase hex.
HEX_FIELDS = {"cbor", "bytes", "sha256", "public_key", "signature", "seed", "claims_cbor"}

# Every vector opens with this header, in this order, so files read alike.
# json.dumps preserves insertion order (sort_keys is left False), so this is
# what pins the order rather than any sorting step.
HEADER = ["kind", "description", "spec"]

HEXDIGITS = set("0123456789abcdef")


def is_hex(value):
    return (
        isinstance(value, str)
        and value != ""
        and len(value) % 2 == 0
        and all(c in HEXDIGITS for c in value)
    )


def main():
    if not VECTORS.is_dir():
        print("OK: no vectors/ directory to check.")
        return 0

    errors = []
    count = 0
    for path in sorted(VECTORS.rglob("*.json")):
        rel = path.relative_to(ROOT)
        text = path.read_bytes().decode("utf-8")

        if "\r" in text:
            errors.append(f"  {rel}: uses CR; line endings must be LF")

        try:
            obj = json.loads(text)
        except json.JSONDecodeError as e:
            errors.append(f"  {rel}: is not valid JSON ({e})")
            continue
        count += 1

        if not isinstance(obj, dict):
            errors.append(f"  {rel}: top level must be a JSON object")
            continue

        kind = obj.get("kind")
        parent = path.parent.name
        allowed = DIR_KINDS.get(parent)
        if allowed is None:
            errors.append(f"  {rel}: is in unknown directory '{parent}/'")
        elif kind not in allowed:
            errors.append(
                f"  {rel}: kind '{kind}' not allowed in '{parent}/' "
                f"(expected one of {sorted(allowed)})"
            )

        if not obj.get("description"):
            errors.append(f"  {rel}: missing a non-empty 'description'")
        if not obj.get("spec"):
            errors.append(f"  {rel}: missing a 'spec' reference")
        if list(obj.keys())[:3] != HEADER:
            errors.append(
                f"  {rel}: first fields must be {HEADER} in order, "
                f"found {list(obj.keys())[:3]}"
            )

        for field in REQUIRED.get(kind, []):
            if field not in obj:
                errors.append(f"  {rel}: kind '{kind}' requires field '{field}'")

        for field in HEX_FIELDS:
            if field in obj and not is_hex(obj[field]):
                errors.append(f"  {rel}: field '{field}' must be lowercase hex of even length")

        canonical = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
        if text != canonical:
            errors.append(
                f"  {rel}: not in canonical 2-space form (see vectors/README.md)"
            )

    if errors:
        print("FAIL: conformance vector corpus has problems:\n")
        print("\n".join(errors))
        return 1
    print(f"OK: {count} conformance vectors valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
