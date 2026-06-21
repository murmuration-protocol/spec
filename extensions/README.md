# Murmur specification extensions

The Murmur specification is a small **core** ([spec.md](../spec.md)) plus a set of optional **extensions** in this directory. The core states the contract model and the rules every conforming implementation obeys. An extension deepens one mechanism for the implementations that use it, and adds nothing to the reading burden of the implementations that do not.

This is the sensible-default-with-room-to-grow discipline made structural. The core stays small and stable, and capability accretes at the edges without taxing the centre.

## Conformance

An implementation conforms to the **core**. It MAY additionally conform to one or more **extensions**, one per feature it implements. The witness (see the [primer](../primer.md)) conforms to the core alone.

Two invariants keep the structure honest:

- An extension MAY add requirements for the feature it governs. It MUST NOT contradict or weaken a core rule. The core is the floor; extensions build upward from it, never into it.
- An implementation that does not use an extension's feature need not read or implement it. A contract declares which extensions a peer must satisfy to bind, so a core-only implementation detects, rather than guesses, when it has met a peer that needs more than it offers.

## The extensions

- [settlement.md](settlement.md): per-event attestation, quorum structure, and the stage, assent, commit, and finality lifecycle. Required only for multi-party settlement and conserved-value finality. Deepens core Section 4.8.
- [pools.md](pools.md): the redundancy pool, the candidate state machine, state projection and handoff, and the pool-backed virtual steward. Required only for multi-member failover. Deepens core Section 9.
- [ownership.md](ownership.md): propagation through intermediaries, transfer failure recovery, salvage, the containment pole, and the compute floor. Required only for ownership transfer beyond first commissioning. Deepens core Section 4.6.
- [updates.md](updates.md): distribution, the trust model for received updates, fleet propagation, and coordinator-free canaried activation. Required only for implementations that update definitions in the field. Deepens core Section 7.2.
- [federation.md](federation.md): cross-regime trust, the harder election tiers, rootless topologies, and multi-principal arbitration. Required only for systems that span more than one trust domain or have no single steward. Deepens core Sections 4.4, 8.4, 9.2, and 10.
- [forensic.md](forensic.md): the immutable, tamper-evident audit record. Required only where stakes justify reconstruction (liability, regulation). Deepens core Section 12.

## Reserved seams

The core names several mechanisms it does not yet deepen: content-based routing (Section 8.5), heterogeneous capability composition (Section 15.2), confidential and authenticated discovery (Section 4.7), and transport profiles and bridges (Sections 6.3 and 6.4). The first three each become an extension when an implementation needs one. Transport profiles differ in kind. The profile concept and its rules are core, and the concrete per-substrate profiles, each with its conformance vectors, will land in a future `profiles/` directory rather than here, because a profile is a binding rather than the deepening of a mechanism. That directory is named `profiles/` to avoid colliding with "binding", the core's term for authority admission, and the reference adaptors that demonstrate the profiles live in the reference daemon, not in the specification. Nothing in the core forecloses any of these.

## A note on ownership

Each extension is a candidate ownership boundary. When the project grows working groups, an extension is the natural unit for one to hold: a bounded area with its own depth, its own open questions, and its own reviewers, that the core reader can ignore. That governance does not exist yet, and the structure does not require it. The modularity is its precondition, put in early so it costs nothing to adopt later.
