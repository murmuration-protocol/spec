# Murmur canonical encoding rules

This document pins the canonical encoding: the exact byte form a Murmur artifact takes. It is normative. The specification governs the model; this document governs the bytes; the conformance vectors are the executable form of these rules and check them. Where this document and the vectors disagree, this document governs and the vector is corrected, by the precedence of specification Section 6.3: the text is normative, the suite checks it.

The governing requirement is **exactly one byte form per logical value**. Murmur artifacts are content-addressed and signed (specification Section 7.2), so a definition, a grant, or an attestation MUST encode to identical bytes in every implementation, or its hash and its signature stop verifying the moment it crosses a bridge. Every rule here exists to make that true. A decoder MUST reject a well-formed CBOR artifact that is not in this canonical form, rather than re-encode it to compare (specification Section 7.2).

This canonical form binds the **control plane**: contract definitions, grants, attestations, and the signed envelope. It does not bind the real-time data plane. A note stream, a sensor feed, or an actuator command rides its substrate raw and owes nothing to these rules (specification Section 5). The values pinned here are therefore declarations, authored by people and read by people, not sampled machine signals. That is why their conventions are chosen for exactness and legibility, not for machine arithmetic.

The encoding is deterministic CBOR (RFC 8949). This document restricts CBOR to a small deterministic subset and adds the value conventions below.

## Scope of this draft

This draft pins the **value domain**: the scalar values a canonical artifact may carry and how each reaches its single byte form. Four sections remain to be drafted, and the conformance vectors lead each:

- the permitted CBOR subset (the major types allowed, the ban on tags and indefinite lengths, the minimal-length rules), of which the existing `reject/` vectors already pin part;
- the map-key rules (single-type keys per map, integer keys for fixed schema fields, text keys for open name-indexed maps, no float, container, mixed, or duplicate keys, canonical ordering);
- the signed envelope and identifier layout, with the signed-input boundary;
- the algorithm-tag namespace and its reserved private range;
- the unit vocabulary that schema fields reference by code.

## Value domain

A declared deadline, rate, or threshold must mean one number and encode to one byte form. The rules below give each scalar value exactly one canonical encoding.

### No floating point

Floating-point values (CBOR major type 7 half, single, and double floats) MUST NOT appear in a canonical artifact. They round differently across platforms, they carry a negative zero and not-a-number forms with no single encoding, and a declared decimal such as `0.1` has no exact floating-point value. A float would reintroduce the rounding error this profile exists to exclude. Every magnitude a Murmur artifact declares is a measured or specified quantity of finite precision, which the exact forms below represent without loss.

### Integers

Integers use CBOR major type 0 (unsigned) and major type 1 (negative), minimally encoded: the shortest head that holds the value, never a longer one. A decoder MUST reject a non-minimal integer.

Plain integers carry **protocol-bounded magnitudes**: a format version, a sequence number, a fencing token, a lease or liveness interval in the protocol's own time base. The protocol sets the range of each, so there is nothing to foresee, and a 64-bit integer holds it.

### Domain-declared magnitudes

A magnitude whose range the domain sets, not the protocol, MUST NOT be pinned to a fixed unit chosen at design time. No single unit foresees the span from a keyboard to a substation, and the wrong choice forces a breaking schema change later. Such a magnitude is carried as a **base-10 decimal**: a two-element array `[scale, mantissa]`, both integers, denoting `mantissa` times ten raised to `scale`. A deadline of 150 milliseconds, in a field the schema declares to be in seconds, is `[-2, 15]`, read as fifteen times ten to the minus two.

The base is base 10 deliberately. These values originate in base 10, written by a person, so base 10 holds them exactly where binary scaling could not. Base 10 also represents every value binary scaling can, and more: any `m` times two to the `e` is `(m` times five to the `|e|)` times ten to the minus `|e|`, while `0.1` has no binary-scaled form at all. The cost of base 10 is arithmetic, which this layer does not perform. It carries and compares declared magnitudes, never computes on them (specification Section 7.3).

The decimal has exactly one canonical form, so content-addressing holds:

- the mantissa MUST NOT be divisible by 10, so trailing zeros are stripped and `[-2, 15]` is the only encoding of that quantity, never `[-3, 150]`;
- the mantissa carries the sign, so a negative quantity has a negative mantissa;
- zero is the single form `[0, 0]`;
- both elements are minimally encoded integers.

The decimal encodes a number, not a claim about significant figures. A declaration that must also state precision or tolerance carries that as a separate field. It is never smuggled into trailing zeros.

The decimal is self-describing in its **scale**, not in its **kind**. The scale travels with the value, so the magnitude's range need not be foreseen. The kind, that this field is a decimal at all, comes from the schema, not from a tag on the wire. This is the same discipline as the integer schema keys: the meaning of a field lives in the definition, not in the bytes.

### Rationals

A value that is an exact ratio rather than a finite decimal, a gear ratio or a sample-rate conversion, is carried as a **rational**: a two-element array `[numerator, denominator]`, both integers, denoting `numerator` divided by `denominator`. Use a rational only where the ratio is the meaning. A measured quantity of finite decimal precision is a decimal, not a rational. A ratio with no finite decimal form, such as one third, is exactly why the rational exists, since neither a decimal nor a binary float can hold it.

The rational has exactly one canonical form:

- the denominator MUST be positive and MUST NOT be zero;
- the numerator and denominator MUST be coprime, reduced by their greatest common divisor;
- the numerator carries the sign;
- zero is the single form `[0, 1]`;
- both elements are minimally encoded integers.

Neither the decimal nor the rational uses a CBOR tag. CBOR's tagged decimal-fraction, bigfloat, and bignum forms are excluded with all other tags by the CBOR subset rules. The element order matches CBOR's decimal-fraction convention, scale before mantissa, so a reimplementer reads it as familiar, but the construct is a bare two-element array recognized by its declared schema position, never by a tag. A reader that finds a two-element array where the schema declares a decimal interprets it as a decimal, and where the schema declares a rational interprets it as a rational. An implementation MUST NOT accept a decimal where a rational is declared, or the reverse.

### Units

The dimension and base unit of a domain-declared magnitude are part of the field's schema, declared once in the capability definition, never repeated in every value. The schema commits to a dimension and a base unit, for example a duration in seconds, and the decimal carries the magnitude in that unit. This is what lets the base unit stay broad while the value stays exact: the schema commits to seconds, and `[-2, 15]` expresses 0.15 of a second without the schema ever choosing milliseconds. A value MUST be interpreted in the dimension and base unit its schema declares, and an implementation MUST NOT carry a magnitude whose unit its schema does not fix.

A unit is referenced by a code from a controlled vocabulary, never written as a free-text unit string. In a content-addressed artifact a unit string would make case and character identity load-bearing, and units differ by exactly that: a gigabyte, a gibibyte, and a gigabit are GB, GiB, and Gb, three quantities a single character or a single case change apart. A hash that turns on whether an author typed GiB or GB is the silent ambiguity content-addressing exists to forbid. Derived and compound units carry the same hazard, since a frequency or a newton-metre has several plausible spellings and no canonical string, so they too are named entries in the vocabulary, not strings assembled on the wire. The unit vocabulary is stewarded like the algorithm-tag and profile registries, and is pinned among the sections still to draft (above).

### Human magnitude strings are an authoring input

A person authoring a definition writes magnitudes the legible way, `150ms`, `3h2m`, `1.6Hz`. These strings are an authoring-surface input (specification Section 7.1). The compiler parses them and emits the canonical decimal in the schema's base unit, and they never appear on the wire. The wire carries the magnitude as a decimal and the unit as a vocabulary code, so the canonical form turns on arithmetic and a controlled code, never on string formatting, character case, or one speller's choice of unit.

### Text and byte strings

- **Text strings** (CBOR major type 3) are valid UTF-8, minimally length-encoded, with no byte-order mark, and in **Unicode Normalization Form C** (NFC). They carry values meant to be read: a capability name, a profile name, a registry tag. A string that can take more than one byte form for the same text would break content-addressing, so exactly one normalization form is canonical, and a decoder MUST reject a text string that is not already in NFC rather than normalize it to compare, by the same rule that rejects non-canonical CBOR. NFC is the composed form that the web and Linux userland already assume, and is the W3C character-model recommendation. It is deliberately not the decomposed form (NFD) associated with the macOS filesystem, so that the common authoring environment emits canonical bytes by default. Protocol identifiers such as tags and profile names SHOULD additionally stay within a conservative character subset, ASCII where it suffices, which keeps the most load-bearing strings trivially canonical and spares a constrained device the Unicode tables a full NFC check would need.
- **Byte strings** (CBOR major type 2) carry opaque bytes: digests, keys, signatures. They are minimally length-encoded and carry no transformation. A digest or a key names its algorithm by the tag mechanism (specification Section 7.1), not by its length.

### Booleans, and the absence of null

Booleans are the CBOR simple values true and false. Null and undefined MUST NOT appear in a canonical artifact. An absent optional field is omitted entirely, never encoded as null, because "present and null" and "absent" would otherwise be two byte forms of the same absence.
