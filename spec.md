# Murmur Protocol Specification

**Status: working draft.** This document captures the design decisions made so far. It is not a 1.0. Open questions are collected in [Section 15](#15-open-questions); they are honest, load-bearing, and the most useful place to direct objections.

This document is **normative**: it states what the contract model is and what a conforming implementation must do. The rationale for these decisions, the design principles behind them, the demonstration roadmap, and the relationship to neighbouring systems live in the non-normative [primer](primer.md). Where the two appear to disagree, this document wins.

This specification is organized as a small **core**, this document, plus optional **extensions** that each deepen one mechanism for the implementations that use it (see [extensions/](extensions/README.md)). An implementation conforms to the core, and MAY additionally conform to one or more extensions, one per feature it implements. The witness conforms to the core alone. An extension MAY add requirements for the feature it governs; it MUST NOT weaken a core rule.

## Table of contents

1. [Purpose and scope](#1-purpose-and-scope)
2. [Conventions and terminology](#2-conventions-and-terminology)
3. [The four orthogonal properties](#3-the-four-orthogonal-properties)
4. [Discovery and authority](#4-discovery-and-authority)
5. [The two planes](#5-the-two-planes)
6. [Declare, require, match](#6-declare-require-match)
7. [Definitions and encoding](#7-definitions-and-encoding)
8. [Topics, slots, and binding](#8-topics-slots-and-binding)
9. [Pools and steward failure](#9-pools-and-steward-failure)
10. [Leader election and fencing](#10-leader-election-and-fencing)
11. [Cryptographic profile](#11-cryptographic-profile)
12. [Recovery plane](#12-recovery-plane)
13. [Safety and resilience](#13-safety-and-resilience)
14. [Conformance](#14-conformance)
15. [Open questions](#15-open-questions)

## 1. Purpose and scope

Murmur is a local-first contract layer for cyber-physical systems. It specifies a contract model (identity, capability typing, granted authority, role binding, and declared failure semantics) and a small set of layering rules. It does not specify a transport, and it does not displace the certified, domain-specific stacks that already own each domain (CAN-FD, TSN, and SOME-IP under ISO 26262; IEEE 2030.5, IEC 61850, and IEEE 1547 for grid and DER; CoreMIDI and RTP-MIDI for audio). It binds to them. The governing analogy: POSIX, not Linux; IP, not Ethernet. One abstract contract, many domain bindings.

The protocol normatively specifies the contract and its verification: what a valid identity, grant, ownership transfer, or safe-state declaration is, how a device checks one, and the requirement that such state be inspectable. Everything above that line (registration apps, key custody, onboarding and recovery experience, fleet consoles, brand) is product territory, which competes on experience and which this specification does not constrain. The line is drawn so that any conforming product works with any conforming device, and so that a product which does not honour the contract (for example, one that never genuinely transfers ownership) is detectably non-conformant rather than silently divergent.

One constraint shapes everything below: local-first is strongest exactly where stakes are highest. Drivetrain motion control and grid anti-islanding must not depend on a cloud round trip. Resilience and safety are derived from local reasoning plus declared safe defaults, never from the reachability of a central authority.

A second constraint sets the protocol's deepest boundary: Murmur bounds consequences and attributes actions. It does not evaluate correctness, in any realm. A declared safe state, a fencing token at the resource, a canary halt, and the forensic record each bound what a wrong, stale, or hostile action can do, and each records who did it. None of them judges whether the action was right. Correctness lives in an authority the protocol defers to: a test suite, a ledger, a safety monitor, a human reviewer, or the physical floor itself. The protocol's role is to require that authority where the stake demands it, to verify that its assent was given and recorded, and to fall to a declared safe state when it is absent or unreachable. Declared failure semantics is one instance of this stance, not a separate promise. It is consequence-bounding given a physical floor to bound against; where no such floor exists, the bounding is weaker, and correctness must come from an authority outside the protocol. The grounding and the cross-realm argument are in the primer.

A third constraint caps complexity: node-side evaluation is total and statically bounded, never Turing-complete. Configuration is declarative data by default, matched by fixed code (the declare, require, match shape, Section 6). A restricted total predicate language is admitted only where a node must test runtime state it could not know at design time, such as a conditional safe state, a readiness gate, or a subscription filter, and on the safety-critical path the full branch tree is fixed and certifiable when the role is designed (Section 8.2). Authoring-time generation may be programmatic, but it adds no expressiveness a definition could not state directly (Section 7.1). The detail and its litmus test are in Section 7.3.

A fourth constraint keeps the hardware floor low: time is local and relative, never globally synchronized. Ordering and authority-at-a-point are logical, carried by the monotonic sequence that fencing already uses (Section 10) rather than a clock. Durations, liveness intervals, and grant expiry are measured as local elapsed time from a local event (receipt, the last heartbeat), so they need only a local timer, tolerate arbitrary clock skew, and hold correctly on a device that has been offline for years. A synchronized absolute clock is never required; wall-clock time is optional metadata, captured where a node has it and never depended on.

Two further constraints govern how the model is built rather than what it does, and both recur by name throughout. The fifth is the **separation law**: two needs with opposing requirements never share machinery. One mechanism serving both a live need and a durable one, or a discovered fact and a granted one, corrupts both, so the model splits such pairs and keeps them split. Several splits below are each one instance of this law, not a separate rule: discovered versus granted authority (Section 4.1), the control and real-time planes (Section 5), the authoring, contract, and wire layers (Section 7.1), the recovery and forensic planes (Section 12), and continuity versus authorization (Section 9.3).

The sixth is the **degenerate-case law**: the general shape is defined first, and the common case is recovered as its degenerate instance, never the reverse. A slot is a capacity-one topic (Section 8), a single binding is a capacity-one pool (Section 9), a lone node is a one-member virtual principal (Section 9.3), and the witness's single steward is exclusive failover at a population of one (Section 10). Defining the simple case as the base instead would leak its assumptions, one owner, one failure root, one key, into everything layered above. The simple case is therefore the abstraction running at its limit, so the witness exercises the real mechanism and a second participant needs no new code.

## 2. Conventions and terminology

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

- **Murmuration**: the system; the emergent whole that no node coordinates. There is no node that runs the murmuration; coherence is bottom-up.
- **Murmur**: the protocol; the local rules each node speaks to its neighbours. A *Murmur exchange* is a single peer interaction.
- **`murmurd`**: the reference daemon that speaks Murmur.
- **Node**: a participant with a self-certifying identity (defined precisely in Section 3).
- **Feature-capability**: what kind of thing a node is, expressed as structural interface satisfaction. Discovered, never granted.
- **Authority** (granted authority): whether a node may participate in a given function, conveyed by an object-capability-style grant. Granted, never discovered.
- **Capability contract** (or **definition**): the versioned, content-addressed, signed artifact that gives a capability its meaning (Section 7).
- **Steward**: the owner of a topic or slot contract: its schema, declared safe state, and quorum rule. The steward need not be on the data path and need not be the receiving end. The steward is never called the "consumer".
- **Producer** / **consumer**: per-edge labels describing which way one capability flows on one edge. Never properties of a node; a node is routinely both at once.
- **Slot**: a named role defined by a steward, with a required interface and a declared safe state; the degenerate case of a topic (Section 8).
- **Topic**: a named, typed, shared contract that many nodes attach to as publisher, subscriber, or both.
- **Binding**: the act of admitting one identity into one role. The certified chokepoint.
- **Grant**: a delegable, expirable, verifiable token of authority.
- **Envelope**: bounds a member declares at admission on how it may later be activated.
- **Safe state**: the declared behaviour of a capability edge on loss of liveness, fenced at the resource.
- **Fencing token**: a monotonically increasing value carried by a grant and enforced at the resource, which rejects anything older than the highest value it has seen.
- **Owner**: the party holding the trust root for a device. Distinct from the manufacturer and from any steward.
- **Attestation**: a signed claim, bound to a node's identity key, that the node is genuine, satisfies a regime, or is fit for a role.
- **Regime**: the named standard a node enforces or was certified under; the unit of transitive trust (Section 4.4).
- **Ownership domain**: the set of devices sharing an owner root; the unit of ownership transfer (Section 4.6).
- **Pool**: an optional construct that presents many candidates behind one slot-shaped interface (Section 9).
- **Transport profile** (or **profile**): a named, fully specified realization of the transport match (Section 6.1) for one substrate, complete enough that independent implementations interoperate over it (Section 6.3). Distinct from the cryptographic profile of Section 11.
- **Bridge**: a node that speaks two profiles and relays a contract across them (Section 6.4).

## 3. The four orthogonal properties

The contract model treats four properties as independent axes. Implementations MUST NOT collapse any two. The canonical test is four identical motor modules in one vehicle: same interface, distinct identities, non-interchangeable positions.

| Axis | Question | Property | Discoverable? |
|------|----------|----------|---------------|
| **Identity** | Who is this? | A self-certifying identifier bound to a public key; no naming authority exists to spoof (defined precisely below). | Yes (announced) |
| **Feature-capability** | What kind of thing is this? | Structural interface satisfaction. A thing "is" a motor, inverter, or synth voice if it satisfies the declared interface. | Yes (free, ambient by default; see Section 4.7) |
| **Role** | What part does it play here? | A role defined by a steward, carrying a required interface and a declared safe state. Filled by binding an identity into it. | Schema is discoverable; the binding is granted, not discovered |
| **Edge direction** | Which way does this capability flow? | A per-capability edge label (produce, consume, request-response). Not a node property. | Declared per capability |

An identifier is **self-certifying** when, given the identifier and a live peer, possession of the corresponding private key is verifiable locally, with no registry or naming authority consulted. Whoever proves possession is the identified node, and nothing else can be; spoofing a name requires breaking the key or the digest, never capturing a registry. The construction is defined at its general shape, and the familiar simple forms are recovered as its degenerate (the degenerate-case law, Section 1). The general identifier is **rotation-surviving**. An inception event binds the initial key and pre-commits a digest of its successor. The digest of that event is the stable identifier, and a signed, hash-linked key-event log carries each later rotation forward, so the identity outlives any single key. The pre-commitment is load-bearing. An attacker who captures the current key cannot rotate the identifier, because the successor key is revealed only at rotation. A compromised key therefore buys impersonation for a bounded, recoverable window, never permanent capture of the identity, the same bound as Section 4.6.2. The degenerate forms drop the history. A named cryptographic **digest of the key**, supplied alongside the key for verification, is the rotation-surviving identifier with an empty history, and a deployment that will never rotate MAY collapse its inception event to the bare digest. A **raw encoded key** is the same with the digest elided, self-contained but welded to one key algorithm. The normative commitment is to the property, not to a pinned encoding. The concrete encoding and signature algorithm are chosen together with the substrate (open questions 11 and 33). The witness runs a degenerate form and a durable principal the general one, with no new identity code between them (Section 9.3 and open question 20).

### 3.1 Producer and consumer are per-edge labels

A node exposes a set of capabilities, some provided and some required. "Producer" and "consumer" describe the role relative to one capability on one edge, never the node as a whole. A bidirectional relationship is two ports, not one duplex channel, because the two directions fail independently. Each direction MUST carry its own declared safe state and its own liveness contract. Edge direction is therefore a corollary of declared, per-edge safe state (Sections 8.2, 13.1), not an independent primitive: because the two directions fail independently, each needs its own safe state, and that is what makes them two edges rather than one duplex axis. It is counted among the four axes of Section 3 because keeping the directions distinct is a test a reimplementer must apply, not because it is irreducible.

The slot or topic contract owner is the steward (Section 8). Implementations and documentation MUST NOT use "consumer" for that role; the steward need be neither on the data path nor the receiving end.

### 3.2 Capability shape

Every capability declares one of three shapes in its contract:

- **stream-produce** and **stream-consume**: one-way flow (notes, torque commands, telemetry).
- **request-response**: a first-class shape. The correlation between a request and its matching response is the content of the capability and cannot be reconstructed from two independent one-way flows.

## 4. Discovery and authority

### 4.1 The central split

Two meanings of "capability" are kept rigorously separate, in the most important instance of the separation law (Section 1):

- **Feature-capability**: what a thing is. Self-describing, discovered, ambient by default (Section 4.7).
- **Authority**: whether a thing may participate in a given function. Granted, never discovered.

Discovering that a node satisfies an interface confers no authority. Admitting it into a function is a deliberate, non-discoverable, verifiable act. Hazard analysis attaches to the slot and its required interface, fixed at design time; the identity filling the slot may vary at runtime without reopening the safety case, provided it satisfies the contract and passes admission.

> Discovery proposes; binding disposes.

### 4.2 Stake and the authority ladder

Authority strength MUST scale with the stake of the action. The rungs, weakest first:

1. **Ambient (presence-based)**: being on the bus, in the room, or reachable on the network is itself the entitlement. This is the model systems fall into by default and it is almost always a mistake. It is acceptable only when two factors are both high: the difficulty of illegitimate presence, and the lowness of the stake. Either factor failing disqualifies it.
2. **Granted**: an explicit, verifiable, expirable grant (Section 4.1).
3. **Granted with attestation**: the grant is valid only alongside an attestation from a party the verifier trusts (Sections 4.3, 8.2).
4. **Granted, attested, multi-party**: for the highest stakes, authority that no single party can mint.

Presence MAY contribute evidence to an authorization decision; it MUST NOT be the decision.

The protocol constrains on **declared and attested claims, never on real-world effects**. A guard phrased as "ambient authority may not command an actuator" is unenforceable, because the protocol cannot know what a capability does in the world. Instead: ambient authority is valid only for a capability declared and attested as lowest-stake, and high-stake authority requires attestation to act. Under-claiming is therefore self-defeating: declaring low stake to avoid attestation yields only low-stake authority, and the high-stake action stays unreachable. Over-claiming is handled by Section 4.5. Wherever this specification says "safety-critical capability", read "declared and attested as such".

A corollary governs the design itself, not the implementation: the specification does not build on a property it cannot verify. Where a guarantee is wanted but cannot be attested, the design re-architects until the guarantee is no longer needed, rather than asserting it and relying on it. On-device key generation and identity uniqueness are the worked example (Section 4.6.2); the primer states the principle.

### 4.3 Attestation and exclusion are coupled

Attestation is the only sanctioned in-protocol exclusion mechanism, and attestation and the right to exclude third-party parts are two ends of one lever:

- It MUST be possible to build a secure system without attestation.
- It MUST be impossible to have attestation without a secure system.

The forcing is structural, not a rule layered on top. To exclude a part by attestation, the system must bind each part to a cryptographic identity, check it against a trust root, and reject parts that cannot prove themselves; that rejection is theft-resistance (a stolen or swapped part cannot attest into a system it was never enrolled in), co-extensive with whatever scope is excluded. A manufacturer who skips attestation forfeits in-protocol exclusion, and the aftermarket is open by default. The contradictory position, exclusion without security, is not a state the mechanism can occupy within the protocol. Keeping attestation the sole sanctioned exclusion path (so that a proprietary handshake or serial-number check cannot route around the coupling) is open question 23.

### 4.4 Transitive trust

The core default is a single owner-held trust root (Section 4.5): a node accepts what its owner's root vouches for, and needs no cross-regime reasoning. When a system spans nodes held to *different* standards, onward trust must carry a floor along the path: a connecting-flight rule with a small set of named regime tiers, the floor lowered by the weakest hop and restored only by re-screening. That machinery, which a single-owner system never runs, is the [federation extension](extensions/federation.md).

### 4.5 Trust governance

There is no central body that defines who may attest. A consortium of blessed attesters is rejected outright; it is the single point of capture the architecture exists to avoid.

- Anyone MAY attest, and anyone MAY require attestation. "I accept attestations from X" is a local, owner-held edge, not a global fact. There is no central list to capture, by construction.
- The subject of an attestation is general, not only a device or a part. The same governance credentials any principal a verifier must trust, including an institution that holds a seat in a quorum (Section 4.8). The regime that vouches for "this is a regulated bank" is chosen locally by the relying party, an owner for a device or a counterparty for a transaction, and is capturable by no one, exactly as for a part's regime. Who may credential institutional seat-holders is the same local, plural decision, never a global registry.
- The owner holds the trust roots and defines their own equivalence table (which regimes satisfy which tier of Section 4.4).
- **Trust authority transfers by attested update.** The requirement to attest is itself mutable via an attested change. A vendor's last act (or a court's, or a successor's) can attest a transfer of attestation authority to a community, a successor, or the owners; devices that trusted the vendor then trust the new authority by the same mechanism that always governed them. There is no special abandonment mode.
- Over-attestation is not prevented; it is made survivable and self-limiting. The over-attester bears the build and maintenance cost and the abandonment liability; the stake claim and its attestation requirement are inspectable and forensically logged (Section 12), so over-classification is conspicuous and contestable; and owner-held roots plus attested transfer give the owner a route around it.
- Owner sovereignty relocates the attack surface onto the owner, who can be socially engineered. Re-rooting trust MUST therefore be conspicuous, reversible, and forensically logged, never silent. The behavioural floor (Section 13.3) bounds what even a maliciously trusted attester can do at the actuator.

### 4.6 Device lifecycle and ownership

The worked mechanics (propagation through intermediaries, transfer failure recovery, retained-ownership legibility, salvage, the containment pole, and the compute floor) are in the [ownership extension](extensions/ownership.md). This section fixes the axioms.

#### 4.6.1 Operability and ownership are orthogonal

A device is operable under whoever owns it now; ownership decides the governance root, not whether the machine works. Low-stake operation MAY rest on ambient authority (Section 4.2); high-stake operation REQUIRES a grant from the current owner; governance acts (persistent updates, fleet enrolment, re-rooting, revocation) wait for the new owner after a transfer. A capability MAY declare itself inert until commissioned (a grid inverter ships refusing to feed the grid until owned); this is a per-capability stake declaration, not the global rule.

#### 4.6.2 Identity birth and the two keys

At manufacture, the device generates its own identity keypair inside a secure element. The manufacturer signs a birth certificate over the public key and MUST NOT hold the device private key. Two keys are kept rigorously separate:

- The **device identity key**: on-device, never divulged. It signs telemetry and proves "I am this device".
- The **owner root key**: authority. The owner holds the private half; the device holds the public half and obeys delegations signed by it.

The protocol cannot verify either requirement. On-die generation, non-retention, and uniqueness are manufacturing facts no signature reveals, and a key is copyable information, so the protocol references a keyholder, never a physical entity (Section 3). Where assurance exists it is a per-key attestation from the secure-element regime (Section 4.4), trusted plurally, not a protocol guarantee. A held or cloned device key is bounded by owner sovereignty and the floor, since it buys impersonation, never authority. The anti-counterfeit residue is treated in the [ownership extension](extensions/ownership.md).

Ownership transfers from the supply chain to the buyer by a zero-touch voucher; the human act is scan, tap, or click, never a command-line ritual. This composes over existing mechanisms (IEEE 802.1AR IDevID/LDevID, FIDO Device Onboard, BRSKI per RFC 8995, on-die secure elements) rather than inventing a new onboarding scheme; reconciling their PKI- and cloud-shaped assumptions with the local-first posture is open question 28.

#### 4.6.3 The owner operates at the policy layer

The owner signs *who may publish* (a delegation), never the payloads themselves. Re-rooting an entire fleet is one owner-signed superseding delegation: monotonic (Section 10's fencing applied to authority, so no revocation list is needed in the field), diffused eventually-consistently (Section 7), and verified independently by each device. One owner action, not one per device.

Hard precondition: owner-root enrolment at commissioning, in bulk, zero-touch. If enrolment is skipped and the vendor later dies with no successor named, the only remaining path is per-device physical re-commissioning, which does not scale. This failure is named rather than papered over.

#### 4.6.4 Ownership domains

Ownership is held at the level of the **ownership domain**: the set of devices sharing an owner root, which is the unit of transfer. Nesting (a dealer's domain contains a car; the car contains its components) reuses the steward-of-stewards recursion (Section 9). Ownership grouping is a distinct axis from functional composition: devices can share an owner without being wired together, and be wired together without sharing an owner. The domain is named as the transfer unit and nothing more; membership and partial-transfer machinery are not built until a domain needs them. Partial transfer (selling a part out of a domain) is unbind plus re-enrol.

#### 4.6.5 The handoff backstop

The end-of-life handoff path must never dead-end. The always-valid target is the owners themselves (release-to-owners): it distributes authority rather than concentrating it, every device has an owner-root slot, and it cannot be captured. A vendor MAY pre-name a successor to preserve update continuity; a dead-man's switch SHOULD make release-to-owners automatic on prolonged vendor silence. Paid succession and escrow services are legitimate but MUST be plural, opt-in, and downstream, never a single privileged recipient.

#### 4.6.6 The three layers of bringing a part into a system

Three layers MUST NOT be collapsed; collapsing them is the diagnostic-port theft pattern, in which physical presence equals authority to act.

- **Layer 1, ownership** (whose is it?): after a physical reset, the part adopts the owner root presented in a bounded claim window. Trust at this one moment comes from the physical situation; a freshly wiped part has no prior anchor against which to verify a signature.
- **Layer 2, admission** (may it act as X here?): owning a part does not let it act. The role's steward signs a grant binding the part's identity into a specific role (Section 8.2). Owned-but-not-admitted is a real, distinct state.
- **Layer 3, attestation** (gated roles only): if the role requires attestation, the Layer 2 grant is valid only if the part also carries the required attestation. Open roles skip this layer.

Presence buys only Layer 1, only at the one bootstrap moment where no key relationship yet exists, only on a part the holder physically reset, and reversibly. It buys nothing in Layers 2 or 3.

### 4.7 Discovery visibility

Feature-capability is discovered, and by default discovery is ambient. Announcing a capability is itself stake-bearing for some nodes: it can leak topology to passive listeners and solicit probing of high-stake targets. Discovery visibility is therefore a per-capability declared property with three rungs: **ambient** (the default), **authenticated-before-disclosure** (announce only a key; reveal capabilities to an authenticated peer), and **no-broadcast rendezvous** (advertise nothing; a legitimate initiator connects to a known endpoint and authenticates first).

This is attack-surface reduction only, never a second authority mechanism. Hiding is not securing: a node MUST refuse unauthorized commands regardless of its discovery visibility (Section 4.1), so reduced visibility cannot substitute for granted authority. Only the ambient rung is required; the stricter rungs are a reserved seam (open question 26).

### 4.8 Attestation authority

An attestation is assent from an authority, addressed as one. Section 4.2's ladder requires attestation for high-stake action. This section states the rules the core fixes. The internal structure of a multi-party authority, and its use for settlement and conserved-value finality, are deepened in the [settlement extension](extensions/settlement.md).

Per-property and per-event attestation are distinct. A **per-property** attestation is a durable, cacheable claim bound to an identity, a definition, or a role (Sections 4.3, 8.3). It is verified offline against a signature already held, it survives partition, and it is the default. A **per-event** attestation is assent to one specific action at the moment it is taken. It cannot be cached, because it concerns this event and no other.

Per-event attestation carries a hazard the per-property case does not. If every event must reach a designated authority while it acts, that authority is a central resource, a liveness dependency, and a single point of capture, which the architecture refuses. The hazard is resolved by the authority's structure, not by avoiding per-event attestation. A single designated attester is a central resource. A quorum is not: it needs k of n independent parties to assent, no one of which is load-bearing, and it survives the loss of any individual member. Per-event attestation is therefore permitted only where the authority is itself decentralized (a quorum or pool), and only at stakes that justify its cost.

A quorum does not remove the reachability cost. Reaching k members at action time is a latency and availability cost a cached property does not have, and under partition the quorum may not assemble. A capability that gates on per-event attestation MUST declare a safe state for the case where assent cannot be obtained in time, and MUST take it rather than act unattested. The choice between per-property and per-event is stake-scaled: the higher and more irreversible the stake, the more a capability will pay the per-event liveness cost rather than rely on a cacheable property.

The internal structure of the authority, the standing and ephemeral quorum forms, the negative path that distinguishes an unreachable member from one that affirmatively declines, and the stage, assent, commit, and finality lifecycle by which an attested action defers durability to a source of truth are specified in the [settlement extension](extensions/settlement.md). They are required only of implementations that gate on per-event attestation; a base implementation that uses none does not carry them. The structure, when present, is ignorable: a verifier that needs only the fact of assent reads it as one bit, and one that needs progress, attribution, or membership inspects it (open question 31).

## 5. The two planes

Live event delivery and identity/capability/configuration state have opposite requirements and MUST NOT share machinery (the separation law, Section 1).

| | Control / identity / capability plane | Real-time event plane |
|---|---|---|
| Carries | identity, capability state, slot schemas, bindings, grants, configuration | the live stream (notes, torque commands, telemetry) |
| Requirements | reliable; local-first; eventually consistent is acceptable | low latency; loss-tolerant |
| Loss handling | convergence on reconnect | loss recovered by journaling, never by trading latency for ordered-reliable delivery |

## 6. Declare, require, match

One shape recurs throughout the contract model, stated here once and invoked by name thereafter. A provider **declares** what it offers. A consumer or role **requires** what it needs. A **match** step binds the two only where the declaration satisfies the requirement, and MUST refuse the binding otherwise. Where the matched property is observable at runtime, two further motions apply: the forensic plane (Section 12) **witnesses** promised against actual, and a breach is a liveness failure that fires the declared safe state (Section 13). The same shape governs transport and non-functional envelopes (below), safe states (Section 8.2), and attestation at admission (Section 8.3).

### 6.1 Transport

Transport is not specified, but it is not opaque: latency, ordering, reliability, duplexness, and MTU leak through to whether a capability works at all.

- Transports declare properties: latency class, ordered or not, reliable or not, framed or not, MTU.
- Capabilities require properties.
- The match binds a capability to a transport only where the declared properties satisfy the required ones. Implementations MUST refuse the binding otherwise.

The property vocabulary here is the abstract interface. A named, fully pinned realization of it for one substrate, the unit over which independent implementations actually interoperate, is a profile (Section 6.3).

### 6.2 Non-functional envelopes

A capability's contract MAY carry a non-functional envelope: latency budget, jitter tolerance, liveness interval and staleness deadline, delivery guarantee, throughput. This is the same shape applied to the capability rather than the transport, declared per edge (Section 3.1: a gesture port and a feedback port have different needs). It is matched at admission, witnessed at runtime, and a breach fires the declared safe state.

Murmur declares, matches, and witnesses these requirements. It does not itself provide hard real-time guarantees; those remain the substrate's or the certified domain controller's to deliver. The envelope deliberately carries a few load-bearing dimensions plus a reserved seam, not an exhaustive QoS vocabulary (open question 27). An envelope dimension that cannot be measured is not admissible.

### 6.3 Profiles

Section 6.1 fixes what a transport must declare and a capability must require. A **profile** is the other half: a named, fully pinned realization of that match for one substrate, complete enough that two independently built nodes interoperate over it with no further agreement. The property vocabulary is the abstract interface; a profile is a concrete recipe against it. "Murmur over CAN-FD", "Murmur over QUIC", and "Murmur over CoreMIDI" are profiles. Optionality is the enemy of interoperability. A profile MUST therefore minimize it: where the abstract match would admit a choice, the profile fixes one, and any alternative it still permits is itself named, so a peer detects it rather than guesses.

A profile pins three things: the wire encoding of contract messages on the substrate (Section 7.1), the discovery mechanism, and, for each requirement of Section 6.1, how the substrate satisfies it or that it cannot. A requirement the substrate cannot meet is declared unmet, never silently emulated. Capabilities that require it then cannot bind over that profile, because the match refuses otherwise (Section 6.1). This is the imperfect matrix made honest: an unavailable capability is a substrate declaring its limits, not a hidden failure.

**The interoperability floor is scoped, never global.** A steward MAY declare the profile or profiles its contract requires, and a node that speaks one of them can bind. That is the only interoperability guarantee the protocol makes: within a contract, members share a profile by construction. There is deliberately no single profile every node must speak. Requiring one would force every node onto one substrate, and a node that physically cannot speak a substrate cannot be attacked over it. A controller that speaks only Murmur over CAN is fully conforming. Its inability to speak an internet profile is a safety property (Section 13.3), not a conformance gap. A universal mandatory profile would mandate attack surface, and the protocol MUST NOT impose one.

**A profile is defined by its vectors, demonstrated by a reference adaptor.** A profile MUST publish conformance vectors: sample messages with their expected encodings and decodings, the carried-content round trip, and fencing-token pass-through (Section 6.4). The vectors are the normative definition. They are language-neutral data, and they live with the specification, as the schema artifacts of a content format do. A profile SHOULD additionally ship a reference adaptor: a runnable implementation of the substrate-to-contract mapping that passes its own vectors. The adaptor is an oracle and a disambiguation aid, never the definition. Where the prose, the vectors, and the adaptor disagree, the specification wins, then the vectors, then the adaptor. This is the POSIX discipline: the text is normative, a conformance suite checks it, and many implementations exist, none of them the standard. The adaptor's implementation language and calling convention are a reference-daemon concern and are not fixed here.

**The reference profile is a default, not a mandate.** There SHOULD be one reference profile: the baseline the reference daemon ships, and the lingua franca for the general-purpose networked case, RECOMMENDED wherever no constraint argues otherwise. It is chosen for ubiquity and ease of implementation, not for performance. The common case then interoperates with no decision required, and richer profiles are reserved for the cases that need them. It is a default, never a floor: a node that cannot speak it, the air-gapped controller above, stays fully conforming. Its concrete composition (substrate, encoding, discovery) is gated on the substrate and encoding choices still open (open questions 11 and 33).

Profiles are drawn from a small, named, public catalogue, stewarded like the definition commons (the updates extension) rather than owned (open question 34). A node MAY define a private profile. It thereby leaves the interoperating set of any standard profile it does not also speak, and it MUST declare a private profile as private rather than present it as a standard one. Conformance attaches per profile: an implementation conforms to the profiles it speaks, and any claim of interoperability names them. The profile concept and these rules are core. The concrete per-substrate profiles, each with its vectors, live in a future `profiles/` directory, each its own document and its own conformance unit, not in an extension, because a profile is a binding rather than the deepening of a mechanism.

### 6.4 Bridges

**A bridge joins two profiles.** A **bridge** is a node that speaks two profiles and relays a contract across them. It is the only construct that needs more than one. A bridge needs no new machinery; what it may and may not do follows entirely from existing core rules (open question 35).

- **Carried authority and authenticity cross unchanged.** A key-bound grant (Section 11), a per-property attestation (Section 4.8), a content-addressed signed definition (Section 7.2), and a fencing token (Section 10) all verify offline against a key, independent of the substrate that carried them. A bridge relays them as opaque signed content and confers zero authority, exactly as any relaying peer does (Section 7.2). It MUST NOT re-sign carried content, because re-signing forges provenance, and the resource keeps enforcing each fencing token against its original granting authority.
- **Ambient authority cannot cross.** Presence-based authority (Section 4.2, rung 1) means something only on the substrate that defines the presence. A bridge cannot carry it, and MUST re-establish it under the target profile as an ordinary binding (Section 8), which is an owner-visible, forensically logged trust act (Section 4.5). A bridge that re-originates authority thereby becomes a new granting authority, and fencing re-scopes to it (Section 10).
- **The transport match must hold end to end** (Section 6.1). A bridge MUST advertise only the capabilities whose required transport properties its two legs jointly satisfy, and the match refuses the rest.
- **Bridge failure is two stale edges** (Sections 3.1, 13.1). A bridge is two edges, each with its own liveness contract and declared safe state, so its death fires each side's safe state by the ordinary dead-man's switch and introduces no new failure mode.

The bridge is therefore the deliberate, removable, accountable crossing point. Removing it restores the substrate separation physically, and the crossing is the natural site for the policy and audit a trust boundary wants (Section 13.3).

**A bridge's redundancy is the Section 9 pool patterns applied to a bridge.** It is never an unsafe single point of failure, since its death fires each side's safe state. It can be an availability one, removed by running more than one along the carried-versus-ambient line. A **carried-only bridge** holds no authoritative state, so it is a stateless relay, and both shapes of Section 9 apply. Run it all-active as a multiplicity slot, where every live bridge forwards and the consumer collapses duplicates, or as a redundancy pool behind one virtual identity, where one winner forwards and failover is promotion. The choice is an instance of open question 1. An **ambient-crossing bridge** re-originates authority, so it is a steward in all but name (Section 9.1), and it is made redundant the way a steward is. The options are a hardened fail-safe singleton, or a pool-backed virtual bridge identity (Section 9.3) under leader election and fencing (Section 10), so that only the current leader mints authority and a stalled predecessor's late grant is fenced out. In neither shape does the sender enumerate bridges or carry failover logic. It addresses the destination contract, or the pool's single virtual identity, exactly as it addresses any topic (Section 8).

The carried plane composes trivially. The native plane, the ambient re-binding and the end-to-end transport match, does not, and that asymmetry is the point.

## 7. Definitions and encoding

### 7.1 Three layers

The artifact humans write, the abstract contract, and the artifact machines exchange are three different things, and none may masquerade as another (the separation law, Section 1).

```
Authoring surface     ->   Contract definitions    ->   Wire encoding   ->   Transport
(YAML + Starlark)          (capabilities, slots,        (canonical binary,   (pluggable,
                            roles, policies)             compiled)            Section 6)
```

- **Authoring**: YAML for static declarative definitions; Starlark for programmatic ones (parameterized or templated generation, with deterministic sandboxed evaluation and no arbitrary I/O). Both compile to identical contract definitions, and the choice is ergonomic, not semantic. This equivalence is a load-bearing invariant, not a convenience: programmatic authoring MUST NOT express anything a static definition could not, and a node never receives or runs Starlark, only the compiled declarative contract. The day generation can emit what a static definition cannot, the legibility separation has been broken.
- **Wire**: a compact, schema-defined binary encoding, compiled, never authored by hand and never surfaced to users. It is an encoding, not a transport, and rides whatever transport Section 6 selects. The concrete encoding is not settled (open question 33). Its requirements are load-bearing: it MUST be canonical, because definitions, grants, and attestations are content-addressed and signed (Section 7.2), so a non-deterministic encoding makes byte-identical verification fragile; it MUST be implementable on a constrained device without a heavy toolchain or transitive dependency tree; and it SHOULD stay inspectable enough to diagnose in the field. Protobuf is one candidate, efficient and mature, but it is non-canonical by default, opaque on the wire, and heavy to embed; CBOR with COSE meets the constrained-device and canonical requirements more directly and is self-describing. The most technically efficient encoding is the wrong one if it cannot be embedded or debugged by the people the project needs.

### 7.2 Definitions and updates

A definition's identity is **content-addressed and signed**: a hash plus a publisher key, not a mutable name on a server. The same logical artifact MUST therefore encode to identical bytes regardless of who or what produced it, or its hash and signature stop verifying, so a canonical, deterministic encoding is a requirement, not a preference (open question 33). Such a definition verifies the same from the commons, a private registry, a peer, or a USB stick, with no origin server alive. Verifying a received definition is integrity and authorization: is this what publisher P published, and is P allowed to define this capability. A relaying peer confers zero authority on the content; transport trust is never content trust.

Updates reuse the protocol's own machinery and couple to the failure core, which is the whole of what the core fixes. An update that cannot be verified or completed MUST leave the device in its declared safe state, never half-defined. A breaking change is a semantic disconnection: the binding goes stale and fires its declared safe state (Section 13), by the same machinery as a dropped link. Activation keeps the old definition resident and hot, so apply has an unapply. There is no separate rollout-safety subsystem.

The distribution machinery (the public commons and private registries, the freshness, anti-rollback, and eclipse defences, the compatibility relation and fleet propagation, and coordinator-free canaried activation) is the [updates extension](extensions/updates.md). A device that ships fixed definitions and never updates in the field implements none of it.

### 7.3 Evaluation complexity

How much computation a definition or a grant can trigger is itself a contract decision, capped here once so it is not rediscovered field by field. The ceiling is total, statically bounded evaluation, never Turing-complete, at every site a node evaluates anything. Two tiers cover every case.

**Declarative data, the default.** Quorum rules (members, threshold, roles, mandatory flags), attestation coverage, transport and non-functional envelopes, regime equivalence tables, and trust tiers are data structures matched by fixed code: the declare, require, match shape (Section 6). A rich, even elaborate, set of fields is acceptable here, because the code that reads them is fixed and small. Complexity carried as data stays legible and reimplementable; complexity carried as evaluation does not.

**A restricted total predicate, only where runtime state must be tested.** A conditional safe state (Section 8.2), a readiness gate (the updates extension), and a subscription filter (Section 8.5) genuinely depend on state unknown at design time, so they cannot be pure data. These use a restricted predicate language that is total and terminating, with no unbounded loop or recursion. On the safety-critical path the full branch tree is additionally fixed and certifiable when the role is designed (the constraints of Section 8.2 and open question 30).

The litmus test for any new field follows directly. If evaluating it needs runtime state not known at design time, it is a bounded predicate under the Section 8.2 constraints; otherwise it is data. If it would ever need to loop or recurse over unbounded input, that is a design error, because it can be neither certified nor reimplemented from this specification alone (open question 21).

A pluggable policy (a promotion or election policy, or a multi-principal arbiter, Sections 8.4 and 9) MUST resolve to a named policy from a fixed catalogue with declarative parameters, or to a bounded predicate, never to carried code. Where genuinely open-ended choice is wanted, it lives above the contract line as product behaviour (Section 1), and the protocol constrains only the declared envelope within which that choice is made. Which restricted predicate language to specify, an existing total one such as CEL or a smaller purpose-built grammar, is open question 32.

## 8. Topics, slots, and binding

The primitive is the **topic**; the **slot** is its degenerate case (one steward, capacity-1 binding), by the degenerate-case law (Section 1). Defining it the other way around leaks two false assumptions into everything downstream: that the contract owner is on the data path, and that there is one failure root.

### 8.1 Slot

- A slot is a named role defined by a steward, with a required interface and a declared safe state. It is first-class and persists whether or not it is filled.
- Slot states: `unfilled`, `bound-and-live`, `bound-and-stale`. The transition to stale fires the slot's safe state.
- **The safe state belongs to the slot, not the module.** An identical motor controller reads `freewheel` in a drive slot (a held wheel on a lost link is uncommanded propulsion or single-wheel braking, a stability hazard) and `hold-torque` in a hoist slot (freewheeling drops the load). Two genuinely different declared safe states for one module is the point.

### 8.2 Safe states are named capabilities

A declared safe state (`freewheel`, `hold-torque`, `ramp-to-zero-then-freewheel`) is a named capability a node provides and a slot requires, matched by ordinary interface satisfaction. There is no separate safe-state subsystem. Matching establishes eligibility; **binding arms exactly one named safe state for that edge** and makes it locally resident, so it fires on link loss with no further instruction.

The protocol matches the name. What `freewheel` does in the world lives in the definition commons (Section 7) and, where safety-critical, in an attestation that a competent party stands behind. The protocol never classifies by effect (Section 4.2). Physical-environment constraints are below the protocol and explicitly not captured: two motor controllers on a mechanically coupled rotor are a physics problem the protocol cannot see. Conflicts between declared safe states on a shared physical resource are ceded to the system integrator's hazard analysis, backstopped by the physical floor (Section 13.3) and the forensic record. The protocol witnesses them; it does not adjudicate them.

A named safe state MAY be internally conditional ("return home unless the physical environment is compromised; otherwise freeze"), subject to three constraints that keep it a safe state rather than a smuggled response (Section 13.1). The predicate MUST be locally decidable: evaluable by the failing node alone, from sensing and state resident on the node at the moment of failure, in bounded time, with no dependency on the connectivity whose loss fired it. The conditional MUST totalize conservatively: branches are ordered by conservatism, and a predicate that cannot be evaluated takes the most conservative branch, never the most convenient. And the branch taken MUST be forensically logged. The Section 13.1 boundary is restated by this, not weakened: a safe state is what the local node does with local knowledge; the response remains what a coordinator does with global knowledge. The invariant is unchanged: binding arms exactly one name, whose full branch tree is fixed and visible to hazard analysis at design time. What is forbidden is selecting among safe states at failure time, a decision that needs exactly the information failure may have destroyed. How expressive the predicate may grow before it defeats legibility and certification is open question 30.

### 8.3 Binding and admission

- **Binding admits one identity into one slot.** Admission is the certified chokepoint.
- Attestation at admission is the declare, require, match shape (Section 6). The **attestation is a credential carried by the part**, signed and bound to its identity key. The **requirement** (whether, at what tier, attesting what) is **declared by the role's steward**. **Sufficiency is judged at the binding**, where carried credentials are matched against the declared requirement and the grant records the pass. A part may carry credentials no role requires; a role may require credentials only some parts can present. Exclusion and theft-resistance both live at the match.
- The steward owns the schema and advertises it as a capability ("a thing with these slots and these binding rules"). A car and a synth rig differ in their schemas, not in the protocol.
- Admission is **consent-driven**: a member consents to join and declares its activation envelope at admission time (an inverter: "never dispatch me below 20% state of charge"). Consent to admit is not consent to activate; front-loading consent and envelope lets later activation be handshake-free yet sovereign.
- Ranking, priority, and scoring live in the steward, not the protocol. The protocol carries membership and state; the steward decides order.
- **Duplicate live identity is witnessed, not refused.** Two live presentations of one identity into one steward are the local, observable counterpart to birth-time uniqueness, which is unverifiable (Section 4.6.2). A steward MAY surface this as an anomaly, but MUST NOT refuse a binding on that basis alone, because it may be an owner's deliberate redundancy. The protocol witnesses the duplication; the owner decides what it means.

### 8.4 Topologies

All topologies are expressible on the one primitive, and which applies is declared per capability. The core default is the single-steward star:

- **Fan-in** (many producers, one steward): wheels reporting telemetry.
- **Fan-out** (one producer, many subscribers): a timing leader and its follower devices.

Someone always owns the topic's contract (schema, declared safe state, quorum rule), but that contract authority can be a registrar that never touches the data, and is sometimes off the data path entirely. The **mesh** (many to many, no centre, the rootless case the slot model cannot express) and the **multi-principal** node (one node bound into slots owned by different stewards, reconciling conflicting grants through a local arbiter) are the [federation extension](extensions/federation.md). They need no single steward, which is why the topic, not the slot, is the primitive.

### 8.5 Subscriptions are predicates

A subscription carries a predicate over payload or state, not just a topic name, and the contract declares where the predicate is evaluated:

- predicate = `true`: a plain topic subscription (the degenerate case).
- **Subscriber-side evaluation** (the default): ordinary filtering; no model assumption; retrofittable anywhere.
- **Fabric- or publisher-side evaluation**: content-based routing, in which non-matching messages never traverse the link. Architecturally significant, and justified only by physical constraints (constrained bus bandwidth, a safety controller that must not parse everything, a sleeping radio).

The seam is reserved, not the mechanism: content routing is a capability a transport or steward may later offer, never a model change.

## 9. Pools and steward failure

A **pool** is an optional construct usable anywhere a single slot is. It is slot-shaped from the outside (same required interface, presents one winner), so a singleton slot can be upgraded to a pool-backed one without the steward changing anything. A single binding is the degenerate pool: capacity 1, no promotion. The structure is committed to here; the failover machinery (the candidate state machine, promotion policy, the selection locus, state projection and handoff, and pre-warming) is in the [pools extension](extensions/pools.md).

Two patterns the word MUST NOT conflate: a **multiplicity slot** (capacity above one, all members active at once, no slot-level failover) and a **redundancy pool** (one active member plus warm standbys, failover by promotion). Which applies per capability is open question 1.

Where the winner is selected is itself a declared property, the **selection locus**, parallel to the evaluation locus of subscriptions (Section 8.5). Three loci exist. At the **fabric**: multiplicity, all members active, the consumer collapsing duplicates. At the **pool boundary**: one winner behind a virtual identity, the default. At the **consumer**: the pool publishes its membership as a set with an update channel, and the consumer selects with a named policy (Section 7.3), the client-side load-balancing shape. Consumer-side selection keeps the pool off the data path and retires the central frontend as a point of failure, and it is the preferred shape for software fleets and rootless topics (the [pools extension](extensions/pools.md)). One invariant bounds all three: **selection chooses reachability, never authority.** Choosing which member to address grants it nothing; the member acts only on the grant it already holds, and fencing rejects a stale one (Section 10). Selecting among independent grant-issuers without election would be split-brain, and is forbidden.

A pool presents one capability while internally orchestrating many; this is capability composition, with the pool as the degenerate case where all sub-members satisfy the same interface. Heterogeneous composition is recognized but deliberately out of model (Section 15.1).

Stateful capabilities make pure selection insufficient: a freshly promoted standby that does not know a note is held produces stuck or dropped notes. State projection belongs at the consuming endpoint, which recovers from observation rather than replication wherever the state is fully observable from the consumed stream. The exceptions, the capabilities carrying hidden state that genuinely needs member-side checkpointing, are open question 4, and the handoff mechanics are in the [pools extension](extensions/pools.md).

### 9.1 Steward failure

The recursion bottoms out. Pools and topics close under composition (a pool of pools, a steward of stewards), but there is always a root steward whose liveness is the trust anchor, made reliable by other means than another pool. There is deliberately no coordinator-of-the-whole to promote anything into.

Failing over a steward is categorically harder than failing over a member: the steward holds authoritative state (the ledger), is the trust root issuing grants, and is what producers are pointed at. Three honest options, chosen per capability:

- **Fail safe (harden a singular root).** The steward does not fail over; it fails safe. On steward death every slot goes stale from the top and fires its declared safe state. For most safety-critical stewards this is the correct, certifiable answer; in a vehicle, the motion controller is an internally redundant certified component, not something failed over by a discovery protocol. This is the default.
- **Pool-backed virtual steward identity.** The steward becomes a slot backed by candidate stewards presenting one stable virtual identity. Its costs and mechanics (ledger replication, a threshold credential) are in the [pools extension](extensions/pools.md). Reserved for availability-critical stewards.
- **Published candidate set with consumer selection.** The steward publishes its candidate set with an update channel, and producers select a live candidate by the consumer-side selection locus above. Reads are served by any candidate; authoritative issuance is gated by leader election among them (Section 10), and a stalled former leader is fenced out, so authority stays singular while reachability survives total churn. It needs the ledger replicated, as the virtual identity does, but no threshold credential, so it is buildable on election and fencing alone. It is the natural shape for the software-fleet principal of open question 20, and is developed in the [pools extension](extensions/pools.md).

### 9.2 Failure reasoning forks by topology

In the core default, the **star** (single steward), steward death is one clean event: all its slots fail safe. The **rootless** case has no central death signal, so each subscriber detects publisher staleness and fires its own local safe state, with fencing at every actuator and a declared quorum rule. That reasoning, and the split-brain exposure it carries, is the [federation extension](extensions/federation.md).

### 9.3 The virtual principal

One object recurs through this specification under several names: the pool-backed virtual steward and the published candidate set (Section 9.1), the durable principal of the settlement extension, the virtual bridge identity (Section 6.4), and the software-fleet principal of open question 20. They are one primitive, named here once rather than rediscovered per domain. A **virtual principal** is a first-class identity that exists to be filled by one or more nodes but is not itself a node. It is addressable, it holds and issues grants, and its continuity does not depend on the identity of whatever node animates it now. A single node filling a single slot is its degenerate case, exactly as a single binding is the degenerate pool.

A virtual principal is an identity layer above the keys that currently control it, never a private key handed from node to node. A key is copyable information, and a divulged device-identity key violates Section 4.6.2, so continuity MUST NOT be carried by passing a key. Two constructions give an identity that outlives its current key: a controlling key that rotates forward through a signed key-event log (the rotation-surviving identifier of Section 3), and a threshold key whose holders reshare without changing the public identity (Section 11). They compose, and the composite is the candidate answer to the deep half of open question 20.

Continuity and authorization stay on separate axes, the same discipline as Section 4.1 (the separation law, Section 1). Continuity ("is this the same principal?") is an identity-axis question, answered by verifiable history. Authorization ("may this node act as the principal now?") is an authority-axis question, answered by a grant. A delegation answers only the second, and MUST NOT be made to carry the first. "Hold this grant and you are the same system" collapses two orthogonal axes into one, and is forbidden.

A virtual principal filled by more than one node is safe under a single rule: no two holders may exercise conflicting authority over the same resource at the same instant. Three shapes satisfy it, and one violates it.

- **Disjoint scope.** Authority is attenuated into non-overlapping slices (Section 4), one node for one currency and another for another, so no two holders share a resource. Safe by construction, needing none of the machinery below.
- **Singular in time.** Many nodes may claim the role, but at most one acts per term, and a stalled predecessor's late command is fenced out at the resource. This is the exclusive-failover shape of Section 10.
- **Joint.** Many hold shares, and acting is a k-of-n act (Section 11), so plurality is the mechanism rather than a hazard.
- **Forbidden: concurrent independent plurality.** Two holders each able to exercise the principal's full authority alone, at once. This is split-brain by construction, and Section 9.1's invariant already bans selecting among independent grant-issuers without election.

## 10. Leader election and fencing

No single election algorithm is baked in. The protocol standardizes the interface (candidacy, term or lease, and the obligation to fail safe on failure to elect) as a slot-level policy, the same shape as promotion policy and transport properties.

Local-first and partition-prone means there is no linearizable store to lean on; a lease object in a consensus-backed store is a lock on someone else's consistency, and that ground does not exist here. Election and the declared safe state are two faces of one coin: under partition, when a node cannot safely elect, it MUST fail to the declared safe state it already has. Safety is always chosen over liveness.

The interface names one recurring shape, fixed once here so it is not redesigned per capability: **exclusive failover with bounded terms, fenced at the resource.** It is the contract a role satisfies under three conditions: at most one candidate may act at a time, the right to act passes between candidates on failure, and no stale action survives the handover. Four properties define it, and any mechanism providing them satisfies it.

- **Eligibility is granted and expiring.** Eligible candidates hold an expiring grant from the delegating authority, verifiable offline (Section 4), so that authority need be live only at issuance and renewal, never at runtime.
- **A term is bounded and singular.** At most one candidate holds the right to act within a term, and the term self-expires. Acting authority is singular in time even when the principal it acts for is filled by many nodes (Section 9.3).
- **The term number is the fencing token.** The term carries a monotonically increasing number, enforced at the resource by the fencing rule below, so a stale-term command is rejected locally and instantly. Election and resource share one notion of "current" rather than holding two.
- **Failure to establish a term falls to safe state.** A candidate that cannot establish a current term, under partition or lost quorum, takes its declared safe state (Section 13) rather than acting on an expired or unconfirmed one.

The shape is satisfied at three populations, weakest machinery first, under the one contract.

- **One trusted steward, trivially.** One eligible candidate and one issuer: "the steward picks" is the whole algorithm, the term is the binding itself, and fencing is present but dormant, since with one issuer and one candidate nothing is ever stale. This is the core default, and it is what the witness runs. The witness exercises the full shape at a population of one, not a special-cased shortcut (the degenerate-case law, Section 1). That is the proof the abstraction is real: the day a second contending candidate appears, the identical path produces a higher term and fences the stale one out, with no new code.
- **Peers by consensus.** Crash-fault election among peers with no trusted arbiter produces a leader and a term number together. Raft is one such mechanism, and a worked example using it, the bounded term in the constitutional dictator sense, is in the [federation extension](extensions/federation.md). The core requires no specific algorithm; Raft is an illustration of a satisfier, not the standard.
- **A threshold of holders.** The term-holder is a k-of-n key held by no single node (Section 11), so the right to act survives the loss of any one holder and none is load-bearing.

The harder tiers, crash-fault consensus among peers and Byzantine consensus among mutually distrusting parties, are developed in the [federation extension](extensions/federation.md).

**Fencing tokens are the load-bearing safety mechanism.** Lease election alone is unsafe: a stalled leader's lease can expire, a new leader be elected, and the old leader wake and act. Therefore every leadership grant carries a monotonically increasing token, and the resource (the actuator: motor, inverter) MUST reject any command bearing a token below the highest it has seen. This makes split-brain safe at the resource even while election is momentarily ambiguous, which is the property actually needed, cheaper and stronger than global consensus. A leadership token is a time-bounded, monotonic authority grant enforced at the resource; it is the Section 4 authority machinery, not a new mechanism.

Two rules keep fencing safe under a shared or re-homed identity. The token is minted by the granting authority and carried in the grant, never self-asserted by the part, so a cloned identity cannot inflate its own fencing position; it can only replay an old grant, whose token is stale and rejected. And a resource's high-water mark is scoped to the granting authority, so a part re-homed by physical reset MUST clear any persisted fencing state, or it will reject its new authority's lower-numbered grants and refuse to act. That failure is safe (the slot reads stale and the safe state fires) but it bricks a legitimate repair, so clearing fencing state is part of the reset that re-homes a part (the ownership extension's salvage bootstrap).

## 11. Cryptographic profile

The primitives are borrowed; global consensus is refused. Finality is an authority property, not a delivery property. Even perfect transport permits a double-spend. What rejects the second attempt is an authority that orders the two, not a link that delivers them. A blockchain in the dispatch path is a category error: global total-order consensus is the expensive way to get a weaker guarantee than resource-side fencing already provides locally and instantly.

That refusal concerns the real-time dispatch path, not finality everywhere. Finality is a third property alongside consequence-bounding and attribution: agreement among parties that a state transition is settled and will not be undone. Some transitions in conserved-value domains (payments, settlement) genuinely need finality among mutually distrusting parties, and that is the one case heavy consensus earns. It is delivered by per-event quorum attestation (Section 4.8) and deferred to a pluggable authority. It is never built into the protocol and never placed in a control loop. Banking two-party acknowledgement and blockchain proof-of-work or proof-of-stake are the same per-event quorum gate with different membership models: a small named set, or an open sybil-resistant one. Both establish agreed, attributable finality, not correctness. A fully attested transaction can be fully wrong, since a drained smart contract is validly signed and final, so correctness stays with the authorities the protocol defers to (Section 1). This sharpens open questions 6 and 25.

- **Self-certifying identifiers** (committed as a property, Section 3): authenticating an identifier is local verification of key possession, so name-spoofing is cryptographically impossible rather than checked. Section 3 fixes the construction at its general, rotation-surviving shape, with the raw-key and digest-of-key forms as its degenerate; verifying the general form adds an offline replay of the key-event log to the possession check. The concrete encoding and signature algorithm are open question 11.
- **Capability tokens** (UCAN-style): decentralized, offline-verifiable, local-first delegation chains for Section 4 authority. Grants are **key-bound**: a grant authorizes the holder of a named key and is exercised only by proving possession of that key, so a copied or leaked grant is inert without the key. Accidental possession is therefore harmless, and a grant needs no confidentiality for authority purposes. Deliberate copying is the owner's prerogative: an owner MAY replicate a grant across parts that share an identity for seamless handoff, and the protocol neither prevents this nor needs to. The gate is possession of the key, not secrecy of the grant.
- **Threshold signatures / distributed key generation** (BLS, FROST): the virtual steward credential (Section 9). Any k of n share-holders produce one signature verifiable against one unchanged public key, so steward failover yields the same signature the predecessor would have produced. Share-holders MAY be replaced by resharing, which absorbs total churn of the holding set with no change to the public identity, so the principal's own electorate can turn over while its identity stays one key. The composite of this with a rotation-surviving identifier (Section 3), a key-event log whose current controlling key is itself a threshold key, gives both rotation and no single holder, and is the candidate answer to the deep half of open question 20. Implementation maturity must be confirmed before depending on a specific scheme.
- **Hash-linked (Merkle) logs**: the authority-grant and binding history is an append-only hash-linked chain: tamper-evident delegation and efficient validity proofs without a blockchain.
- **Expiry beats revocation.** A delegation chain proves authority was granted, not that it was never revoked; offline verifiability and timely revocation are in fundamental tension. In any safety context, short-lived grants that must be renewed MUST be preferred over long-lived grants that must be revoked. Expiry is a connectivity-free dead-man's switch; revocation requires reaching everyone. A leadership lease is exactly an ephemeral capability renewed or lost.

## 12. Recovery plane

Operational state and the audit record are different artifacts with opposite requirements, and one mechanism cannot serve both without corrupting both (the separation law, Section 1). The **recovery plane** holds present operational state to survive failover: it is mutable, ephemeral, low-latency, in the failover path, and lives at the consuming endpoint or pool boundary (Section 9). It holds a note-on until its note-off and then forgets.

The **forensic plane** is the other half: the immutable, tamper-evident record that survives disputes. It is an optional sink, not baked into every node (a synth rig runs recovery only; a vehicle or grid system attaches a recorder because liability and regulation demand reconstruction), and its machinery is the [forensic extension](extensions/forensic.md).

The forensic plane is the protocol's role at the edge of its own authority: where Murmur cedes control (physical-world coupling it cannot mediate, overrides it must yield to), it retains witness. It records that something happened where it could not, and should not, govern how.

## 13. Safety and resilience

### 13.1 The failure core

- Safe state on loss of liveness is capability- and slot-specific and declared, never global (Section 8). A held note releases; a drive motor freewheels; an inverter anti-islands.
- The heartbeat is the dead-man's switch that fires the declared safe state.
- The protocol's job is fast, trustworthy detection plus a declared safe default. The response (redistributing torque across the live corners, re-deriving dispatch) belongs to the certified domain controller. Safety logic is never smuggled into the communication layer.
- This specification addresses graceful degradation. Functional safety in the IEC 61508 / ISO 26262 sense (fail-safe versus fail-operational design) is a distinct, heavier discipline and is not claimed here.

### 13.2 Longevity threats

Three longevity threats have three distinct defences, developed in the primer: **abandonment** (the maker stops) is answered by openness, **obsolescence** (the maker engineers the device to stop) by owner sovereignty, and **poison** (a validly signed update that is malicious or bricking) by containment. Their normative residue: trust anchors MUST be owner-re-rootable and there MUST be no vendor-only revocation of the owner's own grants; and poison is contained, never prevented, by canaried activation with automatic halt (the updates extension) and reversibility, because verification checks provenance, not intent.

### 13.3 The physical floor

No software layer is the final safety authority. Every mechanism in this specification raises the cost of casual, remote, and accidental failure, and every one is circumventable by a sufficiently capable, physically present actor, by design (the primer develops why). The final safety authority is a layer the protocol cannot reach.

- For safety-critical capabilities a physical, out-of-band override below the protocol (an emergency stop, a manual disconnect, a fuse) is REQUIRED. It makes no decisions, so it cannot be tricked into a wrong one; Murmur neither mediates it nor can disable it; a physically present authorized actor can always reach it.
- The protocol MUST detect and gracefully yield to a legitimate out-of-band override, and forensically log it, rather than resist it as an attack. How software reliably distinguishes a genuine override from a spoofed one is open question 19.
- The **behavioural floor** (Section 10's fencing applied to intent: an actuator rejecting even a validly signed command that violates its declared safe envelope) is a cost-raiser, not an unbreakable guarantee. It is what makes owner sovereignty safe: the owner chooses whom to trust, and the floor bounds what any trusted party can do.
- **Stake classification is owner-visible and auditable.** Every capability's autonomy classification (unrestricted, re-certification-gated, law-bounded) is a declared, inspectable, forensically logged property. The protocol cannot stop a manufacturer over-classifying everything as safety-critical; it refuses to be the instrument that hides it.

## 14. Conformance

This draft is not yet accompanied by a conformance suite, and its normative statements are still moving. The intended shape of conformance is fixed, though, and follows from Section 1:

- A conforming implementation honours the contract model: it verifies identities, grants, attestations, and definitions as specified; keeps the four axes distinct; arms declared safe states at binding and fires them on loss of liveness; enforces fencing at resources; and keeps the mandated state (ownership, classification, grants, transfers) inspectable.
- A product that presents the contract without honouring it (for example, one that never genuinely transfers ownership, or that hides a capability's stake classification) is non-conformant, and the specification is written so that such divergence is detectable from the outside.
- Conformance composes. An implementation conforms to the core, to each extension whose feature it implements, and to each transport profile it speaks. A profile's conformance is judged against its published vectors (Section 6.3); a reference adaptor demonstrates them but does not define them.

**The witness's active surface is six axioms.** The witness conforms to the core alone and runs only degenerate cases, so most of this specification is present but dormant for it. Fencing never fires, because with one issuer and one candidate nothing is ever stale. Election reduces to the steward picking, pools are capacity one, and the witness has one steward, one profile, no bridge, no per-event attestation, and no federation. What it actually exercises is six things: self-certifying identity (Section 3), the discovered-versus-granted split (Section 4.1), declared safe state fired by a dead-man's switch (Sections 8.2, 13.1), declare, require, match (Section 6), key-bound grants over content-addressed definitions (Sections 11, 7.2), and local relative time (Section 1). The rest is dormant but present, and the degenerate-case law (Section 1) guarantees that dormant machinery needs no new code when a second participant arrives.

A precise conformance clause, with test vectors, follows once the open questions that gate it are closed.

## 15. Open questions

These are the forks not yet closed, kept visible deliberately. Objections to any of them are the most valuable contribution this specification can receive.

1. **Slot capacity and failover shape per capability.** Which slots are multiplicity (no spare; steward-level degradation) and which are redundancy (real standby; promotion)? This drives the state machine.
2. **Which stewards must survive death rather than fail safe?** Decides where threshold keys and steward-state replication are paid for, versus a hardened single root plus safe state. There are now three survival shapes (Section 9.1): a fail-safe singleton, a virtual identity, and a published candidate set with consumer selection and fencing. The third needs no threshold credential, lowering the cost of survival, which shifts but does not settle this per-capability judgment.
3. **Symmetry of binding.** Single-owner systems can treat binding as the steward's prerogative; multi-party systems need the member to be able to refuse or bound its role. The model must permit mutual binding even where a given domain does not use it.
4. **Which real capabilities have hidden state?** State not observable from the stream is the set that forces member-side checkpointing (Section 9). Sharpened: when the consuming endpoint is itself plural or churning (a load-balanced fleet behind one shared identity, a pool failover, a rootless subscriber), recovery from observation is insufficient, because the node that resumes an interaction is not the one that began it. Such state must be keyed by a node-independent identifier and looked up against a store or authority, never pinned to a node. The identifier stays domain-shaped (a transaction id, a request id, a session handle), but the rule is one: state that must outlive the node handling it is addressed by name, not by node. Interlocks with request-response correlation (Section 3.2) and the settlement extension's read-or-retry.
5. **Automatic-within-envelope versus re-consent on promotion.** Front-loaded envelopes make promotion handshake-free; confirm envelope expressiveness covers the grid cases.
6. **Does any domain need agreement on shared history among distrusting parties**, rather than merely verifiable authority? The line between borrowed primitives and an accidental blockchain. Likely answer: per-party signed logs, not consensus. Sharpened (June 2026): provenance needs only per-party signed logs, but finality (agreement that a transition is settled and will not be undone) is a distinct need that some conserved-value domains genuinely have. It is met by per-event quorum attestation deferred to a pluggable authority (Sections 4.8, 11), not by the protocol holding consensus itself.
7. **Topology per capability.** For each real capability: star, fan-in, fan-out, rootless mesh, or multi-principal? Each rootless capability must additionally declare its quorum rule.
8. **Predicate evaluation locus.** Which capabilities, if any, justify fabric-side content routing rather than default subscriber-side filtering?
9. **Edge direction and request-response enumeration.** Split every bidirectional relationship into two independently failing ports; mark request-response capabilities so correlation is first-class.
10. **Naming.** Settled: Murmuration (system), Murmur (protocol), `murmurd` (reference daemon); steward, never "consumer", for the contract owner. The reference implementation follows a per-language convention, `murmur-rs` first, then `murmur-go`, `murmur-haskell`, and so on, so that no single implementation wears the protocol's bare name (POSIX, not Linux). Each is a workspace holding a shared `murmur-core` library and the binaries `murmurd` (the endpoint daemon) and `murmur-bridge` (the cross-profile relay). This resolves the earlier sub-decision toward `murmurd` for the daemon binary; `murmuration` is not used as a binary name.
11. **libp2p as substrate**: adopt it, or reimplement identity, discovery, and negotiation? This decision also fixes the identifier encoding left open in Section 3, where adopting libp2p implies digest-of-key peer identifiers, the degenerate form. Section 3 now fixes the construction at its general, rotation-surviving shape: an inception key plus a signed key-event log, the KERI shape, with the raw-key and digest-of-key forms as its degenerate. What stays open here is therefore the encoding and signature algorithm, not the construction family. The rotation-surviving form composes with a threshold-held current controlling key (Section 11), which removes the single key-holder and is the form question 20 wants. The witness runs the degenerate identifier and a durable principal the general one, with no new identity code between them. It also interlocks with the wire encoding (question 33): libp2p uses protobuf pervasively, so adopting it as the substrate drags protobuf in and partly forecloses the encoding choice, which the embeddability and canonical-encoding requirements may not want.
12. **The fast-versus-supervisory control boundary.** Where exactly does the real-time control loop end and the Murmur supervisory plane begin? Sharpest in datacenter power, where the safe state is partly fast and physical. Misplacement is either control in the communication layer or a missed trip.
13. **Datacenter gap: validate or refute.** Whether a real gap exists beyond what DCIM, hyperscaler-internal power management, and power-aware schedulers already cover is an empirical question. Refutation is a successful outcome (see the primer's datacenter section).
14. **The compatibility relation** (the updates extension). Define precisely when v2 is backward-compatible with v1 for a capability interface, and how breaking changes are declared. The fleet-update story rests on this. Includes whether a superseding fix inherits any of the superseded version's accumulated canary evidence, or starts fresh (the default, the updates extension).
15. **OTA update mechanics for constrained, intermittently connected devices.** Delta versus full transfer, resumability across disconnection, the verify, hold, activate, reverse state machine, and the trust chain checked before acceptance.
16. **Coordinator-free canarying.** Gradual activation needs early activators, an observation discipline, and a halt that propagates across a partitioned fleet, with nothing central to provide any of them. The sketch (rationale in the primer's canarying section): wave membership derived deterministically from node identity and definition hash against publisher-signed thresholds carried in the artifact; randomized jitter within a wave; health inferred from attested silence, with distress reports signed by the victim, or by its steward when the canary dies before it can speak (the binding's liveness contract detects the death), propagating at higher priority than artifacts, and silence counted only while fresh short-expiry no-distress statements keep arriving, so withheld distress surfaces as staleness (the freeze-attack defence, TUF's timestamp-role move, one layer up), and only over attested exposure, since silence from a population that never activated is vacuous and arrival order must not become a de facto canary assignment; holds scoped to the steward's topic; stake tiers setting the evidence required before activation (population canaries, shadow execution fenced from the actuator, publisher-funded rigs, offline qualification attestations). Hard sub-questions: a distress hold is a freeze-attack surface against security fixes, so who may sign credible distress; a publisher-authored schedule cannot be the floor, so minimum canary discipline is device-side and steward-side policy; and stake must set the evidence bar rather than the queue, since a uniformly high-stake fleet that defers en masse becomes an unchosen, unobserved canary of everyone (and a unique configuration of sibling versions is a population of one), while "too important to canary" must stay self-defeating by keeping "activated on zero evidence" an attestable, legible fact; and the remedial clock: who sets the deadline, per stake tier, for fix-class updates, and the precise steps of the capability-scoped degradation ladder when a remedial hold expires without its evidence bar met. Acknowledged rather than solved: the isolated system (a vehicle updated from a thumb drive, a population of one with no gossip reach) activates on evidence frozen at export time and reports distress only on the next physical round-trip, so fleet learning keeps a permanent shadow in the shape of its isolated members. Interlocks with questions 14, 15, and 17.
17. **Irreversible activations.** Some applications have physical side effects no rollback can retract. Name the class and the extra gates it requires. Do not assume rollback always exists.
18. **Owner re-rooting versus certification.** The per-capability autonomy boundary: unrestricted; gated by re-certification (the owner can re-root, but the new authority must itself carry valid attestation); law-bounded. Hard sub-question: how re-certification works when the original certifier is the entity that abandoned the device.
19. **Physical override: authorization and graceful yield.** Who may invoke the out-of-band override, and how the protocol recognizes and safely cedes to a legitimate one rather than resisting it. The smart layer's detection of the dumb floor reintroduces a smart check that can be spoofed; this needs pressure-testing by people who have built emergency-stop systems.
20. **Where does persistent system identity reside through total component churn?** If every node is replaced, what is "the same system", and where does its identity live such that no single component is load-bearing for it? The sketch is a virtual identity backed by a churning peer set (Section 9), owner-held rather than vendor-held. A concrete, buildable instance is a software fleet presenting one principal identity: a bank's settlement workers, or any load-balanced service, hold one stable identity toward their counterparties while every worker behind it is replaced. That is the grandfather's axe in pure software, and it makes the question testable without hardware; the durable principal of the settlement extension and the virtual steward of the pool extension are the same pattern in two domains. Consumer-side selection over a published, live-updated candidate set (Section 9.1) concretely supplies this question's availability half: the principal stays reachable through total member churn with no member load-bearing for it. The unifying object is now named in Section 9.3, the virtual principal, and this question holds its deepest half: where the principal's own identity and key custody reside when no node is load-bearing for them. The candidate answer is the composite continuity of Section 11, a rotation-surviving identifier (Section 3) whose current controlling key is itself threshold-held. The witness already runs the degenerate of that identifier, a digest of the key with no rotation history, so the identity machinery this question deepens is present but dormant from the first build rather than added later (the degenerate-case law, Section 1). The genuinely-not-off-the-shelf residue is electorate churn: when the share-holders who are the principal's control are themselves replaced, "who may hold a share" becomes its own consensus decision, absorbed by resharing while the public identity stays one key. A second residue is duplicity: without dedicated witnesses, a holder could fork the key-event log, presenting divergent histories to different peers. The design's answer is to witness rather than prevent it, composing the forensic plane (Section 12) with the duplicate-identity stance of Section 8.3, and whether that witness suffices at the highest stakes is open. Arguably the deepest open question in the specification.
21. **The legibility budget.** For each sophisticated mechanism: could a competent stranger reimplement it from this specification alone in twenty years? Where capability and legibility conflict, the trade must be deliberate and recorded.
22. **Legible, footgun-resistant owner trust decisions.** Owner-held roots relocate the attack surface onto a socially engineerable owner. How is re-rooting made conspicuous, reversible, and hard to do by accident, without reintroducing a central authority to "help" and thereby rebuilding the consortium?
23. **Sole-exclusion-path enforcement.** The attestation and exclusion coupling (Section 4.3) holds only if attestation is the only in-protocol way to exclude a part. How are non-attestation lockouts kept out of the sanctioned protocol, and out-of-protocol exclusion kept visible and contestable?
24. **Making graceful exit genuinely lower-friction than disappearing.** The handoff mechanism (Section 4.6.5) works only if attested transfer is actually the least-effort wind-down path. Pre-designated successors, a dead-man's switch on vendor silence, legal hooks: what makes "transfer authority" the thing an administrator reaches for over switching off the servers?
25. **Owner-held settlement without a central clearing house.** Contribution records (Section 12) can underwrite payment for grid services without the protocol becoming a market, but multi-party settlement that distrusting parties accept must not collapse into a central ledger. Overlaps question 6. Sharpened (June 2026): the settlement gate is per-event quorum attestation (Section 4.8), and banking acknowledgement and chain consensus are the same gate with named-few versus open-sybil-resistant membership. What stays open is the membership machinery an ownership domain must carry to host such a quorum (overlaps question 29), and the dispute, reversibility-window, and fraud authorities that sit above finality, since finality is not correctness. A standing quorum has an inclusion steward off the data path; an ephemeral pairwise quorum (a retail payer's bank and a merchant's bank, formed for one transaction) has none, and its membership is instead self-defined by the parties under a credentialing regime (Section 4.8). How the scheme-level rulebook stays a credentialing-and-dispute layer rather than a per-transaction clearing house is the live form of this question.
26. **Confidential and authenticated discovery** (Section 4.7). Develop the visibility rungs without ever letting hiding substitute for authorization.
27. **Non-functional envelopes** (Section 6). Which few dimensions are load-bearing; the precise declare-versus-guarantee boundary; and the observability surface, since an unmeasurable envelope is theatre.
28. **Device lifecycle composition.** Composing IEEE 802.1AR, FIDO Device Onboard, and BRSKI, which are PKI- and cloud-shaped, with the local-first no-required-centre property; the compute floor and which devices it excludes; the salvage claim-window mechanism; and the reset-difficulty dial at both its poles (the ownership extension).
29. **Ownership transfer machinery.** The bearer-versus-bound voucher trade, the re-commissioning difficulty dial, recovery oracles for incomplete transfers, and how far ownership domains need membership machinery before the reserved seam must open (Section 4.6).
30. **Conditional safe states: predicate expressiveness versus certifiability.** Section 8.2 permits a named safe state to be internally conditional, bounded by local decidability and conservative totalization. A predicate language inside the most safety-critical path the protocol has is a mini-program in exactly the place the legibility budget guards hardest, and it borders the fail-safe versus fail-operational territory of functional safety that Section 13.1 declines to claim. How expressive may the predicate be (sensor reads, fixed thresholds, validity windows on locally held state) before the branch tree can no longer be certified, or reimplemented from the specification alone? This is the safety-critical instance of the evaluation ceiling (Section 7.3); the cross-cutting language choice is open question 32. Interlocks with questions 4 and 21.
31. **Structured versus opaque attestation authority** (Section 4.8). Attestation authority is structured (member identities, threshold, and roles) so that progress, attribution, heterogeneous roles, and membership change stay expressible, with the opaque single-signer or threshold-signature case as a degenerate collapse. How much of that structure must an implementation carry, and expose, before it breaches the legibility budget? Where does the line fall between low-stake verifiers that read one bit of assent and high-stake verifiers that inspect members, and how is per-event attestation's fail-to-safe-state behaviour specified precisely when a quorum cannot assemble under partition? Also open: the precise negative-path state machine, distinguishing absence from dissent, releasing staged resources, and fencing a late assent; and the stage, assent, commit, and finality lifecycle by which per-event attestation hands durability and outcome-resolution to the source of truth it defers to. Interlocks with questions 3, 6, 17, 21, 25, and 29.
32. **Runtime predicate language** (Section 7.3). The few sites that evaluate a predicate over runtime state (a conditional safe state, a readiness gate, a subscription filter) need a language that is total and terminating, never Turing-complete. Adopt an existing total language such as CEL, or specify a smaller purpose-built grammar (comparisons, boolean operators, field reads, fixed thresholds, validity windows)? CEL is a standard but a large surface for a reimplementer; a minimal grammar is more legible but is one more thing to specify and get right. The decision is the same compose-versus-reinvent trade as the substrate choice (question 11). Interlocks with questions 8, 21, and 30.
33. **Wire encoding** (Section 7.1). The binary form that contract definitions, grants, and attestations compile to is not settled. The requirements: canonical, since these artifacts are content-addressed and signed (Section 7.2) and verification is byte-identical; embeddable on a constrained device without a heavy toolchain or transitive dependencies (the compute floor, question 28); and inspectable enough to debug in the field (the legibility budget, question 21). Protobuf is efficient and mature but non-canonical by default, opaque on the wire, and a substantial dependency burden on embedded targets. CBOR with COSE is the leading alternative: a constrained-device standard with a defined deterministic encoding and built-in signing, self-describing on the wire. Canonical JSON is the maximally inspectable but most verbose end. Interlocks with question 11, since adopting libp2p as the substrate drags protobuf in with it. The guiding principle is that the most technically efficient encoding is the wrong choice if the people the project needs cannot embed or debug it.
34. **The profile catalogue, the reference profile, and the scoped floor** (Section 6.3). A profile realizes the transport match (Section 6.1) for one substrate; the interoperability floor is per-contract, never global; the normative definition of a profile is its published vectors, with a reference adaptor as oracle; and there SHOULD be a reference profile as the default for the general-purpose case. Open: how small and how governed the standard catalogue must be so it does not sprawl into a private profile per vendor, which is the definition-commons governance (the updates extension) and the anti-consortium stance (Section 4.5) applied to profiles; whether a per-contract floor suffices or some deployments need a wider declared interoperability scope; the minimum a profile must pin (encoding, discovery, per-requirement satisfaction) to guarantee blind interoperation; and the concrete composition of the reference profile (substrate, encoding, discovery), which is gated on questions 11 and 33.
35. **Bridge semantics and redundancy across substrates** (Section 6.4). A bridge relays a contract across two profiles. Carried authority, authenticity, and fencing cross unchanged; ambient authority cannot, and must be re-established as a logged re-binding; and a bridge is made redundant as stateless multiplicity (carried-only) or as a virtual steward (ambient-crossing, Sections 9.1 and 10). Open: whether a safety property must be guaranteed to hold *across* a bridge (an override intent originating on one substrate reaching an actuator on another), or only per leg, which is the cross-substrate face of question 12; the precise trust-transfer and fencing-re-scoping rules when a bridge re-originates authority; and how a bridge advertises which capabilities its two legs can jointly carry without weakening the end-to-end transport match. Interlocks with questions 1, 12, 19, and 20.

### 15.1 Deliberately out of model

The model has a named ceiling so that the boundary is a decision, not an oversight. The model is: topic with a direction-neutral contract steward; capabilities typed by shape (stream, request-response); subscriptions as predicates with a declared evaluation locus; failure declared per edge and per topology. Star, fan-out, and rootless mesh are degenerate cases of it; pools and homogeneous composition are instances of it. Parked above the line, expressible later through the reserved seams but not built now:

- **Heterogeneous capability composition** (sub-members satisfying different interfaces). Recognized, not generalized.
- **Content-based and fabric-side routing machinery.** The seam is reserved (Section 8.5); the fabric is unbuilt.
- **Spatial and geometric routing** ("any sensor within this bounding box").
- **Streaming-to-discrete reconciliation**, and other shapes beyond stream and request-response.
- **Physical-world coordination channels and entrainment.** Coordination through channels the protocol does not mediate (speaker and microphone, heat, shared-bus voltage) is legitimate and expected. The protocol's only role at that edge is to witness it (Section 12), never to mediate it.

If a future need pushes any of these below the line, it should arrive through an existing seam (predicate subscriptions, the shape type, the steward-of-stewards recursion), not by reopening the spine.
