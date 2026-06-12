# Contributing to Murmuration

Murmuration is offered early, at the point where it is still shapeable. The most valuable contribution it can receive is a good objection. This document explains what the project is looking for and the conventions that keep it legible.

## What this repository is

This is the specification repository. It holds three documents: the [README](README.md), the idea in plain language; the [specification](spec.md), the normative contract model; and the [primer](primer.md), the non-normative rationale. There is no implementation here. The reference daemon, `murmurd`, lives in a separate repository and is being built around the first demonstration.

The specification is normative and uses RFC 2119 keywords. The primer explains why the specification is shaped the way it is. Where the two appear to disagree, the specification wins.

## What contributions are most useful

The project is early exploration, not a 1.0, and its open questions are stated honestly rather than hidden. Three kinds of contribution are worth more than the rest, in rough order:

1. **Objections to the open questions.** The specification collects its unresolved design forks in Section 18. These are real, load-bearing, and meant to stay visible. A well-argued objection to any of them is the single most useful thing the project can receive.
2. **Field accounts from domains that feel the pain.** Embedded fleets, shared physical resources, updates that cascaded into failure: first-hand accounts of where the underlying problem bites sharpen the design more than speculation can.
3. **Demonstrations that extend the witness.** The first demonstration occupies the easiest corner of every hard problem. A demonstration that carries the contract model into a harder corner (loss, growth, fan-out, multi-principal) is a direct contribution to the roadmap.

Refinements to the prose, corrections, and clarifications are welcome. So is disagreement with the framing itself.

## How to engage

The project keeps debate and actionable change in separate places, on purpose.

- **Discussions** are for the open questions and for design debate. To object to an open question, open a discussion in the Open Questions category and reference its number from Section 18 of the specification. An open question has no "done" state; it is resolved by argument, and a discussion is where that argument lives.
- **Issues** are for concrete, closeable things: an inconsistency between the specification and the primer, an error, a conformance gap, or a specific proposed change with text. An issue should be something a pull request can close.
- **Pull requests** are for edits. Typos and clarity fixes can land directly. A change to normative text should come from a discussion that has settled, not arrive cold, because the cost of an unconsidered normative change is borne by everyone who reimplements from the specification.

## Conventions

### Sign off every commit (DCO)

Every commit must be signed off under the [Developer Certificate of Origin](https://developercertificate.org/). Add the sign-off with `git commit -s`, which appends a `Signed-off-by` line certifying that the contribution is yours to give under the project's licence. This is required from the first commit. There is no separate contributor licence agreement.

### Commit messages

Distinguish normative change from everything else with a prefix, in imperative mood, referencing the section where it helps:

- `normative:` a change to what a conforming implementation must do.
- `editorial:` prose, structure, or clarity, with no change to requirements.
- `proposal:` a substantive change put forward for discussion.
- `chore:` repository mechanics.

Example: `normative: Section 4.3 require attestation to name an owner-evaluated tier`.

### Prose style

The shipped documents follow a deliberate house style, because a document meant to be reimplemented decades from now should not depend on characters most people cannot type, and should read the same in every hand that edits it.

- **British English, Oxford spelling.** Use -ize for the Greek suffix (organize, authorize, recognize) and keep the British -our, -re, and -ce forms (behaviour, colour, centre, licence). This is the first-entry spelling in the Oxford English Dictionary, also used by the Eclipse Foundation and the EU institutions. The -ise-only words keep their s (advertise, compromise, promise, exercise, comprise, surprise), as do -yse words (analyse). An eventual wire-level IETF draft would be Americanized at publication; that is the RFC Editor's house rule, not a reason to switch this repository.
- **Logical quotation.** Sentence punctuation sits outside a closing quote unless it is part of the quoted material, so that a quoted string contains exactly what it claims.
- **Keyboard punctuation only.** No em-dashes or en-dashes. Restructure with commas, colons, parentheses, or a full stop instead. The reasons: contributors who hand-edit introduce mismatched glyphs and the punctuation drifts; the dash reads as a machine tell to part of the audience; and avoiding characters most keyboards lack rhymes with the project's own legibility principle.
- **Short sentences, one idea each.** Split a sentence that chains three ideas through semicolons, or runs much past thirty words. Where a passage lists alternatives, announce the structure first rather than stacking clauses into one sentence.

### Terminology

The names are load-bearing, not decorative, and are defined in Section 2 of the specification. The ones contributors trip on most:

- **Murmuration** is the system, **Murmur** is the protocol, and `murmurd` is the reference daemon.
- The **steward** owns a contract: its schema, safe state, and quorum rule. It is never called the "consumer", and it need not be on the data path.
- **Producer** and **consumer** are per-edge labels, never node identities. One node is routinely both at once.

## Licence and conduct

Contributions are accepted under the [Apache License 2.0](LICENSE), the repository's licence, certified by the DCO sign-off above. The project expects good faith, technical candour, and the working assumption that an objection is a gift. Participation is governed by the [Code of Conduct](CODE_OF_CONDUCT.md), the Contributor Covenant, with conduct concerns directed to chris@raynor.tech.
