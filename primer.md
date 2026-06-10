# Murmuration Primer

This document is **non-normative**. It explains why the [Murmur specification](spec.md) is shaped the way it is: the motivating vision, the design principles, the reasoning behind the contract model's less obvious decisions, the relationship to neighbouring systems, and the demonstration roadmap. Where this document and the specification appear to disagree, the specification wins.

Readers new to the project should start with the [README](README.md), which explains the idea in plain language. This primer sits between the two: it assumes the README's framing and supplies the rationale the specification deliberately keeps out of its own way.

## Table of contents

- [The names](#the-names)
- [The grandfather's axe](#the-grandfathers-axe)
- [Design principles](#design-principles)
- [Why discovery and authority are split](#why-discovery-and-authority-are-split)
- [Why attestation and exclusion are coupled](#why-attestation-and-exclusion-are-coupled)
- [Why there is no consortium](#why-there-is-no-consortium)
- [The incentive engine, applied](#the-incentive-engine-applied)
- [The threat model: abandonment, obsolescence, poison](#the-threat-model-abandonment-obsolescence-poison)
- [Why declared failure semantics are the core](#why-declared-failure-semantics-are-the-core)
- [Lessons borrowed from elsewhere](#lessons-borrowed-from-elsewhere)
- [The witness](#the-witness)
- [The ladder](#the-ladder)
- [The datacenter case](#the-datacenter-case)
- [How to read the specification](#how-to-read-the-specification)

## The names

- **Murmuration** is the system: the emergent whole that no node coordinates.
- **Murmur** is the protocol: the local rules each node speaks to its neighbours.
- **`murmurd`** is the reference daemon that speaks Murmur.

The names are load-bearing, not decorative. A starling murmuration is the canonical case of global coherence arising from purely local rules with no central coordinator, and that is the architecture's central claim. Wherever someone is tempted to add a coordinator-of-the-whole, the name itself should push back.

The lineage is MANET (mobile ad-hoc networking) and swarm robotics: no infrastructure, dynamic membership, route around partition, no required central ground. That posture is inherited deliberately. What is not inherited is MANET routing: Murmur is a contract, identity, and authority layer above whatever moves bytes, not a multi-hop routing protocol. A transport underneath it may itself be a mesh; Murmur is not in that business.

One naming decision remains open (specification, open question 10): whether the globally visible package and binary name is `murmurd` or `murmuration`. The bare token `murmurd` carries a residual association with Mumble's VoIP server (historically named "Murmur") in the daemon register specifically. Inside the org path it disambiguates fully; the exposure is only where the binary name travels context-free.

## The grandfather's axe

The success criterion for the whole design is the grandfather's axe: an axe that has had three new heads and four new handles is the same axe. A system should retain its identity and keep functioning across the complete replacement, several times over, of every physical component, with no single part, and no absent vendor, load-bearing for its continued life. Concretely: a home battery, inverter, and grid connection still working in two decades, having outlived three generations of swapped hardware and possibly every company that made any of it.

This is the murmuration in the name: the flock persists while every starling in it is replaced. Everything in the specification, and the whole of its resilience apparatus, serves this. Even authority is treated as a replaceable component: the mechanism that lets a dying vendor hand its attestation authority to a community is the axe applied to trust itself.

The promise is to the owner (continuity), not against the manufacturer. Friction with replacement-dependent business models is a side effect of keeping the promise, never its purpose. A good manufacturer can sell on this ("interoperates and stays alive for thirty years, even if we are gone"); only a business model that depends on the opposite of longevity will route around it, and that is its choice to make, visibly.

## Design principles

### Legibility is a longevity requirement, not an aesthetic

A mechanism that can only be understood, repaired, or reimplemented by its original author is already abandoned. The classic-car lesson: a carburettor, a vacuum-advance, a washer-bottle squirt pump last fifty years because they are legible. A competent stranger can inspect them, understand them, and repair them with ordinary tools; there is no hidden dependency, no phone-home, and degradation is gradual and diagnosable.

The honest counterweight, with no romanticism: legibility trades against capability. Fuel injection genuinely beats a carburettor on efficiency, emissions, and cold-start, so simplicity alone loses. The point is that legibility and serviceability form a first-class design axis that capability-optimisation systematically under-weights. The axe requires weighing it explicitly: prefer the simplest mechanism that meets the requirement, and treat "could a competent stranger reimplement this from the specification alone, twenty years from now" as a requirement rather than a nicety.

This is a live tension in the specification itself. The model has accreted real sophistication, and each clever mechanism is a future black box unless kept legible. The open specification and the reference daemon are necessary but not sufficient; the specification must also stay simple enough to reimplement. Its eventual narrowing pass must apply a legibility budget, not only a feature ceiling (open question 21).

### The protocol is the ledger, not the bank

Murmur is to its products what a core banking ledger is to a bank: a commoditised middle that specifies how value moves and verifies that it moved, knowing nothing of branches, apps, or brands. The protocol normatively specifies the contract and its verification, plus the requirement that such state be inspectable. The product (a manufacturer's app, a fleet console, a cross-domain key wallet) owns everything else: onboarding, key custody, recovery, support, brand. Products compete on experience; the protocol does not specify it. Custody is the product's to provide; whether custody quietly becomes permanent capture is the protocol's to expose.

The analogy has a stated limit: it holds for build-versus-specify, not for trust topology. A bank is a trusted central custodian; Murmur is local-first and anti-central-party, so the "bank" here is one of many competing vendors, each subject to owner sovereignty and the protocol's legibility, never a trusted middle holding everyone's assets. Borrow the layering, not the centralisation.

### Local-first is strongest where stakes are highest

Drivetrain motion control and grid anti-islanding must not depend on a cloud round trip. Resilience and safety are derived from local reasoning plus declared safe defaults, never from the reachability of a central authority. This is also, structurally, the anti-obsolescence stance: a system with no required centre has no centre to switch off.

### Cede control, retain witness

Nodes interact with the physical world through channels Murmur neither owns nor mediates: a speaker and a microphone, heat and a thermal sensor, voltage on a shared bus. Emergent coordination through those channels is legitimate and expected. Applause is the canonical human example: a wave of synchronised clapping ripples through an audience with no conductor, through a channel nobody administers. The protocol does not try to bring such coordination inside. Doing so is impossible (nodes cannot be stopped from sensing each other physically) and would violate the legibility budget.

At the edge of its own authority, the protocol's role is to witness, not control: to record that something happened where it cannot or should not mediate how. A protocol that claims total control is either lying or tyrannical; one that knows the limit of its authority and chooses accountability at that limit can be trusted. The same posture governs the physical override (below): cede control of what the protocol cannot legitimately own; retain an honest record of it.

### The incentive-alignment engine

Most of the specification's seemingly separate decisions are one thing: an engine that makes the selfish choice and the social good inseparable, rather than enforcing virtue. The mechanism is a single stance: **the burden falls on the party that gains the most from a decision.**

Anti-social behaviour in connected systems is almost always externalisation: capturing a benefit while pushing the cost onto someone else. Lock-in externalises the cost of replacement onto the owner; abandonment externalises orphaning onto the owner; a consortium externalises the cost of exclusion onto everyone outside it. The engine re-internalises those costs onto whoever captures the benefit. Once a party can no longer externalise, its own selfish optimisation must account for the cost it would otherwise dump on others, and selfish and social converge. Worked instances: the party that wants exclusion must build theft-resistance and bears the abandonment liability; the owner who gains autonomy bears the trust decision; the steward who owns the contract owns the safe state.

Two disciplines keep this from curdling into its opposite:

- **Alignment, not enforcement.** The protocol couples selfish to social and makes harm legible; it never compels virtue. Enforcing "good" behaviour re-imports the central arbiter and the unoverridable constraint the rest of the design refuses. Make the good path the path of least resistance; make the harmful path visible; let external consequence (market, regulation, forking) act. The protocol accounts; it does not adjudicate.
- **Align only around structural, near-universal goods**: theft-resistance, longevity, honest accounting, interoperability. For contested values, the protocol witnesses and makes legible, and lets owners and the outside world judge. A protocol that encodes contested values is an arbiter, which is the tyranny failure mode.

A caveat in the same spirit: "the party that gains most" is not always measurable, and deciding it can itself become contested. The principle is a design heuristic for the specification's authors; where the protocol cannot know who gains most, it falls back to legibility. Record, don't adjudicate.

### Circumventability is a safety feature

Every mechanism in the specification (signatures, fencing, canaries, behavioural envelopes) raises the cost of casual, remote, and accidental failure, and every one is circumventable by a sufficiently capable, physically present actor. This is intended. An unbreakable constraint with ill-conceived parameters is its own catastrophe; it must always remain possible to turn Skynet off. So no software layer is the final safety authority. The stack terminates not in an ever-smarter check but in a dumb, physical, out-of-band override (an emergency stop, a manual disconnect, a fuse) that makes no decisions and therefore cannot be tricked into the wrong one, that the protocol neither mediates nor can disable, and that a physically present authorised actor can always reach. The emergency stop cannot be poisoned precisely because it verifies nothing.

The asymmetry is the safety property: a remote attack faces the full smart stack; physical presence can always override. A system that fights its own emergency stop has missed the point, so the protocol is designed to detect a legitimate override, yield to it gracefully, and log it, rather than resist it as an attack.

## Why discovery and authority are split

The split between discovered feature-capability and granted authority resolves a real tension. On one side, the upgrade story: adding a fourth motor module to a vehicle, or a new battery to a home system, should be "no software update, just discovery". On the other, safety during failure: nothing discovered should be able to walk into a certified control loop. The resolution: discovering the fourth motor is free; admitting it into the motion-control loop is a deliberate, non-discoverable, verifiable act. Hazard analysis attaches to the slot and its required interface, fixed at design time, so the identity filling the slot can change at runtime without reopening the safety case. Discovery proposes; binding disposes.

The reason ambient (presence-based) authority is named, ranked lowest, and distrusted by default is that it is the model systems fall into accidentally, and it fails catastrophically in the physical world. A car that trusts its internal bus because physical access is the entitlement means that smashing a window, plugging into the diagnostic port, and enrolling a new key is the system working as designed: presence was the grant, the thief obtained presence, the thief is "authorised". The networked version is the breached perimeter; the pre-zero-trust VPN failure. Presence may contribute evidence; it must never be the decision.

Ambient authority is legitimately sufficient only when two factors are both high: the difficulty of illegitimate presence, and the lowness of the stake. Applause qualifies: it is hard to fake being in the auditorium, and a wrongful clapper costs nothing. A car's diagnostic port fails the first factor; commanding torque fails the second.

One subtlety repays attention: the protocol constrains on declared and attested claims, never on real-world effects. A rule like "ambient authority may not command an actuator" sounds right and is unenforceable, because in an open-interface world the protocol cannot know what a capability does physically; an actuator driver can declare itself a status reporter. So the guard is placed where it can hold: ambient authority is valid only for capabilities declared and attested lowest-stake, and high-stake authority requires attestation to act. Under-claiming becomes self-defeating: declare low stake to dodge attestation and that capability genuinely gets only low-stake authority, so the high-stake action stays unreachable.

## Why attestation and exclusion are coupled

Attestation (a manufacturer's ability to require that parts prove themselves) and exclusion (its ability to refuse third-party parts) are two ends of one lever, and the specification makes them inseparable on purpose. To exclude a part by attestation, a system must cryptographically bind every part to an identity and reject parts that cannot prove themselves. That same binding is theft-resistance: a stolen or swapped part cannot attest into a system it was never enrolled in, so the smash-window-and-enrol attack stops working.

The framing is incentive, not finger-wagging. A manufacturer who insists on locking down is thereby required to deliver the socially good thing (hard-to-steal products) it otherwise has little incentive to build. A manufacturer who skips attestation forfeits in-protocol exclusion, and the aftermarket is open by default. The lazy path is the open path; the locked-down path is the secure path. What the coupling forbids is only the contradictory both-at-once that is today's default abuse: excluding competitors without securing the product. Every coherent position remains available, and every one is acceptable.

## Why there is no consortium

The obvious governance model for "who may attest" is a consortium that lists blessed attesters. It is rejected outright, because it is the single centralisation the whole architecture exists to avoid: the coordinator, the capturable point, and the party that orphans devices on its schedule rather than the owner's. It is also precisely why existing smart-home ecosystems cannot do the grandfather's axe: when the consortium or its cloud is gone, so is the device's standing.

In its place: anyone can attest, and anyone can require attestation. "I accept attestations from X" is a local, owner-held edge, not a global registry entry, so there is no central list to capture, by construction. Trust is a relationship, not a registry.

The headline consequence is that trust authority itself transfers by attested update. A bankrupt vendor's last act (or a court's, or a successor's) can attest a transfer of attestation authority to a community, and devices that trusted the vendor now trust the community by the same mechanism that always governed them. No special abandonment mode, no consortium re-listing. No consortium model can express "the manufacturer is dead, long live the community" without a central blessing; this can, because succession is an ordinary attested edge-rewrite.

The cost is named honestly: owner sovereignty relocates the attack surface onto the owner, who is socially engineerable in ways a defended chokepoint is not (the fake successor community after a bankruptcy; "install our helper to keep your device working"). The mitigations are mitigations, not cures: re-rooting trust must be conspicuous, reversible, and forensically logged, never silent; and the behavioural floor bounds what even a maliciously trusted attester can do at the actuator. The floor is what makes owner sovereignty safe against the owner's own mistakes, the same role it plays against poisoned updates.

## The incentive engine, applied

Three worked mechanisms show the engine doing its job:

- **Graceful exit as the path of least resistance.** Abandonment is the default today because disappearing is the cheapest act available to a dying company; graceful handoff costs effort nobody is incentivised to spend. The fix is to make attested transfer of trust authority a one-action, default, well-trodden end-of-life path, genuinely easier than switching off the servers. Then the lazy choice at wind-down is the responsible one. Nobody is forced to be a good citizen at death; good citizenship is simply made the route of least resistance. This is the mechanism that most directly delivers the axe: devices outlive vendors because the cheapest way to die is to hand off. Whether handoff can actually be made cheaper than disappearing is open question 24, and it is the one the incentive story stands or falls on.
- **Witness becomes settlement.** In shared-resource domains, money already flows for the social good: parties are paid to shed load, share capacity, and stabilise the grid. The forensic plane is already the accounting substrate: a tamper-evident, per-party-signed, owner-held record of who contributed what, when. That turns the witness into a settlement layer without the protocol becoming a market; the record is carried in-protocol, and the payment lives outside, on top. The selfish reason (getting paid) and the social good (grid stability) become inseparable byproducts of the same record.
- **Participation hardens the commons.** Every honest node adds attesters to cross-check, implementation diversity, and peers to quorum against. Named as a property, not leaned on as an incentive: positive externalities are under-provided precisely because the individual does not capture the collective benefit.

And two named traps the design refuses to build:

- **Reputation as a gate.** Owner-held attestation plus the forensic record make verifiable track records possible, but a required or central reputation score re-monopolises (incumbents accrue reputation new entrants cannot), invites gaming, and rebuilds the consortium by the back door. Reputation is admissible only as one owner-evaluable signal among many, never a gate.
- **The morality engine.** Aligning around contested values turns the protocol into an arbiter. The line is held: align around structural, near-universal goods; witness everything contested.

## The threat model: abandonment, obsolescence, poison

Three longevity threats, deliberately kept distinct because their defences are different, and a design that conflates them handles none:

- **Abandonment** is passive: the maker stops, nobody obstructs, the device orphans and bit-rots. The defence is openness. The definition commons outlives any vendor; content-addressed, signed definitions keep verifying with no origin server alive; and the open specification plus the open reference daemon are the ultimate abandonment insurance, because an openly specified protocol can always be continued. Proprietary undocumented protocols are what truly kill orphaned devices.
- **Obsolescence** is adversarial and external: the maker deliberately engineers the device to stop, often weaponising the very trust machinery (signed-firmware locks, attestation, cloud kill-switches) that protects against malware. The defence is owner sovereignty: the owner, not the manufacturer, is the ultimate root of trust for their own device, trust anchors are owner-re-rootable, and there is no vendor-only revocation of the owner's own grants. Local-first forecloses the most popular obsolescence lever structurally.
- **Poison** is adversarial and inside the trust boundary: a validly signed, correctly versioned update that is malicious or bricking, from a compromised or coerced publisher. Verification is defenceless here by construction; it checks provenance, not intent, and a correctly signed lie is still correctly signed. So poison is contained and recovered from, never prevented: canaried activation with automatic halt catches poison at the canary, because poison and incompetence fail the same way there; reversibility survives it; implementation diversity reduces the monoculture blast radius.

All three defences feed the axe. They are not threat-defence for its own sake; they are how a system keeps its identity and keeps working across total component churn, with no part and no vendor load-bearing for its life.

## Why declared failure semantics are the core

Survey the neighbouring systems and a pattern appears. Transport and publish-subscribe are well served (Zenoh, DDS). Identity is well served (SPIFFE, DIDs). Delegable authority is well served (UCAN, Keyhive). Declared behaviour on failure is served by nobody: every cyber-physical domain needs it, and each one that has it at all has hand-built it, vertically, inside its own stack.

Murmur makes it a first-class contract property. Every capability edge declares its safe state on loss of liveness; the heartbeat is a dead-man's switch that fires it; fencing at the resource ensures a deposed or returning component cannot act on stale authority. The mechanism is identical across wildly different stakes: the same declaration that releases a held MIDI note on a dropped Wi-Fi link is a freewheeling drive motor on a lost link, anti-islanding on a dropped inverter, and load-shedding on a datacenter coordinator loss. One contract, demonstrated on a keyboard, sized for a substation.

The design detail that carries the most weight: the safe state belongs to the role, not the device. An identical motor controller must freewheel in a drive slot (a held wheel on a lost link is uncommanded propulsion or single-wheel braking) and hold torque in a hoist slot (freewheeling drops the load). Making the safe state a property of the slot, armed at binding, means the device carries no knowledge of where it is installed, and the same part is safe in both places.

And the honest boundary: the protocol's job is fast, trustworthy detection plus a declared safe default. The response (redistributing torque across three live corners, re-deriving grid dispatch) belongs to the certified domain controller. Safety logic is never smuggled into the communication layer.

## Lessons borrowed from elsewhere

The specification leans on other systems' scar tissue. The load-bearing borrowings, and what each one taught:

- **RTP-MIDI's journal** taught the two-planes split: run the live stream lossy and low-latency, and recover loss by journaling, never by trading latency for ordered-reliable delivery.
- **Go modules** taught that decentralised identity needs a provenance-and-availability layer over it. URL-as-import was elegant and decentralised, and bare decentralisation produced vanishing sources, broken builds, and no trust signal, which Go had to retrofit with a module proxy and checksum database. The definition commons takes the lesson up front: self-certifying decentralised identity for definitions, with the cache, checksum, and attestation layer designed in rather than bolted on.
- **Kubernetes leader election** taught what not to copy. It looks easy because it cheats: it is a compare-and-swap lock on an already-consistent store. Local-first and partition-prone means no such store exists, so election degrades honestly: when a node cannot safely elect, it fails to the declared safe state it already has.
- **The fencing-token argument** (Kleppmann's stalled-leader case) supplies the load-bearing safety mechanism: a deposed leader that wakes and acts is made harmless at the resource, which rejects anything below the highest token it has seen. Split-brain becomes safe at the actuator even while election is ambiguous, which is the property actually needed, cheaper and stronger than global consensus.
- **Zero-trust networking** (the post-perimeter lesson) supplies the ambient-authority rule: location and reachability are signals, never grants.
- **The aviation security model** supplies transitive trust: a small set of named regime tiers, a trust floor carried with the payload and lowered by the weakest hop, and re-screening at the destination's discretion. Named tiers, not a continuous trust score, because a score is illegible and gameable.
- **PKI's revocation problem** supplies the grant lifecycle: offline-verifiable delegation and timely revocation are in fundamental tension, so in safety contexts short-lived grants that must be renewed beat long-lived grants that must be revoked. Expiry is a connectivity-free dead-man's switch.
- **Blockchain** is mined for primitives and refused as architecture: hash-linked logs (tamper-evidence without consensus), threshold signatures (one stable verification key over a churning committee), self-certifying identifiers. Global total-order consensus in a dispatch path is a category error; resource-side fencing gives a stronger local guarantee instantly.
- **libp2p** is the closest existing substrate (peer identity as key hash, modular transports, mDNS and DHT discovery, protocol negotiation) and is under evaluation as a base rather than a thing to reinvent (open question 11).

The deliberate posture throughout is compose, not replace. Zenoh, DDS, SPIFFE, DIDs, UCAN, Zigbee, Matter: every incumbent named in the specification is a potential host or component, not a competitor. The project admires them; the contract layer exists because no one of them spans the four concerns, not because any of them is wrong.

## The witness

The first demonstration is deliberately the smallest honest one: a Raspberry Pi with a MIDI controller, over Wi-Fi, to a Mac running `murmurd` presenting a virtual CoreMIDI source into MainStage. Discovery via mDNS/DNS-SD, with the service record bound to the public key so a spoofed name fails verification.

The build's job is not to beat RTP-MIDI at moving notes; existing tools already move MIDI over Wi-Fi. It is to witness the contract model on a latency case a musician judges instantly:

1. **Identity**: this keyboard is cryptographically this keyboard.
2. **Discovered versus bound**: the keyboard is discovered (interface satisfied) but silent until bound into the `keys-primary` slot; then notes flow.
3. **Authority, live**: revoke the grant and MainStage stops receiving, distinctly from a network failure.
4. **Failure**: pull the Wi-Fi mid-chord; the slot goes stale, the declared safe state fires (all notes off), and nothing sticks.
5. **Pool and contention**: a second identical-feature, distinct-identity keyboard contends for the slot (the four-motor case in miniature); the held-note ledger lives at the consuming endpoint, and promotion replays or patches the seam.
6. **Steward death**: kill the Mac and every slot fails safe, to clean silence. The honest demonstration of steward death; no transparent failover is pretended.
7. (Optional) **Fencing**: grants carry fencing tokens, and the virtual source drops a deposed keyboard's late packets: safety under split-brain, audible in seconds.

MIDI is a witness, not the reference domain. It occupies the easiest corner of every axis: single trusted steward, single owner, fully stream-observable state, soft real-time, failure that annoys rather than injures. Murmuration is sized for the hard ends: multi-party grid, certified drivetrain, hidden state, hard real-time, fatal failure. Every place the demonstration is easy is a place the specification must not generalise from, and the specification flags each one where it matters. Two examples of the discipline: the witness's state is fully reconstructible from the stream, which is the exception rather than the rule (most real capabilities carry hidden state, and that set forces member-side checkpointing); and the witness broadcasts its capabilities over mDNS, which is the ambient end of discovery visibility and demonstrates nothing about the confidential end.

## The ladder

Each rung of the demonstration ladder lights up one hard property the witness leaves dark, in the same cheap, instantly judgeable setting. Each doubles as a roadmap item, done when its corresponding open question closes. The two directions out of the easy corner are resilience under loss (something live goes away gracefully) and growth under addition (something new arrives gracefully); the same two motions reappear, unsafe and expensive, at the dangerous ends.

These rungs are an aspirational roadmap, not built. They are listed to show that the witness is the smallest slice of a planned progression.

| Rung | Demonstration | What it lights up | Open question it closes |
|------|---------------|-------------------|-------------------------|
| Today | The MIDI witness | the friendly baseline: the contract model is real | (baseline) |
| Next: loss | Roadie hot-swap: pull the active keyboard mid-performance; the sustained chord rides through the swap | redundancy pool, pre-warmed standby, consuming-endpoint state | 1, 4 |
| Next: growth | Expression-pedal hot-add: a different kind of device appears, is discovered, binds into a `mod-source` slot, and works, with no restart or update | growth by discovery; admission by interface satisfaction alone | 5 |
| Next: bidirection | Control surface with motorised faders: produces gestures, consumes feedback | per-edge direction; two ports, two safe states | 9 |
| Next: fan-out | Network MIDI clock to many slaved devices; pull the source | rootless failure: each subscriber fires its own local safe state, with no central death signal | 7 |
| Far: loss | Grid inverter or redundant IMU failover | loss where re-observation is impossible: hidden state, member-side checkpointing | 2, 4 |
| Far: growth | A new home battery joins a virtual power plant | growth across mutually distrusting principals; revocable delegation; multi-principal arbitration | 3, 6 |
| Far: physical, single-owner | Datacenter supervisory power and thermal coordination | the VPP pointed inward; safe state = shed; fencing at the device's own power floor | 12 |
| Far: physical, multi-tenant | Multi-tenant shared-resource coordination in a datacenter | shared physical constraints across customer trust boundaries | 2, 7, 12 |

The pedal rung is worth singling out: because the device is obviously not a keyboard, it makes the structural-typing claim concrete. It binds into `mod-source` because it satisfies that slot's required interface, full stop, not because of what kind of thing it is.

## The datacenter case

The AI datacenter appears on the ladder as a far rung, and its status is stated plainly: **unvalidated, pending diagnostic enquiry.** It is best understood not as a beachhead but as a proof that the model generalises, and as the densest concentration of the specification's hard open questions in one operational environment.

Where the model does not fit, and says so: the training hot path. Distributed training's collective operations (all-reduce over RDMA-class fabrics, sub-microsecond, bulk-synchronous, compile-time-static topology) are the most hostile possible environment for this design: no discovery, no negotiation, no latency budget for per-message identity or authority, and, decisively, no locally degradable safe mode, because a dropped rank kills the training step. The superficial resemblance to the drivetrain (many identical modules, one job) is a trap; it lacks the degradability the whole failure model depends on. That is someone else's data plane.

Where the model fits: the supervisory and physical planes, everything at millisecond pace or slower. Fault-tolerance supervision at scale (spare-node promotion is the redundancy pool, with the recovered state hidden, forcing checkpointing). Disaggregated inference fleets (live discovery, capability typing, and dynamic binding at a pace a control plane can breathe at). And the sleeper, the literal cyber-physical layer: power and thermal coordination, where per-node power-cap agents with declared envelopes operate under a rack or facility ceiling and fail safe by shedding, with fencing at each device's own power floor rejecting a deposed coordinator's stale instruction to draw more. A datacenter is a microgrid with starlings; the virtual-power-plant design already covers most of it, pointed inward.

One boundary must be drawn before any test (open question 12): power coordination splits into a fast regime (correlated load transients that can trip protection: real-time, firmware, hardware, not Murmur) and a supervisory regime (facility-wide envelope coordination, fail-safe: Murmur). Misplacing that boundary is either safety logic in the communication layer or a missed trip, so any trial belongs in the supervisory plane, well away from the trip path.

Whether a real gap exists at all, versus coverage by existing DCIM, hyperscaler-internal power management, and power-aware schedulers, is an empirical question, and "the gap isn't real" is a successful outcome of asking it: it would confirm the datacenter as a generality proof rather than a market.

## How to read the specification

The specification is written to be objected to. Its open questions section is not an appendix of loose ends; it is the working surface, and several of its entries (persistent system identity through total churn; owner re-rooting versus certification; the fast-versus-supervisory boundary; making graceful exit cheaper than disappearing) are the deepest design problems in the project. Where prose elsewhere touches one of them, it is presented as open and inviting objection, not as solved.

The model is deliberately maximal up to a named ceiling (specification, Section 18.1) and minimal in what the witness actually builds. The discipline for growth is fixed: new needs should arrive through the reserved seams (predicate subscriptions, the capability shape type, the steward-of-stewards recursion), not by reopening the spine.

The most useful contributions at this stage are objections to the open questions, field accounts from domains that feel the underlying pain, and demonstrations that extend the witness into a harder corner.
