# Murmur canonical encoding rules

This document pins the canonical encoding: the exact byte form a Murmur artifact takes. It is normative. The specification governs the model; this document governs the bytes; the conformance vectors are the executable form of these rules and check them. Where this document and the vectors disagree, this document governs and the vector is corrected, by the precedence of specification Section 6.3: the text is normative, the suite checks it.

The governing requirement is **exactly one byte form per logical value**. A Murmur artifact is named by a content address, the hash of its own bytes (specification Section 7.2). Without one canonical form, two implementations that encode the same logical artifact, a definition, a grant, or an attestation, would hash it to two different addresses, so its identity would fork along implementation lines instead of naming one thing, and it could not be rebuilt from its legible source and checked against its published address. Signing does not drive this. A signature is verified over the exact bytes received, never over a re-encoding of them, so authentication alone would tolerate a looser format. Content-addressed, reproducible identity is what requires the single byte form, and every rule here exists to make that one address reproducible across independent implementations. A decoder MUST reject a well-formed CBOR artifact that is not in this canonical form, rather than re-encode it to compare (specification Section 7.2).

This canonical form binds the **control plane**: contract definitions, grants, attestations, and the signed envelope. It does not bind the real-time data plane. A note stream, a sensor feed, or an actuator command rides its substrate raw and owes nothing to these rules (specification Section 5). The values pinned here are therefore declarations, authored by people and read by people, not sampled machine signals. That is why their conventions are chosen for exactness and legibility, not for machine arithmetic.

The encoding is deterministic CBOR (RFC 8949). This document restricts CBOR to a small deterministic subset and adds the value conventions below.

## Scope of this draft

This draft pins the canonical form in five parts: the **CBOR subset**, the structural rules every artifact obeys; the **value domain**, the scalar values it may carry, each in one byte form; the **map-key rules**, how a map's keys are typed and ordered; the **schema model**, how a field table gives bytes their meaning and how it differs from a distributed definition; and the **signed envelope and identifier layout**, the bytes a signature covers and the structure that names a key. Three sections remain to be drafted, and the conformance vectors lead each:

- the meta-table, and the field tables of the protocol artifact types it describes, the integer key each named field takes on the wire;
- the algorithm-tag namespace and its reserved private range;
- the unit vocabulary that schema fields reference by code.

## CBOR subset

Deterministic CBOR is RFC 8949 with its degrees of freedom removed. Plain CBOR can encode one logical value many ways: a tag or no tag, a short head or a padded one, a definite or an indefinite length, a float that compares equal to another but differs in bytes. Each such choice is a second byte form of one value, and each breaks content-addressing. This subset removes the choices, so a value has one structure and one length encoding before the value conventions below even apply. The rules track the core deterministic encoding of RFC 8949, narrowed further to the major types Murmur uses.

### One data item

A canonical artifact is exactly one CBOR data item. A decoder MUST consume the whole input as that single item and MUST reject any trailing byte, rather than stop at the first complete item and ignore the rest. Trailing bytes are how a second, unread value rides inside one that verifies, so an artifact that does not account for every byte is refused. The `reject/trailing-bytes` vector pins this.

### Permitted major types

Only these CBOR major types appear in a canonical artifact:

- **0** and **1**, unsigned and negative integers (Integers, below);
- **2**, byte strings (Text and byte strings, below);
- **3**, text strings (Text and byte strings, below);
- **4**, arrays;
- **5**, maps;
- **7** restricted to the two simple values true and false (Booleans, and the absence of null, below).

Every other use of major type 7 is excluded: the half, single, and double floats (No floating point, below), null and undefined (Booleans, and the absence of null, below), and every remaining simple value. Major type 6, the tag, is excluded entirely (No tags, below). A decoder MUST reject a major type, or a major-type-7 value, outside this list. The decimal and the rational are arrays of integers, not tagged numbers, so they need no type beyond the array and the integer.

### No tags

A CBOR tag (major type 6) MUST NOT appear in a canonical artifact. A tag is an optional annotation a decoder is free to ignore, so a value and its tagged form are two encodings of one thing. The meaning of a Murmur field comes from its schema position, never from a tag on the wire (Domain-declared magnitudes, below). The tagged decimal-fraction, bigfloat, and bignum forms are excluded by this rule, which is why the decimal and the rational are bare two-element arrays. An algorithm a digest or a key names is carried by the tag mechanism of specification Section 7.1, a field in the schema, not a CBOR tag.

### No indefinite lengths

Every byte string, text string, array, and map MUST carry a definite length in its head. The indefinite-length forms, and the break stop that closes them, MUST NOT appear, and a decoder MUST reject them. An indefinite length lets one value arrive as several chunks, which is a second byte form and a streaming-decode hazard at once. The `reject/indefinite-length-array` vector pins this.

### Minimal encoding

The head of every item MUST use the shortest of CBOR's argument forms that holds its value: the immediate form for an argument under 24, then the one, two, four, and eight byte forms in turn, never a longer head where a shorter one fits. This is one rule with a wide reach. It governs an integer value, a string or container length, and the element count of an array or map alike, because each is a CBOR argument. The value 0 is the single byte `0x00`, never `0x18 0x00`. A length of ten lives in the head, never in a longer following field. A decoder MUST reject a non-minimal head. The `reject/non-minimal-uint` vector pins the integer case; the rule is identical for every length and count.

### Maps and ordering

A map is structurally a definite-length, minimally headed container like any other, and this subset governs that framing. Its keys carry further rules: the permitted key types, the single key type per map, the ban on duplicates, and the canonical sort by encoded key bytes. Those belong to the Map keys section (below), and the `reject/duplicate-map-key` and `reject/unsorted-map-keys` vectors already exercise them. The key rules are kept distinct from the framing rule because a key's type and order are value conventions, not container structure.

### Bounded structure

Nesting is finite, and decoding it is resource-bounded. A canonical artifact has no cyclic or self-referential structure, since CBOR has none, but adversarial input can still nest arrays and maps deeply enough to exhaust a constrained decoder. Decoding MUST be bounded in memory and time under a declared limit, and MUST fail to the declared safe state when the limit is exceeded, by the input-cost rule of specification Section 7.3. A bound on nesting depth is the structural half of that rule.

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

### Structure on the wire, meaning in the schema

A canonical artifact is self-describing in its structure and silent on its meaning. The CBOR major type on the wire fixes what a value is structurally: an integer, a byte string, a text string, an array, a map, or a boolean. What that structure means, which field it is, what dimension it carries, and which of several constructs that share a shape it represents, comes from the value's position in the schema, never from the bytes. This is the reason there are no tags (No tags, above). A tag would place meaning on the wire, where it becomes a second thing a decoder is free to read or ignore.

The sharpest case is the decimal and the rational. Both are a two-element array of integers (Rationals, above), indistinguishable as bytes, and the schema position alone says which a given array is. The integer schema keys are the same discipline at the level of a field name (Map keys, below): field 1 is whatever the definition says, and renaming it in the authoring surface leaves the wire unchanged. The structure is on the wire and the meaning is in the definition.

The line sits exactly at the CBOR major type, and is deliberately not pushed below it. A format could carry less structure still, collapsing a text string and a byte string onto one length-delimited form and letting the schema decide which a field is, as Protocol Buffers does. Murmur does not, for three reasons rooted in content-addressing. First, a text string carries a canonicalization a byte string does not: valid UTF-8 in Normalization Form C, refused on receipt otherwise (Text and byte strings, above). A party that does not hold the schema could then no longer tell whether the bytes are the one canonical form. Second, that ambiguity forks the content address. A producer that does not know a field is text may emit the decomposed form where one that knows emits the composed form. A single logical value then earns two addresses, the fork the canonical form exists to forbid. Third, it opens a type confusion of the family the envelope's anti-negotiation posture closes (Signed envelope and identifier, below). One octet sequence would read as opaque bytes to one party and as a command string to another. The major type costs nothing to keep, since it already rides in the CBOR head, so dropping it saves no bytes.

Protocol Buffers can reinterpret a field across this line because it never promises a canonical byte form, nor a hash taken over its own bytes. It pays for schema-driven structure with a non-deterministic encoding, the freedom this profile exists to remove. Meaning-level canonicality is in any case already the schema's to decide here: the array [2, 10] is canonical as a plain pair of integers, non-canonical as a decimal, and non-canonical as a rational. That dependence is the minimum the no-tags rule forces, not a licence to widen it. Structure stays on the wire.

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

## Map keys

A map is how a Murmur schema names its fields. Its framing is pinned in the CBOR subset above; its keys carry the further rules that give a named structure exactly one byte form: a single key type, no duplicate, and one canonical order.

### One key type per map

Every key in a map MUST be the same type, and that type MUST be either an integer or a text string. A map MUST NOT mix integer and text keys, and a decoder MUST reject one that does. The other canonical types are valid as values but never as keys: no byte string, array, map, or boolean names a field, because a field name is a number or a word, never a digest, a list, or a flag. Floats are excluded everywhere already (No floating point, above).

The two key types are the two ways a map is addressed, and the schema fixes which a given map uses:

- **Integer keys** index a **fixed schema**, a field set known when the definition is authored. Each field is named by a small integer that is its identity for the life of the schema. These are the **integer schema keys** the value domain refers to: the meaning of field 1 lives in the definition, not in any string on the wire. Renaming a field in the authoring surface leaves the same integer on the wire, and an integer is one byte where a name would be many.
- **Text keys** index an **open, name-indexed map**, a set whose members are not fixed at design time, such as a table of capability names or registry tags. The key is a text string under the text-string rules (Text and byte strings, above), valid UTF-8 in Normalization Form C, so two authorings of the same name are the same key.

The choice between integer and text keys is the schema's, made once per map when the definition is authored, never varied from one artifact to the next.

### No duplicate keys

A map MUST NOT carry the same key twice, and a decoder MUST reject one that does, rather than keep the first entry or the last. A duplicate makes a field's value ambiguous, and the rule that resolves it, first-wins or last-wins, is an implementation choice. That choice is exactly the second reading this profile exists to forbid. Because every key is itself minimally encoded, and a text key is in Normalization Form C, two keys are the same key precisely when their encoded bytes are equal, with no further comparison needed. The `reject/duplicate-map-key` vector pins this.

### Canonical order

The keys of a map MUST appear in ascending bytewise lexicographic order of their encoded form: the encoded keys are compared as unsigned bytes, left to right, and the shorter sorts first where one is a prefix of the other. This is the map ordering of the core deterministic encoding of RFC 8949. A decoder MUST reject a map whose keys are out of this order. The `reject/unsorted-map-keys` vector pins this.

The order is taken on the encoded key bytes, not on the decoded value, so a decoder checks it by comparing raw bytes as it reads, without interpreting a single key. For the integer keys of a fixed schema this is the plain numeric order, since a minimally encoded non-negative integer sorts bytewise exactly as it sorts by magnitude. For the text keys of an open map it is the bytewise order of the UTF-8. A map carries one key type, so the two orders never have to be reconciled against each other.

## Schemas and field tables

The principle that structure rides on the wire and meaning comes from the schema (Structure on the wire, meaning in the schema, above) raises the obvious question: where does the schema itself live, and how does a decoder come to hold it. The answer separates two kinds of schema that must never collapse (the separation law, specification Section 1).

### Two kinds of schema

A **field table** is the wire schema of an artifact type. It is a flat list, one entry per field, each entry fixing an integer key, a field name, a canonical type from the value domain above, and whether the field must be present to act (Field-table entries, below). There is one table per protocol artifact type: the signed envelope, the issuer identifier, the grant, the delegation, the capability definition, the safe-state definition, the steward schema, the discovery record. These tables are the grammar of the protocol. They are identical in every implementation and fixed for a given format version. An implementation holds them from the specification at build time, and does not fetch one at runtime to decide authority (The floor is shipped, not fetched, below).

A **definition** is a content-addressed artifact encoded against a field table, carrying the data a deployment varies, a particular capability or a particular steward schema. A definition is distributed as specification Section 7.2 describes, by content address, from the commons or a peer or a USB stick, and referenced by the hash of its own bytes. A grant names the capability it grants by that hash, never by copying it.

This is the answer to how the schema is distributed. The field tables are not distributed, because they are the protocol. The definitions are distributed, because they are not. A relay that forwards a grant it cannot interpret forwards the content-addressed bytes and checks their hash, never decoding the grant's fields, so it needs neither the capability definition the grant names nor the grant table itself.

### The floor is shipped, not fetched

A field table could in principle be written as a canonical artifact, content-addressed and fetched like a definition. That path does not terminate. To decode the fetched table, a decoder needs a table for tables, itself an artifact needing a table, without end. Every format that meets this regress stops it at a fixed floor it ships rather than fetches. The CBOR grammar is RFC 8949, not a fetched description of CBOR. The DNS root is configured, not resolved. A compiler is bootstrapped, not compiled by itself. Murmur's floor is the canonical-encoding rules of this document, the **meta-table** that describes the shape of a field table, and the format version that fixes which rules are in force (specification Section 7.1). That floor is built into every implementation. It is the smallest grammar a node must be born knowing, and on it every other table is data.

On that floor, every protocol artifact table, the envelope, the grant, the capability definition, and the rest, is itself a canonical artifact, an instance of the meta-table with a content address of its own. The tables are authored once, in this specification and its conformance vectors, and an implementation reads them from there rather than transcribing each into its own types by hand. This is adopted, not deferred. At this early stage the tables will change often. A single authored source that every implementation reads is what keeps two implementations from drifting, and what makes a new field a one-artifact change rather than a parallel edit in every language. A change to a table is a change to the grammar, governed by the format version and the validation rules of the next section (Decode, then validate, below).

A table is held, never fetched to decide authority. An implementation's acting decoder is driven only by the tables it holds at build time, the published tables for the format versions it implements. So a node can always state which shapes it will act on, and a shape it was not built for is refused and falls to its safe state, never fetched and then acted on (Decode, then validate, below). An acting node MUST NOT gain the ability to parse a shape it cannot yet honour, which is why a new table ships in the same release as the code that honours it. Only a read-only consumer, a diagnostic or a lint that displays or checks an artifact without acting on it, MAY load a table at runtime, since displaying an unknown shape is safe where acting on it is not.

Whether an implementation drives its decoder from the tables as data or compiles them into its types is a choice below the contract line, and does not change the bytes. The byte contract is the table, not the strategy that reads it. A reference implementation that reads the tables as data takes a table change without a code change; the witness, with one fixed capability, may compile them in. Both are conformant, because both decode the same bytes.

### Field-table entries

Each entry in a field table fixes four things and no more:

- an **integer key**, the field's identity on the wire for the life of the format version, never reused;
- a **name**, the field's identity in the authoring surface and in this specification, with no presence on the wire (Structure on the wire, meaning in the schema, above);
- a **type**, exactly one canonical value-domain type from above: an integer, a byte string, a text string, an array, a map, a boolean, a decimal, or a rational. A decimal or rational field also fixes its dimension and base unit (Units, above);
- a **presence rule**, whether the field must be present for a party to act on the artifact. This is a validation property, not a decoding one (Decode, then validate, below).

### Decode, then validate

A decoder's work is structural and total. It reads the canonical bytes into typed fields, enforces the rules of this document, and rejects non-canonical bytes (specification Section 7.2). It does not reject an artifact for a missing named field, because a missing field is not a malformed encoding.

Presence is enforced one step later, by the party about to act on the artifact, against the field table for the artifact's type and format version. A verifier about to exercise a grant requires the issuer, the audience, the capability, and the signature, since its security rests on them, and refuses a grant lacking them at that gate, not at the decoder. A relay forwarding the same grant requires none of them. Required-ness is scoped to an action and a role, never asserted of the artifact's mere existence.

This is the lesson of proto3, which removed the required field its predecessor carried. In a format that evolves a type in place, a presence check welded into the decoder is permanent and global. A field once required can never be relaxed without a coordinated migration, and a decoder that rejects on a missing field lets one party's requirement wedge every reader that does not use that field. Murmur avoids the trap from both sides. It does not weld presence into the decoder, so a missing field never wedges a forwarder. And it does not evolve a type in place: a changed field set is a new format version, understood or refused as a whole (specification Section 7.1), under a table closed per version, so an unexpected key is non-conformant rather than a tolerated unknown. The escape proto2 lacked, a version a reader either understands entirely or refuses, Murmur has by construction.

One half of the presence question Murmur settles in its own favour. An absent field is omitted entirely, never encoded as a default value or a null (Booleans, and the absence of null, above), so "present with the default" and "absent" are never two readings of one state. That ambiguity is what forced an explicit presence marker back into proto3 after it was removed. The canonical form does not have it to fix.

## Signed envelope and identifier

A signed artifact is claims plus a proof of who authored them. The claims are a canonical-CBOR map under the rules above. The proof is a signature over those claims by a key the reader can name and trust. This section pins the envelope that joins the two, and the identifier that names the key. It is the one part of the canonical form where a wrong byte boundary is a forgery and not a mismatch, so the boundary is stated exactly. The envelope is a minimal owned shape, a CBOR Web Token in all but the COSE wrapper (specification Section 7.1). COSE was declined as heavier than the requirement and unable to enforce the exactly-one-encoding rule that content-addressing needs.

### The signed input

The signature covers one canonical-CBOR **signing input**: the header and the claims together, in a field layout the conformance vectors pin. The header carries the format version and the issuer identifier. Placing both inside the signed bytes is what binds them. The version cannot be swapped to reinterpret the layout, and the issuer cannot be swapped to reattribute the claims, because either change invalidates the signature (specification Section 7.1). Only the signature byte string sits outside the signing input, since a signature cannot cover itself, and it rides alongside the signing input in the envelope.

The signature is verified over the signing input exactly as received, never over a re-encoding of it. A verifier MUST NOT decode the artifact and re-encode it to obtain the bytes to check, because that puts its own encoder in the trusted path, where an encoder bug becomes a refused-but-valid signature or an accepted forgery. Canonicality is enforced as a separate gate: a decoder that finds the signing input non-canonical rejects it outright, before any signature check, by the receipt rule (specification Section 7.2). The signature is therefore checked against the exact bytes that arrived, and those bytes are already known to be canonical, because a non-canonical artifact never reaches the check.

This is the posture a non-canonical format such as JSON must also take, signing and verifying the exact transmitted octets, since a re-encoding could differ. Authentication needs nothing more, and the single requirement canonicality adds, that those octets be the one valid byte form, does no work for the signature. It works for the content address (specification Section 7.2). Because every producer of the same logical artifact emits the same bytes, the artifact has one address across all of them, so its identity is reproducible by an independent implementation rather than tied to whoever first serialized it. That reproducibility, not the signature, is what the canonical form is bought for.

### The content address

An addressed artifact, such as a published capability definition, also carries a **content address**: a hash that names it independently of who signed it. The hash is taken over the claims body, so the same logical definition encodes to the same address regardless of its publisher (specification Section 7.2). That producer-independence is what lets a definition verify the same from the commons, a peer, or a USB stick, with no origin server alive. The signature and the content address are two operations with two purposes, authentication and naming, and they are kept distinct: the signature covers the header and the claims so the author and the version are bound, the address covers the claims body so it stays the same across authors.

The address names its own hash algorithm in the reference that resolves it, taken from that trusted reference and never from the fetched bytes, so a substituted artifact cannot redirect verification to a weaker hash (specification Section 7.2). Any transport compression is outside this form, and is reversed before the hash or the signature is checked.

### Algorithm rides with identity, not with the envelope

The envelope carries no negotiable algorithm field. The signature algorithm is the one the issuer identifier declares (specification Section 3), and the hash algorithm is the one the content-address reference declares (specification Section 7.1). This is the PASETO posture: anti-negotiation realized by binding the algorithm to the identity, not by a cipher-suite field an attacker could set. The `alg: none` forgery and the key-confusion attack both need such a field, and the layout offers none to set.

The format version sits in the signed input, and each algorithm tag sits where altering it breaks verification rather than redirects it: the signature algorithm in the issuer identifier the signature covers, the hash algorithm in the address reference the hash answers to (specification Section 7.1). The four anti-forgery rules of specification Section 7.1 follow from this layout, and the suite pins them as the algorithm-agility negative cases: there is no unsecured form, the algorithm is taken from the trusted anchor and never from the artifact under test, one key bears one algorithm, and a verifier enforces a local allowlist so downgrade-resistance is the verifier's to keep. The format version is a single integer, incremented only when these canonical rules or the envelope layout change, and a reader that does not recognize the version rejects the artifact rather than guess its layout.

### Identifier layout

The issuer identifier names the signing key in a self-describing, algorithm-tagged byte structure (specification Section 3). It carries two tags, kept distinct because they vary independently (the separation law, specification Section 1):

- a **form tag**, selecting one of the three identifier forms;
- an **algorithm tag**, naming the digest or key algorithm the form uses, drawn from the same namespace as the envelope and content-address tags.

The three forms are one construction at three depths of history, the general shape with its degenerate cases (the degenerate-case law, specification Section 1):

- the **rotation-surviving** form carries the digest of an inception event. The stable identifier is that digest, and a hash-linked key-event log, supplied alongside for verification, carries each rotation forward, so the identity outlives any single key.
- the **digest-of-key** form carries a digest of the public key. It is the rotation-surviving form with an empty history, and the key is supplied alongside to check against the digest.
- the **raw-key** form carries the encoded public key itself, the digest elided. It is self-contained but welded to one key algorithm.

In every form the identifier is the compact, stable name. The bulky material it commits to, the key or the key-event log, travels alongside it in discovery or in the envelope, never inside the identifier, and a verifier accepts that material only when it hashes to the identifier. A digest identifier is welded to the hash that minted it, whose forgery resistance rests on second-preimage resistance, the property that outlives broken collision resistance (specification Section 3).

The exact field order, the tag integers, and the encoding of each form are pinned by the conformance vectors and the algorithm-tag namespace, the next section to draft (open question 11). The existing `envelope/` vectors pin the verifiable core beneath this layout: a deterministic Ed25519 signature over canonical-CBOR claims, checked both as reproducible bytes and as a verify verdict. They sign the bare claims, the signing primitive, and the full envelope wraps that primitive with the header pinned here.
