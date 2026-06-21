# Conformance vectors

The vectors are the normative, language-neutral definition of the Murmur byte contract (Section 6.3). They live with the specification, not with any implementation, because a canonical encoding proven by a single implementation is unfalsifiable: it only ever agrees with itself. Two implementations checking the same vectors, each verifying artifacts the other signed, is what makes the contract real.

These are the core encoding vectors: canonical CBOR, content-addressing, and the signed envelope (Section 7.2). Per-profile vectors, such as the carried-content round trip and fencing-token pass-through, are a profile's own conformance unit and live with the profile, not here.

## Layout

One vector per file. A change or an addition touches exactly one file, so diffs stay legible and there is no shared array to conflict on. The directory names the category; the file's own `kind` is authoritative. There is no manifest: a runner globs the tree and dispatches on `kind`.

```
vectors/
  encode/        a value and its one canonical CBOR byte form
  content-id/    canonical bytes and their SHA-256 content address
  envelope/      the signed envelope: a byte-pinned signature, and verify cases
  reject/        valid CBOR that is non-canonical and must be refused on receipt
```

## File shape

Every file is a JSON object, self-describing, with a fixed field order: `kind`, `description`, `spec`, then inputs, then expected results. All byte-valued fields are lowercase hexadecimal strings, never JSON numbers. Small counters stay plain integers.

One split is worth keeping. Vectors against a fixed Murmur schema, such as a grant or a capability definition, carry a friendly named-field `value`, because the mapping from field name to CBOR key lives in the implementation, not the fixture. Vectors against the raw canonical-CBOR rules carry only hex, because there is no schema, just bytes and a verdict. The reject vectors are the second kind, and they are the most load-bearing: they are what makes "exactly one byte form is valid" (Section 7.2) falsifiable rather than aspirational.

### Kinds

- `encode`: a `value` and its expected canonical `cbor`. Checked both ways, value to bytes and bytes to value.
- `content-id`: canonical `cbor` and its expected `sha256` content address.
- `envelope-sign`: a `seed`, the `claims_cbor` that is signed, and the expected `signature`. Ed25519 signing is deterministic (RFC 8032), so the signature bytes are reproducible across implementations and can be pinned, not merely verified.
- `envelope-verify`: a `public_key`, `claims_cbor`, a `signature`, and a `valid` verdict. The negative cases, a flipped byte or a wrong key, carry `valid: false`.
- `reject`: the offending `bytes` and a `reason`. A conformant decoder refuses them rather than re-encoding to compare (Section 7.2).

The signed envelope on the wire is the canonical claims, an Ed25519 signature, and a small header. The exact bytes the signature covers, including whether the header is part of the signed input, are pinned with the envelope schema. These vectors sign the canonical claims directly, as the verifiable core.

## Formatting

- Two-space indent, LF line endings, one trailing newline.
- Every file opens with the same header, `kind`, `description`, `spec`, in that order. The kind-specific fields follow in a stable authored order.
- Byte fields are the only place raw bytes live; everything else is human-readable.

`tools/check-vectors.py` enforces all of the above, including that each file already equals its canonical re-serialization, so a regeneration cannot churn unrelated lines. It is standard-library Python with no dependencies, matching the other lints in `tools/`.

## How implementations consume them

Both `murmur-rs`, the reference implementation, and `murmur-go`, the conformance oracle, read this directory and run every vector. The cross-test runs each direction: one implementation signs, the other verifies, byte-identical. The vectors are the contract; the implementations are parties to it.

## Status

This is the first scaffold, and the byte values are real and self-checking. The Ed25519 public key matches RFC 8032 Test 1, and the reject cases follow the canonical CBOR rules of RFC 8949. The wire encoding is mandated by the spec (Section 7.1): deterministic CBOR with an owned signed envelope, versioned and algorithm-tagged. Schema-level vectors, a real grant and a real capability definition, land once those field tables are pinned.
