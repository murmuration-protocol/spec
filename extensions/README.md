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

Further extensions land here as the mechanisms they govern are needed: pools and state handoff (core Section 9), ownership transfer machinery (core Section 4.6), and coordinator-free activation (core Section 7.5). Until then they are reserved seams in the core, named but not deepened.

## Reserved seams

The core names several mechanisms it does not yet deepen: content-based routing (Section 8.5), heterogeneous capability composition (Section 15.1), confidential and authenticated discovery (Section 4.7), and transport bindings (a future `bindings/` directory). Each becomes an extension when an implementation needs it. Nothing in the core forecloses them.

## A note on ownership

Each extension is a candidate ownership boundary. When the project grows working groups, an extension is the natural unit for one to hold: a bounded area with its own depth, its own open questions, and its own reviewers, that the core reader can ignore. That governance does not exist yet, and the structure does not require it. The modularity is its precondition, put in early so it costs nothing to adopt later.
