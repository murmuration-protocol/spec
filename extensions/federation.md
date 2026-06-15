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

- **Crash-fault, bounded membership, no trusted arbiter** (peer ECUs): lease plus pre-designated primary plus deterministic failover, with the consistent store supplied deliberately. The bounded dictator below is the worked example.
- **Multi-party, mutually distrusting** (grid participants): participants can lie, so crash-fault consensus is unsound; this tier needs Byzantine fault tolerance plus consent envelopes.

Fencing at the resource (Section 10) remains the load-bearing safety mechanism under all tiers, and is the reason a momentarily ambiguous election is still safe.

## A worked example: the bounded dictator

The exclusive-failover shape of Section 10 is satisfied trivially by a single steward and distributively by a threshold scheme. Between them sits the crash-fault tier: peers with no trusted arbiter, electing one leader to act alone for a bounded term. This is the constitutional dictator in the Roman sense, a final arbiter appointed for a fixed term and a bounded purpose, not the pejorative one. Raft is the worked illustration here, and the choice is deliberate. Raft won its mindshare over the incumbent by dividing the same problem more legibly, which is the property this specification values over raw efficiency. It is shown as an example of a satisfier, never as a required algorithm.

The shape, drawn at this population, has three legs that fail independently.

- **Eligibility** is the slow, offline, expiring grant: "these identities MAY claim this role" (Section 4). The delegating authority need be live only at issuance and renewal, never at runtime. Where issuance itself must survive churn, it is threshold-issued (Section 11), a distributed arbiter rather than a single one.
- **Election** is the rare, quorum-paid democratic act among the eligible set. It produces a leader and a monotonic term number together. The expensive act is paid rarely, and the leader then acts fast and alone within its term. That amortization is what makes the tier tractable.
- **The term and the resource** make the bound real. A finite term does not enforce itself, because a stalled leader that wakes still believes it rules. Fencing at the resource (Section 10) is the third leg. The resource obeys only the highest term number it has seen, and rejects a stale-term command instantly and locally.

The arbiter is democratized, not removed. The quorum is collectively the arbiter, so no single node is a point of capture or failure. The cost retained is liveness: the electorate must be able to convene. The degradation is the desired one. Under partition the electorate cannot convene, no re-election happens, the term lapses, and every actor falls to its declared safe state (Section 13). Safe-not-live under partition comes for free.

Where this tier is paid is set by whether a physical resource is present to arbitrate. Where the exclusive right is arbitrated by a single physical resource, that resource is a free sequencer: the actuator was always singular, so making it the arbiter of who acts now adds no new single point of failure, and exclusive failover costs almost nothing. Where the right has no physical chokepoint, an issuing or minting right in pure software, there is no actuator to play arbiter, and exclusive failover must pay for the full machine above with real quorum liveness. This is the primer's dimming floor reappearing exactly here, and it is why settlement is the hard witness. The only escape from paying for consensus, even in software, is to drop exclusivity: attenuate into disjoint scopes so no two holders contend (Section 9.3), and merge what remains. Anything that must be exactly one, somewhere, pays for ordering.

## Rootless topologies

A **rootless** topic (many to many, no centre) is the case the slot model cannot express, and the reason the topic is the primitive. It has no central death signal: each subscriber MUST independently detect publisher staleness and fire its own local safe state. Partition produces sub-flocks, each internally coherent, each potentially believing it is whole: split-brain with no quorum to arbitrate. Consequently fencing tokens MUST live at every actuator independently, and the topic contract MUST specify its quorum rule. Rootless buys the absence of a single point of failure and pays in distributed detection and split-brain exposure.

## Multi-principal arbitration

A **multi-principal** node is bound into slots owned by different stewards (a home energy manager and a utility aggregator) and runs a **local arbiter** to reconcile conflicting grants within its declared envelope. The arbiter resolves to a named policy from a fixed catalogue or a bounded predicate, never to carried code (the evaluation ceiling, Section 7.3).

## Open questions

This extension carries open question 3 (symmetry of binding), open question 7 (topology per capability, including each rootless capability's quorum rule), and open question 12 (the fast-versus-supervisory control boundary). The bounded-dictator example also bears on open question 20 (persistent identity through churn): the elected leader is the current controller of a virtual principal whose electorate may itself churn. Those entries in the core specification carry the current state of each.
