# Murmur Protocol Specification

**Status: working draft.** This document captures the design decisions made so far. It is not a 1.0. Open questions are collected in [Section 18](#18-open-questions); they are honest, load-bearing, and the most useful place to direct objections.

This document is **normative**: it states what the contract model is and what a conforming implementation must do. The rationale for these decisions, the design principles behind them, the demonstration roadmap, and the relationship to neighbouring systems live in the non-normative [primer](primer.md). Where the two appear to disagree, this document wins.

## Table of contents

1. [Purpose and scope](#1-purpose-and-scope)
2. [Conventions and terminology](#2-conventions-and-terminology)
3. [The four orthogonal properties](#3-the-four-orthogonal-properties)
4. [Discovery and authority](#4-discovery-and-authority)
5. [The two planes](#5-the-two-planes)
6. [Transport binding](#6-transport-binding)
7. [Non-functional envelopes](#7-non-functional-envelopes)
8. [Definitions and encoding](#8-definitions-and-encoding)
9. [Topics, slots, and binding](#9-topics-slots-and-binding)
10. [Pools](#10-pools)
11. [State projection and handoff](#11-state-projection-and-handoff)
12. [Steward failure](#12-steward-failure)
13. [Leader election and fencing](#13-leader-election-and-fencing)
14. [Cryptographic profile](#14-cryptographic-profile)
15. [Recovery plane and forensic plane](#15-recovery-plane-and-forensic-plane)
16. [Safety and resilience](#16-safety-and-resilience)
17. [Conformance](#17-conformance)
18. [Open questions](#18-open-questions)

## 1. Purpose and scope

Murmur is a local-first contract layer for cyber-physical systems. It specifies a contract model (identity, capability typing, granted authority, role binding, and declared failure semantics) and a small set of layering rules. It does not specify a transport, and it does not displace the certified, domain-specific stacks that already own each domain (CAN-FD, TSN, and SOME-IP under ISO 26262; IEEE 2030.5, IEC 61850, and IEEE 1547 for grid and DER; CoreMIDI and RTP-MIDI for audio). It binds to them. The governing analogy: POSIX, not Linux; IP, not Ethernet. One abstract contract, many domain bindings.

The protocol normatively specifies the contract and its verification: what a valid identity, grant, ownership transfer, or safe-state declaration is, how a device checks one, and the requirement that such state be inspectable. Everything above that line (registration apps, key custody, onboarding and recovery experience, fleet consoles, brand) is product territory, which competes on experience and which this specification does not constrain. The line is drawn so that any conforming product works with any conforming device, and so that a product which does not honour the contract (for example, one that never genuinely transfers ownership) is detectably non-conformant rather than silently divergent.

One constraint shapes everything below: local-first is strongest exactly where stakes are highest. Drivetrain motion control and grid anti-islanding must not depend on a cloud round trip. Resilience and safety are derived from local reasoning plus declared safe defaults, never from the reachability of a central authority.

A second constraint sets the protocol's deepest boundary: Murmur bounds consequences and attributes actions. It does not evaluate correctness, in any realm. A declared safe state, a fencing token at the resource, a canary halt, and the forensic record each bound what a wrong, stale, or hostile action can do, and each records who did it. None of them judges whether the action was right. Correctness lives in an authority the protocol defers to: a test suite, a ledger, a safety monitor, a human reviewer, or the physical floor itself. The protocol's role is to require that authority where the stake demands it, to verify that its assent was given and recorded, and to fall to a declared safe state when it is absent or unreachable. Declared failure semantics is one instance of this stance, not a separate promise. It is consequence-bounding given a physical floor to bound against; where no such floor exists, the bounding is weaker, and correctness must come from an authority outside the protocol. The grounding and the cross-realm argument are in the primer.

## 2. Conventions and terminology

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

- **Murmuration**: the system; the emergent whole that no node coordinates. There is no node that runs the murmuration; coherence is bottom-up.
- **Murmur**: the protocol; the local rules each node speaks to its neighbours. A *Murmur exchange* is a single peer interaction.
- **`murmurd`**: the reference daemon that speaks Murmur.
- **Node**: a participant with a self-certifying identity (defined precisely in Section 3).
- **Feature-capability**: what kind of thing a node is, expressed as structural interface satisfaction. Discovered, never granted.
- **Authority** (granted authority): whether a node may participate in a given function, conveyed by an object-capability-style grant. Granted, never discovered.
- **Capability contract** (or **definition**): the versioned, content-addressed, signed artifact that gives a capability its meaning (Section 8).
- **Steward**: the owner of a topic or slot contract: its schema, declared safe state, and quorum rule. The steward need not be on the data path and need not be the receiving end. The steward is never called the "consumer".
- **Producer** / **consumer**: per-edge labels describing which way one capability flows on one edge. Never properties of a node; a node is routinely both at once.
- **Slot**: a named role defined by a steward, with a required interface and a declared safe state; the degenerate case of a topic (Section 9).
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
- **Pool**: an optional construct that presents many candidates behind one slot-shaped interface (Section 10).

## 3. The four orthogonal properties

The contract model treats four properties as independent axes. Implementations MUST NOT collapse any two. The canonical test is four identical motor modules in one vehicle: same interface, distinct identities, non-interchangeable positions.

| Axis | Question | Property | Discoverable? |
|------|----------|----------|---------------|
| **Identity** | Who is this? | A self-certifying identifier bound to a public key; no naming authority exists to spoof (defined precisely below). | Yes (announced) |
| **Feature-capability** | What kind of thing is this? | Structural interface satisfaction. A thing "is" a motor, inverter, or synth voice if it satisfies the declared interface. | Yes (free, ambient by default; see Section 4.7) |
| **Role** | What part does it play here? | A role defined by a steward, carrying a required interface and a declared safe state. Filled by binding an identity into it. | Schema is discoverable; the binding is granted, not discovered |
| **Edge direction** | Which way does this capability flow? | A per-capability edge label (produce, consume, request-response). Not a node property. | Declared per capability |

An identifier is **self-certifying** when, given the identifier and a live peer, possession of the corresponding private key is verifiable locally, with no registry or naming authority consulted. Whoever proves possession is the identified node, and nothing else can be; spoofing a name requires breaking the key or the digest, never capturing a registry. Two standard constructions satisfy the property: the identifier is the encoded public key itself (self-contained, but variable-length and welded to one key algorithm), or the identifier is a named cryptographic digest of the key (fixed-length and algorithm-agile, with the key supplied alongside for verification, which discovery does anyway). The normative commitment is to the property. The concrete construction is deliberately not yet pinned: it is decided together with the substrate choice (open question 11), where a construction that lets an identity survive key rotation must also be weighed (see that question and question 20).

### 3.1 Producer and consumer are per-edge labels

A node exposes a set of capabilities, some provided and some required. "Producer" and "consumer" describe the role relative to one capability on one edge, never the node as a whole. A bidirectional relationship is two ports, not one duplex channel, because the two directions fail independently. Each direction MUST carry its own declared safe state and its own liveness contract.

The slot or topic contract owner is the steward (Section 9). Implementations and documentation MUST NOT use "consumer" for that role; the steward need be neither on the data path nor the receiving end.

### 3.2 Capability shape

Every capability declares one of three shapes in its contract:

- **stream-produce** and **stream-consume**: one-way flow (notes, torque commands, telemetry).
- **request-response**: a first-class shape. The correlation between a request and its matching response is the content of the capability and cannot be reconstructed from two independent one-way flows.

## 4. Discovery and authority

### 4.1 The central split

Two meanings of "capability" are kept rigorously separate:

- **Feature-capability**: what a thing is. Self-describing, discovered, ambient by default (Section 4.7).
- **Authority**: whether a thing may participate in a given function. Granted, never discovered.

Discovering that a node satisfies an interface confers no authority. Admitting it into a function is a deliberate, non-discoverable, verifiable act. Hazard analysis attaches to the slot and its required interface, fixed at design time; the identity filling the slot may vary at runtime without reopening the safety case, provided it satisfies the contract and passes admission.

> Discovery proposes; binding disposes.

### 4.2 Stake and the authority ladder

Authority strength MUST scale with the stake of the action. The rungs, weakest first:

1. **Ambient (presence-based)**: being on the bus, in the room, or reachable on the network is itself the entitlement. This is the model systems fall into by default and it is almost always a mistake. It is acceptable only when two factors are both high: the difficulty of illegitimate presence, and the lowness of the stake. Either factor failing disqualifies it.
2. **Granted**: an explicit, verifiable, expirable grant (Section 4.1).
3. **Granted with attestation**: the grant is valid only alongside an attestation from a party the verifier trusts (Sections 4.3, 9.2).
4. **Granted, attested, multi-party**: for the highest stakes, authority that no single party can mint.

Presence MAY contribute evidence to an authorization decision; it MUST NOT be the decision.

The protocol constrains on **declared and attested claims, never on real-world effects**. A guard phrased as "ambient authority may not command an actuator" is unenforceable, because the protocol cannot know what a capability does in the world. Instead: ambient authority is valid only for a capability declared and attested as lowest-stake, and high-stake authority requires attestation to act. Under-claiming is therefore self-defeating: declaring low stake to avoid attestation yields only low-stake authority, and the high-stake action stays unreachable. Over-claiming is handled by Section 4.5. Wherever this specification says "safety-critical capability", read "declared and attested as such".

### 4.3 Attestation and exclusion are coupled

Attestation is the only sanctioned in-protocol exclusion mechanism, and attestation and the right to exclude third-party parts are two ends of one lever:

- It MUST be possible to build a secure system without attestation.
- It MUST be impossible to have attestation without a secure system.

The forcing is structural, not a rule layered on top. To exclude a part by attestation, the system must bind each part to a cryptographic identity, check it against a trust root, and reject parts that cannot prove themselves; that rejection is theft-resistance (a stolen or swapped part cannot attest into a system it was never enrolled in), co-extensive with whatever scope is excluded. A manufacturer who skips attestation forfeits in-protocol exclusion, and the aftermarket is open by default. The contradictory position, exclusion without security, is not a state the mechanism can occupy within the protocol. Keeping attestation the sole sanctioned exclusion path (so that a proprietary handshake or serial-number check cannot route around the coupling) is open question 23.

### 4.4 Transitive trust

When a system spans nodes held to different standards, onward trust follows a connecting-flight rule: passengers re-clear security at a hub the destination has not certified as equivalent.

- The unit of trust is an attested **regime** (the standard a node enforces), not the node and not the payload.
- Trust levels form a small set of **named tiers**, not a continuous score (for example: self-asserted; attested by an owner-trusted party; attested under a certified-equivalent regime; re-screen required). Continuous trust scores are illegible and gameable, and are not used.
- Onward trust is the **minimum regime along the path**: a floor carried with the payload, lowered by the weakest link, never raised by a later strong hop, restored only by re-screening at a node that vouches from its own root.
- The receiving node decides locally: it compares the carried floor against its stake-scaled requirement and then accepts, re-screens, downgrades the action to what the floor permits, or refuses.

### 4.5 Trust governance

There is no central body that defines who may attest. A consortium of blessed attesters is rejected outright; it is the single point of capture the architecture exists to avoid.

- Anyone MAY attest, and anyone MAY require attestation. "I accept attestations from X" is a local, owner-held edge, not a global fact. There is no central list to capture, by construction.
- The owner holds the trust roots and defines their own equivalence table (which regimes satisfy which tier of Section 4.4).
- **Trust authority transfers by attested update.** The requirement to attest is itself mutable via an attested change. A vendor's last act (or a court's, or a successor's) can attest a transfer of attestation authority to a community, a successor, or the owners; devices that trusted the vendor then trust the new authority by the same mechanism that always governed them. There is no special abandonment mode.
- Over-attestation is not prevented; it is made survivable and self-limiting. The over-attester bears the build and maintenance cost and the abandonment liability; the stake claim and its attestation requirement are inspectable and forensically logged (Section 15), so over-classification is conspicuous and contestable; and owner-held roots plus attested transfer give the owner a route around it.
- Owner sovereignty relocates the attack surface onto the owner, who can be socially engineered. Re-rooting trust MUST therefore be conspicuous, reversible, and forensically logged, never silent. The behavioural floor (Section 16.3) bounds what even a maliciously trusted attester can do at the actuator.

### 4.6 Device lifecycle and ownership

#### 4.6.1 Operability and ownership are orthogonal

A device is operable under whoever owns it now; ownership decides the governance root, not whether the machine works. Low-stake operation MAY rest on ambient authority (Section 4.2); high-stake operation REQUIRES a grant from the current owner; governance acts (persistent updates, fleet enrolment, re-rooting, revocation) wait for the new owner after a transfer. A capability MAY declare itself inert until commissioned (a grid inverter ships refusing to feed the grid until owned); this is a per-capability stake declaration, not the global rule.

#### 4.6.2 Identity birth and the two keys

At manufacture, the device generates its own identity keypair inside a secure element. The manufacturer signs a birth certificate over the public key and MUST NOT hold the device private key. Two keys are kept rigorously separate:

- The **device identity key**: on-device, never divulged. It signs telemetry and proves "I am this device".
- The **owner root key**: authority. The owner holds the private half; the device holds the public half and obeys delegations signed by it.

Ownership transfers from the supply chain to the buyer by a zero-touch voucher; the human act is scan, tap, or click, never a command-line ritual. This composes over existing mechanisms (IEEE 802.1AR IDevID/LDevID, FIDO Device Onboard, BRSKI per RFC 8995, on-die secure elements) rather than inventing a new onboarding scheme; reconciling their PKI- and cloud-shaped assumptions with the local-first posture is open question 28.

#### 4.6.3 The owner operates at the policy layer

The owner signs *who may publish* (a delegation), never the payloads themselves. Re-rooting an entire fleet is one owner-signed superseding delegation: monotonic (Section 13's fencing applied to authority, so no revocation list is needed in the field), diffused eventually-consistently (Section 8), and verified independently by each device. One owner action, not one per device.

Hard precondition: owner-root enrolment at commissioning, in bulk, zero-touch. If enrolment is skipped and the vendor later dies with no successor named, the only remaining path is per-device physical re-commissioning, which does not scale. This failure is named rather than papered over.

#### 4.6.4 Propagation through intermediaries

Subordinate devices with no uplink of their own receive owner-signed changes relayed through intermediaries. Acceptance is content-trusted and relay-agnostic: the subordinate verifies the owner's signature, never the relay's say-so. Trusting the relay would let a compromised intermediary hijack ownership of everything behind it (see Section 8.3). Propagation is eventually consistent; mixed states are safe in the interim.

#### 4.6.5 Ownership domains

Ownership is held at the level of the **ownership domain**: the set of devices sharing an owner root, which is the unit of transfer. Nesting (a dealer's domain contains a car; the car contains its components) reuses the steward-of-stewards recursion (Section 12). Ownership grouping is a distinct axis from functional composition: devices can share an owner without being wired together, and be wired together without sharing an owner. The domain is named as the transfer unit and nothing more; membership and partial-transfer machinery are not built until a domain needs them. Partial transfer (selling a part out of a domain) is unbind plus re-enrol.

#### 4.6.6 Transfer failure modes

A forgotten transfer, a deliberately retained root, and a dead vendor produce the same end state: the root is held by a non-current-owner who is not completing the handoff. Three layered defences:

1. **Legibility.** Ownership state is an inspectable declared fact, so an unfinished transfer is visible at the point of sale rather than discovered later.
2. **Proof-of-purchase recovery.** A path to complete a transfer after the fact from the buyer's side; ideally the claim voucher travels physically with the device.
3. **Forced physical re-commissioning.** A destructive last resort (factory-reset then claim), with theft-resistance from friction plus forensic logging. This floor guarantees the protocol never permanently locks out a legitimate owner.

Honest limit: root holder gone, no recovery oracle, and re-commissioning locked down leaves the buyer stuck. This is strictly better than today's invisible and unrecoverable locks, and not perfect.

#### 4.6.7 Retained ownership

The protocol cannot force a manufacturer to transfer ownership. On-device key generation at least prevents the manufacturer from holding the device identity key. Beyond that, the defence is legibility: "is this device genuinely owner-transferable" is a declared, attestable, inspectable property, so retained ownership is conspicuous and contestable by markets, regulators, and repair law, rather than buried.

#### 4.6.8 The handoff backstop

The end-of-life handoff path must never dead-end. The always-valid target is the owners themselves (release-to-owners): it distributes authority rather than concentrating it, every device has an owner-root slot, and it cannot be captured. A vendor MAY pre-name a successor to preserve update continuity; a dead-man's switch SHOULD make release-to-owners automatic on prolonged vendor silence. Paid succession and escrow services are legitimate but MUST be plural, opt-in, and downstream, never a single privileged recipient.

#### 4.6.9 The three layers of bringing a part into a system

Three layers MUST NOT be collapsed; collapsing them is the diagnostic-port theft pattern, in which physical presence equals authority to act.

- **Layer 1, ownership** (whose is it?): after a physical reset, the part adopts the owner root presented in a bounded claim window. Trust at this one moment comes from the physical situation; a freshly wiped part has no prior anchor against which to verify a signature.
- **Layer 2, admission** (may it act as X here?): owning a part does not let it act. The role's steward signs a grant binding the part's identity into a specific role (Section 9.2). Owned-but-not-admitted is a real, distinct state.
- **Layer 3, attestation** (gated roles only): if the role requires attestation, the Layer 2 grant is valid only if the part also carries the required attestation. Open roles skip this layer.

Presence buys only Layer 1, only at the one bootstrap moment where no key relationship yet exists, only on a part the holder physically reset, and reversibly. It buys nothing in Layers 2 or 3.

#### 4.6.10 Salvage bootstrap

A salvaged part MUST be re-homeable by anyone with physical access: no vendor, no account, no app. A physical reset puts the part into a claimable state for a bounded window; it joins the domain of the first node to issue a deliberate claim in that window (pairing-mode shaped, never "the first packet on the air"). The reset MUST be physical (a jumper, a button held through power-on, a disassembly step), never a software command alone, and the part can always be reset again: the most recent physical possessor wins. A reset salvaged part still cannot attest into an attestation-gated system; theft-resistance lives at admission and attestation, not at the part.

#### 4.6.11 The containment pole

Some parts must refuse to operate anywhere but their authorized system (a safety interlock, a dosing controller, an immobilizer). This is the same machinery with the dials reversed: a grant naming one specific system, plus a declared safe state of "inert" when not bound into it. Absolute, permanent non-transferability is deliberately not offered at the protocol level; un-resettable binding is the same mechanism as brick-forever and is refused. Useless-if-removed, where required, is a hardware tamper response below the protocol. Permanence and exclusivity MUST themselves be declared, inspectable properties: legible non-fungibility is permitted and contestable; silent non-fungibility is forbidden.

#### 4.6.12 Compute floor

The above requires elliptic-curve verification and ideally a secure element. That is feasible on most modern microcontrollers, but it is a real floor: a truly trivial part with no secure element cannot participate.

### 4.7 Discovery visibility

Feature-capability is discovered, and by default discovery is ambient. Announcing a capability is itself stake-bearing for some nodes: it can leak topology to passive listeners and solicit probing of high-stake targets. Discovery visibility is therefore a per-capability declared property with three rungs: **ambient** (the default), **authenticated-before-disclosure** (announce only a key; reveal capabilities to an authenticated peer), and **no-broadcast rendezvous** (advertise nothing; a legitimate initiator connects to a known endpoint and authenticates first).

This is attack-surface reduction only. Hiding is not securing: a node MUST refuse unauthorized commands regardless of its discovery visibility, and reduced visibility MUST NOT stand in for granted authority. The seam is reserved; only the ambient rung is required (open question 26).

### 4.8 Attestation authority

An attestation is assent from an authority, addressed as one. Section 4.2's ladder requires attestation for high-stake action. This section specifies what the attesting authority may be and when its assent is checked.

Per-property and per-event attestation are distinct. A **per-property** attestation is a durable, cacheable claim bound to an identity, a definition, or a role (Sections 4.3, 9.3). It is verified offline against a signature already held, it survives partition, and it is the default. A **per-event** attestation is assent to one specific action at the moment it is taken. It cannot be cached, because it concerns this event and no other.

Per-event attestation carries a hazard the per-property case does not. If every event must reach a designated authority while it acts, that authority is a central resource, a liveness dependency, and a single point of capture, which the architecture refuses. The hazard is resolved by the authority's structure, not by avoiding per-event attestation. A single designated attester is a central resource. A quorum is not: it needs k of n independent parties to assent, no one of which is load-bearing, and it survives the loss of any individual member. Per-event attestation is therefore permitted only where the authority is itself decentralized (a quorum or pool), and only at stakes that justify its cost.

A quorum does not remove the reachability cost. Reaching k members at action time is a latency and availability cost a cached property does not have, and under partition the quorum may not assemble. A capability that gates on per-event attestation MUST declare a safe state for the case where assent cannot be obtained in time, and MUST take it rather than act unattested. The choice between per-property and per-event is stake-scaled: the higher and more irreversible the stake, the more a capability will pay the per-event liveness cost rather than rely on a cacheable property.

The attesting authority is structured, not opaque. An authority may be a single signer, a threshold quorum, or a delegation chain, and it is addressed as one in every case. The protocol's model of it is structured: a set of named member identities, a threshold, and, where members are not interchangeable, their roles. A threshold signature (Section 14) MAY transport a quorum's assent as a single object verifiable against a single key. That is the opaque case, and it is a degenerate configuration of the structured one, not a separate mechanism.

Structure is mandated rather than hidden because four properties are not expressible without it, and each is load-bearing in the protocol's harder domains:

- **Progress.** Under partition a node must reason about partial assent: how many of k have signed, who is missing, whether to wait, time out, or fail safe. An opaque threshold signature is binary and cannot express "in progress".
- **Attribution.** When a quorum-attested action is later found wrong, the forensic plane (Section 15) needs to know which members assented. Threshold signatures are designed to hide the individual signers, so opaque assent and attributable assent are in tension, and the attribution requirement forces the structured form wherever stakes demand it.
- **Heterogeneous roles.** "The sender and the receiver both assent" is not flat k-of-n; the members are required and non-interchangeable. This needs structure the protocol can see.
- **Membership change.** Quorum membership changes over time, and that change is itself an attested change the trust model must be able to reason about (Section 4.5). Membership hidden below the interface is invisible to it.

A verifier that needs only the fact of assent reads a structured attestation as one bit and never inspects its members. This preserves the legibility of low-stake domains, which run the degenerate single-signer or opaque-quorum case and touch no structure. A verifier that needs progress, attribution, or membership inspects the structure. The structure is present but ignorable. This is the pool pattern (Section 10) applied to authority: a quorum attester is a pool of attesters, exposed at the interface and ignorable, never erased below it. How much structure an implementation must carry before the legibility budget is breached is open question 31.

Quorum membership binds to a durable principal, never to a node. A seat in a quorum is a role bound to a stable identity, a bank or an institution or an owner, in the sense of Section 4.1. The node that presents a seat's assent need not be stable, and often is not. It holds a short-lived delegated grant to attest as the principal, rooted in the principal's key, and the verifier checks that the assent chains to the seat's bound identity and satisfies the seat's role. The presenting node's own identity is not part of the quorum. Churn is therefore handled by expiry, not by membership change: a vanished incumbent's grant lapses (Section 14), and the principal delegates afresh to whatever node is current, with no change to the quorum contract. A seat MAY itself be backed by a pool of such incumbents (Section 10). A quorum of stable principals then composes over fleets of ephemeral nodes: the seats are named and few, while the nodes behind each seat are many and replaceable.

Per-event attestation has a negative path, and absence and dissent are distinct events on it. Absence is a member that cannot be reached: the dead-man's switch fires and the capability takes its declared safe state. Dissent is a member that is reached and affirmatively declines, as a sending party with insufficient funds declines to attest. Dissent is information, not silence. It MUST be carried as a signed negative that propagates like a distress report (Section 15), never inferred from a timeout, and a node MUST distinguish the two: absence may be waited on or retried, while dissent is a decision. Whatever was staged in anticipation of assent is released by the negative path. A stage is a held resource whose declared safe state is release on loss of liveness or on signed refusal, the held note of Section 9.2 in another domain. The fencing token (Section 13) makes the release safe against a late assent: an assent arriving after a stage is released carries a token the resource has already superseded, and is rejected. Compensation for a refused multi-step action is the ordinary safe-state machinery, not a new mechanism.

Assent is not commit, and commit is not finality. A high-stake per-event action has a lifecycle the protocol carries requirements across but does not itself complete:

1. **Stage.** A held resource with a release safe state, as above.
2. **Assent.** The quorum agrees the action should commit. This is refusable and may be partial. It is not the commit.
3. **Commit.** A durable, idempotent write to the source of truth. The protocol requires that assent gate such a write; it does not provide the durability.
4. **Finality.** The durable, agreed, attributable record (Section 14). It lives in the source of truth the protocol defers to (Section 1), not in the protocol.

The source of truth resolves the uncertainty consensus cannot. When a confirmation is lost, with both parties having assented, the link dropped, and the outcome unknown, the resolution is a read against the source of truth keyed by a transaction identifier or fencing token, never a re-run of the quorum. The write MUST be idempotent so that the read-or-retry is safe. The protocol's role is to require that the gate terminates in a durable, idempotent commit and to witness the finality record. The durability, the ordering, and the truth of the balance remain the deferred authority's (Section 1). Outcomes that no read can undo are the irreversible-activation class (open question 17).

## 5. The two planes

Live event delivery and identity/capability/configuration state have opposite requirements and MUST NOT share machinery.

| | Control / identity / capability plane | Real-time event plane |
|---|---|---|
| Carries | identity, capability state, slot schemas, bindings, grants, configuration | the live stream (notes, torque commands, telemetry) |
| Requirements | reliable; local-first; eventually consistent is acceptable | low latency; loss-tolerant |
| Loss handling | convergence on reconnect | loss recovered by journaling, never by trading latency for ordered-reliable delivery |

## 6. Transport binding

Transport is not specified, but it is not opaque: latency, ordering, reliability, duplexness, and MTU leak through to whether a capability works at all.

- Transports declare properties: latency class, ordered or not, reliable or not, framed or not, MTU.
- Capabilities declare requirements.
- A matching step binds a capability to a transport only where the declared properties satisfy the declared requirements. Implementations MUST refuse the binding otherwise.

## 7. Non-functional envelopes

The declare/require/match shape of Section 6 generalizes from the transport to the capability. A capability's contract MAY carry a non-functional envelope (latency budget, jitter tolerance, liveness interval and staleness deadline, delivery guarantee, throughput), declared per edge (Section 3.1: a gesture port and a feedback port have different needs). Four motions, all reusing existing machinery:

1. **Declare** the envelope in the capability contract.
2. **Match at admission**: refuse to bind where the substrate or path cannot claim the requirement.
3. **Witness at runtime**: the forensic plane (Section 15) records promised versus actual.
4. **Fail on violation**: a breached timing or liveness guarantee is a liveness failure and fires the declared safe state (Section 16).

Murmur declares, matches, and witnesses these requirements. It does not itself provide hard real-time guarantees; those remain the substrate's or the certified domain controller's to deliver. The envelope deliberately carries a few load-bearing dimensions plus a reserved seam, not an exhaustive QoS vocabulary (open question 27). An envelope dimension that cannot be measured is not admissible.

## 8. Definitions and encoding

### 8.1 Three layers

The artifact humans write, the abstract contract, and the artifact machines exchange are three different things, and none may masquerade as another.

```
Authoring surface     ->   Contract definitions    ->   Wire encoding   ->   Transport
(YAML + Starlark)          (capabilities, slots,        (protobuf,           (pluggable,
                            roles, policies)             compiled)            Section 6)
```

- **Authoring**: YAML for static declarative definitions; Starlark for programmatic ones (parameterized or templated generation, with deterministic sandboxed evaluation and no arbitrary I/O). Both compile to identical contract definitions; the choice is ergonomic, not semantic.
- **Wire**: protobuf, compiled, never authored by hand and never surfaced to users. Protobuf is an encoding, not a transport; it rides whatever transport Section 6 selects.

### 8.2 Definition identity and distribution

Definitions are versioned artifacts that are named, distributed, verified, and updated in the field, including on devices with intermittent, low-bandwidth connectivity. A system that discovers capabilities at runtime must also be able to learn and update what those capabilities mean without a full redeploy.

- A definition's identity is **content-addressed and signed**: a hash plus a publisher key, not a mutable name on a server.
- Two registry kinds are first-class. A **public commons**: an open, neutral, ungated registry of common definitions, stewarded rather than owned; this shared vocabulary is the one thing a no-coordinator system legitimately coordinates. And **private registries**: an operator's curated, access-controlled, audited registries for its own fleet.
- Verification and certification ride on the open commons as signed attestations layered over it, never as a gate on the vocabulary itself.
- Definition updates to field devices reuse the protocol's own machinery: distribution is control-plane (Section 5), eventually consistent, tolerant of arbitrary disconnection; provenance is a hash-linked signed log (Sections 14, 15); application is fail-safe (Section 16). An update that cannot be verified or completed MUST leave the device in its declared safe state, never half-defined.

### 8.3 Trust model for distribution

Trust comes from what the artifact is, never from where it came from. Verification is byte-identical whether a definition arrived from the commons, a private registry, a peer, or a USB stick. Trusting a received update decomposes into four distinct questions (the decomposition established by The Update Framework and carried into vehicles by Uptane), which implementations MUST NOT conflate:

1. **Integrity and authenticity**: is this what publisher P published? Content address plus signature.
2. **Authorization and provenance**: is P allowed to define this capability? Trust root, delegation chain, or attestation.
3. **Freshness and anti-rollback**: a malicious peer can serve a genuinely signed but stale, since-revoked definition. Devices MUST enforce monotonicity over the signed decision sequence, not over the artifact version: each activation decision carries a sequence number above the highest seen, and a device rejects any decision below it. This is the fencing token (Section 13) applied to definitions. An authorized reversal is therefore not a rollback in this sense: it is a new, higher-sequence decision that activates an older artifact (Section 8.5), moving forward through decisions while moving backward through artifacts. Replay stays defeated, because a replayed stale artifact arrives with no new signed decision. Pair with expiry and gossiped signed revocations.
4. **Availability and eclipse**: peers can withhold but cannot forge. A node that cannot confirm currency within its declared window MUST degrade rather than trust indefinitely old definitions: fail safe on stale.

A peer relaying an update, even a peer bound to the same slot, confers zero authority on the content. Transport trust is never content trust.

### 8.4 Fleet propagation and versioning

A fleet update is not a transaction that completes. Under intermittent connectivity it is a wavefront that may never finish, so mixed-version operation is the designed-for steady state.

- There is no coordinated global rollout sequence; one would assume a coordinator and a completion guarantee the architecture forbids.
- The contract carries an explicit **compatibility relation**: a v2 definition declares whether it is backward-compatible with v1 (open question 14). Compatible changes make any arrival order safe.
- Version is per-edge and per-binding, never per-device. A node bound into slots owned by different stewards may speak v1 on one binding and v2 on another.
- Design rule: **stewards tolerate a range; providers speak one version.** The steward population is smaller, more capable, and easier to update, so it absorbs compatibility; the larger provider population migrates lazily in any order behind that tolerance.
- A breaking incompatibility is a semantic disconnection: the binding goes stale and fires its declared safe state (Section 16), with the same machinery as a dropped link. There is no separate rollout-safety subsystem.

### 8.5 Activation

Distribution and activation are separate. Distribution (getting verified bytes in place) is lazy, eventual, and peer-tolerant. Activation (switching the running contract) is a distinct, guarded event.

- Activation MUST be gradual and canaried with automatic halt. Nothing central stages this (Section 8.4); canarying is a discipline each node applies to itself. A node activates only after a local observation window of attested silence: no credible distress concerning the definition, where the silence itself is evidenced fresh, since silence a node cannot verify as live MUST hold activation rather than permit it. Attested silence MUST also be inhabited: an all-clear over a population that never activated is vacuous, so observers' statements carry exposure ("N bound providers run this definition, no distress"), exposure claims are subject to the same relevance test as distress, and a later-wave node gates on attested exposure of earlier waves wherever any exist. A node with no earlier wave to wait for is knowingly the first activator and is governed by the evidence requirements of its declared stake. Holds are instrumental, never intrinsic: a hold MUST name the evidence it awaits, and where that evidence cannot arrive (no peers exist for the configuration, or no gossip reach exists at all), the hold collapses to a decision on the evidence in hand rather than persisting as delay for its own sake. For a node with no gossip reach at all (an isolated system updated from physical media), the signed evidence bundle carried with the artifact stands in for live silence, frozen at the moment of export; accepting that horizon MUST be an explicit owner policy, never a silent default. A node that activates and trips its safe state publishes a signed distress report (its steward publishes one on its behalf if it dies unspoken, detected through the binding's liveness contract), which halts further activation wherever it propagates. Widening is emergent (verified exposure of earlier waves plus verified absence of distress, never elapsed time alone), and never a go signal from a rollout controller. A node SHOULD NOT activate ahead of the evidence its declared stake requires; where no lower-stake population exists to generate that evidence, it comes from shadow execution (the new definition run on live inputs with outputs fenced from the actuator), publisher-supplied rigs, or attested offline qualification. The mechanics are open question 16. The mixed-version window is the blast-radius limiter, not a problem to eliminate.
- Synchronized fleet-wide activation is an anti-pattern wherever failure can be irreversible. It converts independent small risks into one correlated large risk, destroys mid-rollout observability, and is itself a physical hazard in shared systems (a thousand inverters hitting safe state at once is a grid event).
- Reversibility is first-class: the old definition stays resident and hot, so apply has an unapply. "Can this be rolled back" is a property of an update, not an afterthought. Updates with physically irreversible side effects are a named class requiring stronger gates (open question 17).
- An update is **routine** unless its publisher declares it **remedial** against a named defect. A routine update MAY be held indefinitely; the wavefront never finishing is the designed-for steady state (Section 8.4). Continuing on the current version is operationally safe by construction (the shipped safety case still holds, and a hold creates no new hazard) but not indefinitely secure once a remedial update exists, since exposure on the named defect accumulates with time. Remedial holds MUST therefore be bounded, with deadlines scaled to declared stake. The remedial claim is itself attestable and auditable, and making it raises the publisher's evidence burden rather than lowering it: the rush attack (every update declared an urgent fix) is the dual of the freeze attack, and both are claims to be made legible, never trusted outright.
- A capability MAY declare a readiness predicate that delays activation ("only when idle, between cycles"). For a routine update the predicate may hold as long as it likes; for a remedial update it is bounded by the same deadline as every other hold, because an unbounded hold on a fix is a denial-of-service vector: delaying for smoothness is fine, indefinite delay of a fix is worse than a capability-scoped safe-state trip. At expiry the node MUST NOT simply continue as if no clock had run: it activates if its evidence bar is met, and otherwise escalates by degrading the affected capability toward its own declared safe state, shedding high-stake authority first and function last, which bounds exposure without activating unvetted code. Escalation is per capability, never per system: the blast radius of a stuck update is the capability it is stuck on, and a system-wide response to one capability's stuck update is forbidden.
- **Reversal is not only automatic.** The canary halt has a manual sibling. An owner MAY sign a reversal across their domain, and a steward MAY sign one across its topic: ordinary scoped governance acts, expressed as forward decisions that activate the resident older definition (Section 8.3). Reversing a remedial update is within the owner's sovereignty but MUST be conspicuous and forensically logged; the re-accepted exposure becomes an attestable fact.
- **Supersession and the compromised publisher.** A publisher MAY supersede an in-flight update. Supersession propagates at the same priority as distress, and a node that never activated the superseded version skips it under the decision-sequence rule. Whether a superseding fix inherits accumulated evidence is open (questions 14, 16); fresh evidence is the default. A compromised publisher will not sign the cure, so reversal escalates through other authorities at their own scopes: canary halt, steward hold, owner reversal, and finally revocation of the publisher's authority itself through ordinary trust governance, the same attested-transfer machinery that handles a dead vendor (Sections 4.5, 4.6.8).

## 9. Topics, slots, and binding

The primitive is the **topic**; the **slot** is its degenerate case (one steward, capacity-1 binding). Defining it the other way around leaks two false assumptions into everything downstream: that the contract owner is on the data path, and that there is one failure root.

### 9.1 Slot

- A slot is a named role defined by a steward, with a required interface and a declared safe state. It is first-class and persists whether or not it is filled.
- Slot states: `unfilled`, `bound-and-live`, `bound-and-stale`. The transition to stale fires the slot's safe state.
- **The safe state belongs to the slot, not the module.** An identical motor controller reads `freewheel` in a drive slot (a held wheel on a lost link is uncommanded propulsion or single-wheel braking, a stability hazard) and `hold-torque` in a hoist slot (freewheeling drops the load). Two genuinely different declared safe states for one module is the point.

### 9.2 Safe states are named capabilities

A declared safe state (`freewheel`, `hold-torque`, `ramp-to-zero-then-freewheel`) is a named capability a node provides and a slot requires, matched by ordinary interface satisfaction. There is no separate safe-state subsystem. Matching establishes eligibility; **binding arms exactly one named safe state for that edge** and makes it locally resident, so it fires on link loss with no further instruction.

The protocol matches the name. What `freewheel` does in the world lives in the definition commons (Section 8) and, where safety-critical, in an attestation that a competent party stands behind. The protocol never classifies by effect (Section 4.2). Physical-environment constraints are below the protocol and explicitly not captured: two motor controllers on a mechanically coupled rotor are a physics problem the protocol cannot see. Conflicts between declared safe states on a shared physical resource are ceded to the system integrator's hazard analysis, backstopped by the physical floor (Section 16.3) and the forensic record. The protocol witnesses them; it does not adjudicate them.

A named safe state MAY be internally conditional ("return home unless the physical environment is compromised; otherwise freeze"), subject to three constraints that keep it a safe state rather than a smuggled response (Section 16.1). The predicate MUST be locally decidable: evaluable by the failing node alone, from sensing and state resident on the node at the moment of failure, in bounded time, with no dependency on the connectivity whose loss fired it. The conditional MUST totalize conservatively: branches are ordered by conservatism, and a predicate that cannot be evaluated takes the most conservative branch, never the most convenient. And the branch taken MUST be forensically logged. The Section 16.1 boundary is restated by this, not weakened: a safe state is what the local node does with local knowledge; the response remains what a coordinator does with global knowledge. The invariant is unchanged: binding arms exactly one name, whose full branch tree is fixed and visible to hazard analysis at design time. What is forbidden is selecting among safe states at failure time, a decision that needs exactly the information failure may have destroyed. How expressive the predicate may grow before it defeats legibility and certification is open question 30.

### 9.3 Binding and admission

- **Binding admits one identity into one slot.** Admission is the certified chokepoint.
- Attestation at admission follows the same declare/require/match shape as everything else. The **attestation is a credential carried by the part**, signed and bound to its identity key. The **requirement** (whether, at what tier, attesting what) is **declared by the role's steward**. **Sufficiency is judged at the binding**, where carried credentials are matched against the declared requirement and the grant records the pass. A part may carry credentials no role requires; a role may require credentials only some parts can present. Exclusion and theft-resistance both live at the match.
- The steward owns the schema and advertises it as a capability ("a thing with these slots and these binding rules"). A car and a synth rig differ in their schemas, not in the protocol.
- Admission is **consent-driven**: a member consents to join and declares its activation envelope at admission time (an inverter: "never dispatch me below 20% state of charge"). Consent to admit is not consent to activate; front-loading consent and envelope lets later activation be handshake-free yet sovereign.
- Ranking, priority, and scoring live in the steward, not the protocol. The protocol carries membership and state; the steward decides order.

### 9.4 Topologies

All topologies are expressible on the one primitive, and which applies is declared per capability:

- **Fan-in** (many producers, one steward): wheels reporting telemetry.
- **Fan-out** (one producer, many subscribers): a timing leader and its follower devices.
- **Mesh** (many to many, no centre): the rootless case the slot model cannot express, and the reason the topic is the primitive.
- **Multi-principal** (one node, many grantors): a node bound into slots owned by different stewards (a home energy manager and a utility aggregator) runs a **local arbiter** to reconcile conflicting grants within its declared envelope.

Someone always owns the topic's contract (schema, declared safe state, quorum rule), but that contract authority can be a registrar that never touches the data. The steward is direction-neutral and sometimes off the data path entirely. A rootless topic's contract MUST specify its quorum rule (Section 12.1).

### 9.5 Subscriptions are predicates

A subscription carries a predicate over payload or state, not just a topic name, and the contract declares where the predicate is evaluated:

- predicate = `true`: a plain topic subscription (the degenerate case).
- **Subscriber-side evaluation** (the default): ordinary filtering; no model assumption; retrofittable anywhere.
- **Fabric- or publisher-side evaluation**: content-based routing, in which non-matching messages never traverse the link. Architecturally significant, and justified only by physical constraints (constrained bus bandwidth, a safety controller that must not parse everything, a sleeping radio).

The seam is reserved, not the mechanism: content routing is a capability a transport or steward may later offer, never a model change.

## 10. Pools

A **pool** is an optional construct usable anywhere a single slot is. It is slot-shaped from the outside (same required interface, presents one winner), so a singleton slot can be upgraded to a pool-backed one without the steward changing anything.

Two patterns the word MUST NOT conflate:

- **Multiplicity slot**: capacity above one, all members active at once (four wheel slots, each capacity-1). Failure means the slot goes unfilled and the steward redistributes; there is no slot-level failover.
- **Redundancy pool**: one active member plus warm standbys; failover is promotion (two keyboards contending for one role; redundant IMUs; an aggregator choosing among inverters).

Model:

- A single binding is the degenerate pool: capacity 1, promotion policy none. The structure is committed to; no single failover semantics is.
- Candidate states: `eligible` (discovered, satisfies the interface, not admitted), `admitted-standby` (pre-granted, live heartbeat, idle), `active`, `stale`.
- Promotion policy is a pluggable slot-level declaration, the same shape as transport properties and election policy.
- The data interface stays transparent through the virtual winner, but the control interface MUST emit promotion as an event: degradation reasoning depends on knowing what is currently live.

A pool presents one capability while internally orchestrating many; this is capability composition, with the pool as the degenerate case where all sub-members satisfy the same interface. A composing node is a steward downward (to its members) and a producer or consumer upward (to its own steward) at once. Heterogeneous composition, where sub-members satisfy different interfaces, is recognized but deliberately out of model (Section 18.1).

## 11. State projection and handoff

Stateful capabilities make pure selection insufficient: a freshly promoted standby that does not know a note is held produces stuck or dropped notes.

- **State projection belongs at the consuming endpoint.** The node already receiving the winner's stream maintains "what is currently live" as a side effect of consumption. On promotion it replays resume-state into the new winner, or patches the seam itself (emitting the releases the new source cannot know to send).
- **Recover from observation, not replication**, wherever the state is fully observable from the consumed stream. This adds no new failure mode; the consuming endpoint is already the liveness anchor for that edge.
- Full stream-observability is the exception, not the rule. Most real capabilities carry hidden state (a sensor's internal calibration, an inverter's charge model, and the steward's own ledger). **That set, and only that set, requires member-side checkpointing or replication.** Identifying it per domain is open question 4.
- In a fan-out or rootless topic, each subscriber projects independently; there is no single consuming endpoint.
- Per slot, standbys are **pre-admitted** (keys exchanged and grant issued, so promotion pays no authorization handshake; always do this) and optionally **pre-warmed** (already receiving a shadow of the projection, making the switch sub-perceptual; a continuous cost, paid only where the slot warrants it).

## 12. Steward failure

A pool is a logical principal, not necessarily a physical node; its logic is co-located at the steward boundary. A free-standing pool component is a single point of failure holding the very state the pool exists to protect.

The recursion bottoms out. Pools and topics close under composition (a pool of pools, a steward of stewards), but there is always a root steward whose liveness is the trust anchor, made reliable by other means than another pool. There is deliberately no coordinator-of-the-whole to promote anything into.

Failing over a steward is categorically harder than failing over a member: the steward holds authoritative state (the ledger), is the trust root issuing grants, and is what producers are pointed at. Two honest options, chosen per capability:

- **Fail safe (harden a singular root).** The steward does not fail over; it fails safe. On steward death every slot goes stale from the top and fires its declared safe state. For most safety-critical stewards this is the correct, certifiable answer; in a vehicle, the motion controller is an internally redundant certified component, not something failed over by a discovery protocol.
- **Pool-backed virtual steward identity.** The steward becomes a slot backed by candidate stewards presenting one stable virtual identity, so producers do not re-point on switch. Costs: the steward's ledger becomes unobservable hidden state and MUST be replicated or checkpointed (Section 11), and the virtual identity needs a real threshold credential (Section 14). Reserved for availability-critical stewards.

### 12.1 Failure reasoning forks by topology

- **Star (single steward):** steward death is one clean event; all its slots fail safe. 
- **Rootless (mesh):** there is no central death signal. Each subscriber MUST independently detect publisher staleness and fire its own local safe state. Partition produces sub-flocks, each internally coherent, each potentially believing it is whole: split-brain with no quorum to arbitrate. Consequently fencing tokens MUST live at every actuator independently, and the topic contract MUST specify its quorum rule. Rootless buys the absence of a single point of failure and pays in distributed detection and split-brain exposure.

## 13. Leader election and fencing

No single election algorithm is baked in. The protocol standardizes the interface (candidacy, term or lease, and the obligation to fail safe on failure to elect) as a slot-level policy, the same shape as promotion policy and transport properties.

Local-first and partition-prone means there is no linearizable store to lean on; a lease object in a consensus-backed store is a lock on someone else's consistency, and that ground does not exist here. Election and the declared safe state are two faces of one coin: under partition, when a node cannot safely elect, it MUST fail to the declared safe state it already has. Safety is always chosen over liveness.

Three tiers, by domain:

1. **Trusted single steward** (a synth rig; a single-owner vehicle subsystem): election collapses to "the steward picks". No consensus needed; a ground exists.
2. **Crash-fault, bounded membership, no trusted arbiter** (peer ECUs): lease plus pre-designated primary plus deterministic failover, with the consistent store supplied deliberately.
3. **Multi-party, mutually distrusting** (grid participants): participants can lie, so crash-fault consensus is unsound; this tier needs Byzantine fault tolerance plus consent envelopes.

**Fencing tokens are the load-bearing safety mechanism.** Lease election alone is unsafe: a stalled leader's lease can expire, a new leader be elected, and the old leader wake and act. Therefore every leadership grant carries a monotonically increasing token, and the resource (the actuator: motor, inverter) MUST reject any command bearing a token below the highest it has seen. This makes split-brain safe at the resource even while election is momentarily ambiguous, which is the property actually needed, cheaper and stronger than global consensus. A leadership token is a time-bounded, monotonic authority grant enforced at the resource; it is the Section 4 authority machinery, not a new mechanism.

## 14. Cryptographic profile

The primitives are borrowed; global consensus is refused. Finality is an authority property, not a delivery property. Even perfect transport permits a double-spend. What rejects the second attempt is an authority that orders the two, not a link that delivers them. A blockchain in the dispatch path is a category error: global total-order consensus is the expensive way to get a weaker guarantee than resource-side fencing already provides locally and instantly.

That refusal concerns the real-time dispatch path, not finality everywhere. Finality is a third property alongside consequence-bounding and attribution: agreement among parties that a state transition is settled and will not be undone. Some transitions in conserved-value domains (payments, settlement) genuinely need finality among mutually distrusting parties, and that is the one case heavy consensus earns. It is delivered by per-event quorum attestation (Section 4.8) and deferred to a pluggable authority. It is never built into the protocol and never placed in a control loop. Banking two-party acknowledgement and blockchain proof-of-work or proof-of-stake are the same per-event quorum gate with different membership models: a small named set, or an open sybil-resistant one. Both establish agreed, attributable finality, not correctness. A fully attested transaction can be fully wrong, since a drained smart contract is validly signed and final, so correctness stays with the authorities the protocol defers to (Section 1). This sharpens open questions 6 and 25.

- **Self-certifying identifiers** (committed as a property, Section 3): authenticating an identifier is local verification of key possession, so name-spoofing is cryptographically impossible rather than checked. The concrete construction (raw encoded key, digest of key, or a rotation-surviving derivation) is open question 11.
- **Capability tokens** (UCAN-style): decentralized, offline-verifiable, local-first delegation chains for Section 4 authority.
- **Threshold signatures / distributed key generation** (BLS, FROST): the virtual steward credential (Section 12). Any k of n share-holders produce one signature verifiable against one unchanged public key, so steward failover yields the same signature the predecessor would have produced. Implementation maturity must be confirmed before depending on a specific scheme.
- **Hash-linked (Merkle) logs**: the authority-grant and binding history is an append-only hash-linked chain: tamper-evident delegation and efficient validity proofs without a blockchain.
- **Expiry beats revocation.** A delegation chain proves authority was granted, not that it was never revoked; offline verifiability and timely revocation are in fundamental tension. In any safety context, short-lived grants that must be renewed MUST be preferred over long-lived grants that must be revoked. Expiry is a connectivity-free dead-man's switch; revocation requires reaching everyone. A leadership lease is exactly an ephemeral capability renewed or lost.

## 15. Recovery plane and forensic plane

Operational state and the audit record are different artifacts with opposite requirements; one mechanism cannot serve both without corrupting both. They observe the same event stream and diverge in retention and integrity.

| | Recovery plane | Forensic plane |
|---|---|---|
| Focus | the present | the past |
| Mutability | mutable, ephemeral | immutable, write-once |
| Integrity | none needed | tamper-evident (hash chain) |
| Latency | low; in the failover path | irrelevant; never in the control path |
| Lives at | the consuming endpoint or pool boundary (Section 11) | a sink, attached where stakes justify it |
| Purpose | survive failover | survive disputes |

- The same event enters both: recovery holds a note-on until its note-off and then forgets; forensics appends it, hash-linked, forever.
- The forensic plane is an optional sink, not baked into every node. A synth rig runs recovery only; a vehicle or grid system attaches the recorder because liability and regulation demand reconstruction.
- A hash-chained single-writer log is tamper-evident without consensus. Where multiple distrusting parties must agree a log is complete, cross-checked per-party signed logs are preferred over a shared ledger (open questions 6, 25).
- Per domain, the recorder is **passive** (logs what it observes; the default) or **active** (events must be durably logged before they may act; heavier, used only where regulation mandates write-before-act).

The forensic plane is the protocol's role at the edge of its own authority: where Murmur cedes control (physical-world coupling it cannot mediate, overrides it must yield to), it retains witness. It records that something happened where it could not, and should not, govern how.

## 16. Safety and resilience

### 16.1 The failure core

- Safe state on loss of liveness is capability- and slot-specific and declared, never global (Section 9). A held note releases; a drive motor freewheels; an inverter anti-islands.
- The heartbeat is the dead-man's switch that fires the declared safe state.
- The protocol's job is fast, trustworthy detection plus a declared safe default. The response (redistributing torque across the live corners, re-deriving dispatch) belongs to the certified domain controller. Safety logic is never smuggled into the communication layer.
- This specification addresses graceful degradation. Functional safety in the IEC 61508 / ISO 26262 sense (fail-safe versus fail-operational design) is a distinct, heavier discipline and is not claimed here.

### 16.2 Longevity threats

Three distinct threats, with three distinct defences; conflating them yields a design that handles none.

- **Abandonment** (passive: the maker stops; the device orphans). Defence: openness. The definition commons outlives any vendor; content-addressed signed definitions verify with no origin server alive; the open specification and reference daemon are the floor that makes continuation always possible.
- **Obsolescence** (adversarial, external: the maker engineers the device to stop, often weaponizing the same trust machinery that protects against malware). Defence: owner sovereignty. The owner, not the manufacturer, is the ultimate root of trust for their own device. Trust anchors MUST be owner-re-rootable; there MUST be no vendor-only revocation of the owner's own grants. Local-first already removes the most popular obsolescence lever: there is no required centre to switch off.
- **Poison** (adversarial, inside the trust boundary: a validly signed, correctly versioned update that is malicious or bricking). Verification is defenceless here by construction; it checks provenance, not intent. Poison is contained and recovered from, never prevented: canaried activation with automatic halt (Section 8.5) catches it where incompetence would also be caught; reversibility survives it; implementation diversity reduces monoculture blast radius.

### 16.3 The physical floor

Every mechanism in this specification (signatures, fencing, canaries, envelopes) raises the cost of casual, remote, and accidental failure, and every one is circumventable by a sufficiently capable, physically present actor. This is intended. No software layer is the final safety authority. That is the cyber-physical instance of the general rule: the final safety authority is a layer the protocol cannot reach.

- For safety-critical capabilities a physical, out-of-band override below the protocol (an emergency stop, a manual disconnect, a fuse) is REQUIRED. It makes no decisions, so it cannot be tricked into a wrong one; Murmur neither mediates it nor can disable it; a physically present authorized actor can always reach it.
- The protocol MUST detect and gracefully yield to a legitimate out-of-band override, and forensically log it, rather than resist it as an attack. How software reliably distinguishes a genuine override from a spoofed one is open question 19.
- The **behavioural floor** (Section 13's fencing applied to intent: an actuator rejecting even a validly signed command that violates its declared safe envelope) is a cost-raiser, not an unbreakable guarantee. It is what makes owner sovereignty safe (the owner chooses whom to trust; the floor bounds what any trusted party can do), and it is deliberately not rooted somewhere nothing can reach.
- **Stake classification is owner-visible and auditable.** Every capability's autonomy classification (unrestricted, re-certification-gated, law-bounded) is a declared, inspectable, forensically logged property. The protocol cannot stop a manufacturer over-classifying everything as safety-critical; it refuses to be the instrument that hides it.

The protocol assumes it will be circumvented by a sufficiently capable actor and treats this as a required property. Its mechanisms raise attack cost and contain blast radius; they do not, and must not, constitute absolute prevention, because absolute prevention means an unoverridable system, which is the worse failure.

## 17. Conformance

This draft is not yet accompanied by a conformance suite, and its normative statements are still moving. The intended shape of conformance is fixed, though, and follows from Section 1:

- A conforming implementation honours the contract model: it verifies identities, grants, attestations, and definitions as specified; keeps the four axes distinct; arms declared safe states at binding and fires them on loss of liveness; enforces fencing at resources; and keeps the mandated state (ownership, classification, grants, transfers) inspectable.
- A product that presents the contract without honouring it (for example, one that never genuinely transfers ownership, or that hides a capability's stake classification) is non-conformant, and the specification is written so that such divergence is detectable from the outside.

A precise conformance clause, with test vectors, follows once the open questions that gate it are closed.

## 18. Open questions

These are the forks not yet closed, kept visible deliberately. Objections to any of them are the most valuable contribution this specification can receive.

1. **Slot capacity and failover shape per capability.** Which slots are multiplicity (no spare; steward-level degradation) and which are redundancy (real standby; promotion)? This drives the state machine.
2. **Which stewards must survive death rather than fail safe?** Decides where threshold keys and steward-state replication are paid for, versus a hardened single root plus safe state.
3. **Symmetry of binding.** Single-owner systems can treat binding as the steward's prerogative; multi-party systems need the member to be able to refuse or bound its role. The model must permit mutual binding even where a given domain does not use it.
4. **Which real capabilities have hidden state?** State not observable from the stream is the set that forces member-side checkpointing (Section 11).
5. **Automatic-within-envelope versus re-consent on promotion.** Front-loaded envelopes make promotion handshake-free; confirm envelope expressiveness covers the grid cases.
6. **Does any domain need agreement on shared history among distrusting parties**, rather than merely verifiable authority? The line between borrowed primitives and an accidental blockchain. Likely answer: per-party signed logs, not consensus. Sharpened (June 2026): provenance needs only per-party signed logs, but finality (agreement that a transition is settled and will not be undone) is a distinct need that some conserved-value domains genuinely have. It is met by per-event quorum attestation deferred to a pluggable authority (Sections 4.8, 14), not by the protocol holding consensus itself.
7. **Topology per capability.** For each real capability: star, fan-in, fan-out, rootless mesh, or multi-principal? Each rootless capability must additionally declare its quorum rule.
8. **Predicate evaluation locus.** Which capabilities, if any, justify fabric-side content routing rather than default subscriber-side filtering?
9. **Edge direction and request-response enumeration.** Split every bidirectional relationship into two independently failing ports; mark request-response capabilities so correlation is first-class.
10. **Naming.** Settled: Murmuration (system), Murmur (protocol), `murmurd` (reference daemon); steward, never "consumer", for the contract owner. Open sub-decision: whether the globally visible package and binary name is `murmurd` or `murmuration`.
11. **libp2p as substrate**: adopt it, or reimplement identity, discovery, and negotiation? This decision also fixes the identifier construction left open in Section 3 (adopting libp2p implies digest-of-key peer identifiers). To weigh alongside it: both raw-key and digest-of-key identifiers weld an identity to one key forever, while a rotation-surviving construction (an identifier derived from an inception key plus a signed key-event log, the KERI shape) lets identity outlive its current key, which bears directly on question 20.
12. **The fast-versus-supervisory control boundary.** Where exactly does the real-time control loop end and the Murmur supervisory plane begin? Sharpest in datacenter power, where the safe state is partly fast and physical. Misplacement is either control in the communication layer or a missed trip.
13. **Datacenter gap: validate or refute.** Whether a real gap exists beyond what DCIM, hyperscaler-internal power management, and power-aware schedulers already cover is an empirical question. Refutation is a successful outcome (see the primer's datacenter section).
14. **The compatibility relation** (Section 8.4). Define precisely when v2 is backward-compatible with v1 for a capability interface, and how breaking changes are declared. The fleet-update story rests on this. Includes whether a superseding fix inherits any of the superseded version's accumulated canary evidence, or starts fresh (the default, Section 8.5).
15. **OTA update mechanics for constrained, intermittently connected devices.** Delta versus full transfer, resumability across disconnection, the verify, hold, activate, reverse state machine, and the trust chain checked before acceptance.
16. **Coordinator-free canarying.** Gradual activation needs early activators, an observation discipline, and a halt that propagates across a partitioned fleet, with nothing central to provide any of them. The sketch (rationale in the primer's canarying section): wave membership derived deterministically from node identity and definition hash against publisher-signed thresholds carried in the artifact; randomized jitter within a wave; health inferred from attested silence, with distress reports signed by the victim, or by its steward when the canary dies before it can speak (the binding's liveness contract detects the death), propagating at higher priority than artifacts, and silence counted only while fresh short-expiry no-distress statements keep arriving, so withheld distress surfaces as staleness (the freeze-attack defence, TUF's timestamp-role move, one layer up), and only over attested exposure, since silence from a population that never activated is vacuous and arrival order must not become a de facto canary assignment; holds scoped to the steward's topic; stake tiers setting the evidence required before activation (population canaries, shadow execution fenced from the actuator, publisher-funded rigs, offline qualification attestations). Hard sub-questions: a distress hold is a freeze-attack surface against security fixes, so who may sign credible distress; a publisher-authored schedule cannot be the floor, so minimum canary discipline is device-side and steward-side policy; and stake must set the evidence bar rather than the queue, since a uniformly high-stake fleet that defers en masse becomes an unchosen, unobserved canary of everyone (and a unique configuration of sibling versions is a population of one), while "too important to canary" must stay self-defeating by keeping "activated on zero evidence" an attestable, legible fact; and the remedial clock: who sets the deadline, per stake tier, for fix-class updates, and the precise steps of the capability-scoped degradation ladder when a remedial hold expires without its evidence bar met. Acknowledged rather than solved: the isolated system (a vehicle updated from a thumb drive, a population of one with no gossip reach) activates on evidence frozen at export time and reports distress only on the next physical round-trip, so fleet learning keeps a permanent shadow in the shape of its isolated members. Interlocks with questions 14, 15, and 17.
17. **Irreversible activations.** Some applications have physical side effects no rollback can retract. Name the class and the extra gates it requires. Do not assume rollback always exists.
18. **Owner re-rooting versus certification.** The per-capability autonomy boundary: unrestricted; gated by re-certification (the owner can re-root, but the new authority must itself carry valid attestation); law-bounded. Hard sub-question: how re-certification works when the original certifier is the entity that abandoned the device.
19. **Physical override: authorization and graceful yield.** Who may invoke the out-of-band override, and how the protocol recognizes and safely cedes to a legitimate one rather than resisting it. The smart layer's detection of the dumb floor reintroduces a smart check that can be spoofed; this needs pressure-testing by people who have built emergency-stop systems.
20. **Where does persistent system identity reside through total component churn?** If every node is replaced, what is "the same system", and where does its identity live such that no single component is load-bearing for it? The sketch is a virtual identity backed by a churning peer set (Section 12), owner-held rather than vendor-held. Arguably the deepest open question in the specification.
21. **The legibility budget.** For each sophisticated mechanism: could a competent stranger reimplement it from this specification alone in twenty years? Where capability and legibility conflict, the trade must be deliberate and recorded.
22. **Legible, footgun-resistant owner trust decisions.** Owner-held roots relocate the attack surface onto a socially engineerable owner. How is re-rooting made conspicuous, reversible, and hard to do by accident, without reintroducing a central authority to "help" and thereby rebuilding the consortium?
23. **Sole-exclusion-path enforcement.** The attestation and exclusion coupling (Section 4.3) holds only if attestation is the only in-protocol way to exclude a part. How are non-attestation lockouts kept out of the sanctioned protocol, and out-of-protocol exclusion kept visible and contestable?
24. **Making graceful exit genuinely lower-friction than disappearing.** The handoff mechanism (Section 4.6.8) works only if attested transfer is actually the least-effort wind-down path. Pre-designated successors, a dead-man's switch on vendor silence, legal hooks: what makes "transfer authority" the thing an administrator reaches for over switching off the servers?
25. **Owner-held settlement without a central clearing house.** Contribution records (Section 15) can underwrite payment for grid services without the protocol becoming a market, but multi-party settlement that distrusting parties accept must not collapse into a central ledger. Overlaps question 6. Sharpened (June 2026): the settlement gate is per-event quorum attestation (Section 4.8), and banking acknowledgement and chain consensus are the same gate with named-few versus open-sybil-resistant membership. What stays open is the membership machinery an ownership domain must carry to host such a quorum (overlaps question 29), and the dispute, reversibility-window, and fraud authorities that sit above finality, since finality is not correctness.
26. **Confidential and authenticated discovery** (Section 4.7). Develop the visibility rungs without ever letting hiding substitute for authorization.
27. **Non-functional envelopes** (Section 7). Which few dimensions are load-bearing; the precise declare-versus-guarantee boundary; and the observability surface, since an unmeasurable envelope is theatre.
28. **Device lifecycle composition.** Composing IEEE 802.1AR, FIDO Device Onboard, and BRSKI, which are PKI- and cloud-shaped, with the local-first no-required-centre property; the compute floor and which devices it excludes; the salvage claim-window mechanism; and the reset-difficulty dial at both its poles (Sections 4.6.10, 4.6.11).
29. **Ownership transfer machinery.** The bearer-versus-bound voucher trade, the re-commissioning difficulty dial, recovery oracles for incomplete transfers, and how far ownership domains need membership machinery before the reserved seam must open (Section 4.6).
30. **Conditional safe states: predicate expressiveness versus certifiability.** Section 9.2 permits a named safe state to be internally conditional, bounded by local decidability and conservative totalization. A predicate language inside the most safety-critical path the protocol has is a mini-program in exactly the place the legibility budget guards hardest, and it borders the fail-safe versus fail-operational territory of functional safety that Section 16.1 declines to claim. How expressive may the predicate be (sensor reads, fixed thresholds, validity windows on locally held state) before the branch tree can no longer be certified, or reimplemented from the specification alone? Interlocks with questions 4 and 21.
31. **Structured versus opaque attestation authority** (Section 4.8). Attestation authority is structured (member identities, threshold, and roles) so that progress, attribution, heterogeneous roles, and membership change stay expressible, with the opaque single-signer or threshold-signature case as a degenerate collapse. How much of that structure must an implementation carry, and expose, before it breaches the legibility budget? Where does the line fall between low-stake verifiers that read one bit of assent and high-stake verifiers that inspect members, and how is per-event attestation's fail-to-safe-state behaviour specified precisely when a quorum cannot assemble under partition? Also open: the precise negative-path state machine, distinguishing absence from dissent, releasing staged resources, and fencing a late assent; and the stage, assent, commit, and finality lifecycle by which per-event attestation hands durability and outcome-resolution to the source of truth it defers to. Interlocks with questions 3, 6, 17, 21, 25, and 29.

### 18.1 Deliberately out of model

The model has a named ceiling so that the boundary is a decision, not an oversight. The model is: topic with a direction-neutral contract steward; capabilities typed by shape (stream, request-response); subscriptions as predicates with a declared evaluation locus; failure declared per edge and per topology. Star, fan-out, and rootless mesh are degenerate cases of it; pools and homogeneous composition are instances of it. Parked above the line, expressible later through the reserved seams but not built now:

- **Heterogeneous capability composition** (sub-members satisfying different interfaces). Recognized, not generalized.
- **Content-based and fabric-side routing machinery.** The seam is reserved (Section 9.5); the fabric is unbuilt.
- **Spatial and geometric routing** ("any sensor within this bounding box").
- **Streaming-to-discrete reconciliation**, and other shapes beyond stream and request-response.
- **Physical-world coordination channels and entrainment.** Coordination through channels the protocol does not mediate (speaker and microphone, heat, shared-bus voltage) is legitimate and expected. The protocol's only role at that edge is to witness it (Section 15), never to mediate it.

If a future need pushes any of these below the line, it should arrive through an existing seam (predicate subscriptions, the shape type, the steward-of-stewards recursion), not by reopening the spine.
