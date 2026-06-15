# Federation: distrusting parties and no single steward (extension)

**Status: optional extension.** This extension deepens the cases where a system spans more than one trust domain, or has no single steward: cross-regime trust, election among mutually distrusting participants, rootless mesh topologies, and a node reconciling grants from several stewards. The core default for every one of these is the simple case, and most implementations stay there: one owner-held trust root, a trusted single steward that picks, and a star topology. A grid, a virtual power plant, or a cross-organization system needs this extension; a single-owner system does not.

Section references are to the core specification unless stated otherwise. Where this extension and the core appear to disagree, the core wins.

## The core hook

The core fixes the single-trust-domain, single-steward, star defaults (Sections 4.4, 4.5, 8.4, 9.2, 10). This extension adds what a multi-party or rootless system needs on top: cross-regime trust floors, the harder election tiers, rootless failure reasoning, and multi-principal arbitration. It adds requirements for implementations that span trust domains or run without a single steward; it never weakens a core rule.

## Transitive trust across regimes

When a system spans nodes held to different standards, onward trust follows a connecting-flight rule: passengers re-clear security at a hub the destination has not certified as equivalent.

- The unit of trust is an attested **regime** (the standard a node enforces), not the node and not the payload.
- Trust levels form a small set of **named tiers**, not a continuous score (for example: self-asserted; attested by an owner-trusted party; attested under a certified-equivalent regime; re-screen required). Continuous trust scores are illegible and gameable, and are not used.
- Onward trust is the **minimum regime along the path**: a floor carried with the payload, lowered by the weakest link, never raised by a later strong hop, restored only by re-screening at a node that vouches from its own root.
- The receiving node decides locally: it compares the carried floor against its stake-scaled requirement and then accepts, re-screens, downgrades the action to what the floor permits, or refuses.

## Election among distrusting parties

The core default is a trusted single steward (Section 10), where election collapses to "the steward picks". Two harder tiers apply where there is no trusted arbiter:

- **Crash-fault, bounded membership, no trusted arbiter** (peer ECUs): lease plus pre-designated primary plus deterministic failover, with the consistent store supplied deliberately.
- **Multi-party, mutually distrusting** (grid participants): participants can lie, so crash-fault consensus is unsound; this tier needs Byzantine fault tolerance plus consent envelopes.

Fencing at the resource (Section 10) remains the load-bearing safety mechanism under all tiers, and is the reason a momentarily ambiguous election is still safe.

## Rootless topologies

A **rootless** topic (many to many, no centre) is the case the slot model cannot express, and the reason the topic is the primitive. It has no central death signal: each subscriber MUST independently detect publisher staleness and fire its own local safe state. Partition produces sub-flocks, each internally coherent, each potentially believing it is whole: split-brain with no quorum to arbitrate. Consequently fencing tokens MUST live at every actuator independently, and the topic contract MUST specify its quorum rule. Rootless buys the absence of a single point of failure and pays in distributed detection and split-brain exposure.

## Multi-principal arbitration

A **multi-principal** node is bound into slots owned by different stewards (a home energy manager and a utility aggregator) and runs a **local arbiter** to reconcile conflicting grants within its declared envelope. The arbiter resolves to a named policy from a fixed catalogue or a bounded predicate, never to carried code (the evaluation ceiling, Section 7.3).

## Open questions

This extension carries open question 3 (symmetry of binding), open question 7 (topology per capability, including each rootless capability's quorum rule), and open question 12 (the fast-versus-supervisory control boundary). Those entries in the core specification carry the current state of each.
