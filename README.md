# Murmuration

**A common set of rules that lets connected physical devices recognise each other, agree on what each is and what it is allowed to do, and behave safely when any of them drop out, over whatever connection they already use.**

Connected physical devices (a synthesiser, the motors in a car, a home battery feeding the grid) all face the same few problems. They have to find each other, agree on what each is, decide what each is allowed to do, and behave safely when devices disappear. Today every device ecosystem solves this in its own incompatible way, and a device usually stops working the moment the company that made it stops supporting it. This is a specification for doing those four things (identity, capability, authority, and behaviour-on-failure) uniformly across every kind of device, on top of whatever connection the devices already use, so that a system keeps working as its parts, and the companies that made them, come and go.

Stated precisely, for readers who want the technical framing: a *local-first contract layer* for cyber-physical systems, covering identity, capability discovery, granted authority, and declared behaviour on failure, that composes over the transport, identity, and authority layers already in use rather than replacing them. Each of those terms is unpacked below.

> **Status: early exploration.** This repository is a specification and its rationale, not production software. A reference daemon (`murmurd`) is being built around a deliberately small first demonstration, the *witness* (below). The design has open questions, listed in the specification rather than hidden. This is not a 1.0; it is published at the point where it is still shapeable, and objections are the most useful contribution it can receive.

---

## Scope

The thing that generalises across a synthesiser, a drivetrain, and a power grid is not the wire; it is the **contract**. That contract is a protocol, **Murmur**; the self-coordinating whole it gives rise to is a **Murmuration**. Murmur specifies a contract model (identity, capability typing, granted authority, role binding, and declared failure semantics) and a small set of layering rules. It does not specify a transport, and it does not attempt to displace the domain-specific stacks that already own each domain: CAN-FD, TSN, and SOME-IP under ISO 26262; IEEE 2030.5, IEC 61850, and IEEE 1547 for grid and DER; CoreMIDI and RTP-MIDI for audio. It binds to them. Above it, the apps that register a device, the tools that manage a fleet, where keys are kept, and how ownership is transferred in practice are products built on top, which compete on experience and which Murmur does not specify. It is the ledger, not the bank.

The governing analogy is **POSIX, not Linux; IP, not Ethernet**: one abstract contract, many domain bindings. A corollary shapes the whole design: local-first is most necessary exactly where stakes are highest. Drivetrain motion control and grid anti-islanding must not depend on a cloud round-trip, so resilience and safety are derived from local reasoning and declared safe defaults, never from the reachability of a central authority.

A capability declares not only what it is but the non-functional conditions it needs to work: timing, ordering, reliability, liveness deadlines. These are matched when it binds, recorded when they are not met, and a breached timing or liveness guarantee is treated as a failure that fires the declared safe state. The protocol declares and witnesses such requirements; it does not itself provide hard real-time, which remains the certified domain controller's to guarantee.

## The four concerns

Murmuration treats four properties as orthogonal axes. Collapsing any two breaks the canonical case of four identical motor modules in one vehicle: same interface, distinct identities, non-interchangeable positions.

- **Identity: *who* is this.** A device is a public key. The identifier is self-certifying: it is, or derives from, the key, so there is no naming authority to spoof, and the identity is the same across any transport and any domain rather than an address issued by one ecosystem.
- **Feature-capability: *what kind of thing* is this.** Structural interface satisfaction, in the style of a Go interface or MIDI-CI. A device "is" a motor, an inverter, or a synth voice if it satisfies the declared interface. This is discovered, not granted.
- **Granted authority: *what it may do here.*** Whether a device may participate in a given function is a delegable, expirable grant, held separately from what kind of thing it is, and modelled on object-capability tokens. It is granted, never discovered. The split is deliberate: discovering a fourth motor module is free; admitting it into a certified motion-control loop is a deliberate, certifiable act. *Discovery proposes; binding disposes.*
- **Declared behaviour on failure: *what it does when the link drops.*** Every capability declares its safe state on loss of liveness, enforced at the actuator. A held note releases; a disconnected drive motor freewheels; an inverter stops feeding a dead line.

## The core: declared failure semantics

Declared, capability-specific failure behaviour is the property no neighbouring system provides, and the one every cyber-physical domain independently needs. It is a first-class contract property, not an operational afterthought: a heartbeat is a dead-man's switch that fires a declared safe state, and stale grants are fenced at the resource so that a deposed or returning component cannot act on old authority.

The mechanism is identical across wildly different stakes. The same declaration that releases a held MIDI note on a dropped Wi-Fi link is a freewheeling drive motor on a lost link, anti-islanding on a dropped inverter, and load-shed on a datacenter coordinator loss. One contract, demonstrated on a keyboard, sized for a substation.

The safe state belongs to the role, not the device. A single component can declare more than one, and which is armed is decided by the link it accepts, the role it is bound into: the same motor controller freewheels in a drive slot but holds torque in a winch. Each is just a named capability the device offers and a role requires, so the device need carry no knowledge of where it is installed.

The protocol's honest job is fast, trustworthy detection plus a declared safe default. The *response* itself (redistributing torque across three live corners, re-deriving grid dispatch) belongs to the certified domain controller. Safety logic is never smuggled into the communication layer.

## Relationship to existing systems

The most common first reaction is that this is another Zigbee. The distinction is precise. Zigbee is a vertical stack: a radio (IEEE 802.15.4), a mesh network layer, and an application layer in which devices interoperate by agreeing on *clusters*, shared definitions of what a device is. That last layer is the same core idea as Murmuration's capability typing, and Zigbee has shipped it in hundreds of millions of devices. The resemblance is real, but it concerns one layer of one stack.

Murmuration is not a stack; it is a contract. It defines no radio, network, or transport, and runs over Zigbee's radio, Wi-Fi, a wired bus, or a mesh equally. What it adds is what those stacks lack: identity that travels across transports and domains; authority that is granted and revocable, held separately from device type; declared behaviour on failure; one contract across domains rather than one consortium per ecosystem; and the owner, rather than the manufacturer, as the ultimate root of trust.

Each neighbouring system owns one or two of these concerns. None owns the contract that spans them, and none declares behaviour on failure:

| | Transport / pub-sub | Identity | Authority (delegable, revocable) | Secure update dissemination | Declared failure semantics |
|---|---|---|---|---|---|
| Best-in-class today | Zenoh, DDS | SPIFFE, DIDs | UCAN, Keyhive | TUF, Uptane | *none* |

Murmuration is designed to **compose with these, not replace them**. Transport can be Zenoh, DDS, or raw UDP; authority can be UCAN-style tokens; identity can be SPIFFE or a DID; update verification adopts the discipline TUF established and Uptane carries into vehicles. The protocol declares the contract; the substrates move the bytes and sign the keys. Because there is no clear winner among transports, identity layers, or authority schemes (and there may never be), a layer that composes over all of them treats that fragmentation as an advantage: every existing deployment is a potential host rather than a competitor to displace, and adoption adds a contract layer rather than ripping anything out.

## Longevity and ownership

The success criterion is the **grandfather's axe**: an axe that has had three new heads and four new handles is the same axe. A system retains its identity and keeps functioning across the complete replacement, several times over, of every physical component. No single part, and no absent vendor, is load-bearing for its continued life. A home battery, inverter, and grid connection keep working after every component has been swapped several times and possibly after every company that made them has gone.

This is the murmuration in the name: a flock remains itself while every starling in it is replaced. No bird coordinates the whole; coherence arises from local rules. That is also why nothing critical depends on a server that can be switched off.

Two mechanisms make this concrete. The **owner, not the manufacturer, is the ultimate root of trust** for their own device. And **trust authority is transferable by attested update**: a dying vendor's last act can attest a transfer of authority to the owners, or to a community or successor, so devices that trusted the vendor now trust the new authority by the same mechanism that always governed them, with no special abandonment mode and no consortium to re-list. Authority itself becomes a replaceable component.

Grounded in the physical world, this is the salvage case: a component pulled from a breaker's yard can be reset by hand and adopted into a new system by whoever now holds it, with no manufacturer, account, or computer in the loop, and it can always be reset again, so physical possession stays the final authority. Owning a salvaged part is not the same as admitting it into a safety-critical role, which remains a deliberate, attested step, so repairability and safety are not traded against one another.

The same continuity test applies to software. A device that outlives its maker must keep receiving definitions and security fixes safely for decades, so update dissemination is core machinery rather than vendor plumbing. Definitions are content-addressed and signed: they verify identically whether they arrive from an open commons, a private registry, a peer, or a USB stick, with no origin server alive. And there is no separate rollout-safety subsystem. An update that cannot be verified or completed leaves the device in its declared safe state; activation is gradual, canaried, and reversible by design; a breaking change is handled as a semantic disconnection by the same machinery as a dropped link. The hard mechanics (the compatibility relation, delivery to constrained and intermittently connected devices, canarying without a coordinator, updates with physically irreversible effects) are named open questions in the specification, worked in the open rather than left to each vendor to rediscover.

The promise here is continuity for the owner, not a stance against the manufacturer. Longevity and interoperability are properties a manufacturer can build on and sell. Friction arises only with business models that depend on the opposite of longevity, and that friction is a side effect of keeping the promise to the owner, not its purpose.

## The witness

The first demonstration is deliberately the smallest honest one: a MIDI keyboard over Wi-Fi to a Mac running MainStage, through `murmurd`. It occupies the easiest corner of every hard problem (single owner, single steward, fully observable state, soft real-time, annoyance-not-injury failure), with a verdict the human ear is very good at identifying.

A device is discovered but not yet bound. It is bound, and notes flow. Its authority is revoked, and the notes stop. The Wi-Fi is pulled mid-chord and nothing sticks, because the capability declared its safe state. A second keyboard takes over without dropping the held chord. The build's purpose is not to move MIDI better than existing tools already do; it is to make the *contract model* legible on a latency case judged instantly. Declared behaviour on failure, made audible in a few minutes, is the whole thesis, and every place the demonstration is easy is a place the real design is not. The specification says so, and marks each one.

## Principles

**Legibility is a longevity requirement, not an aesthetic.** A mechanism that only its original author can understand or repair is already abandoned. A carburettor or a vacuum-advance still works decades on because a competent stranger can open it, understand it, and repair it with ordinary tools. Legibility trades against capability (fuel injection genuinely beats a carburettor), so the trade is made deliberately rather than by reflex, and "could a competent stranger reimplement this from the specification alone, decades from now" is treated as a requirement.

**No software layer is the final safety authority.** Every check in the protocol (signatures, fencing, canaried activation, behavioural envelopes) raises the cost of casual, remote, and accidental failure, and every one is circumventable by a sufficiently motivated actor. This is intended: an unbreakable constraint with ill-conceived parameters is its own catastrophe. The stack therefore terminates not in an ever-smarter check but in a dumb, physical, out-of-band override (an E-stop, a manual disconnect, a fuse) that makes no decisions, that the protocol neither mediates nor can disable, and that a physically present authorised actor can always reach.

**Incentive alignment over enforcement.** Most of the design is one idea: the burden falls on the party that gains the most from a decision, so that the selfish choice and the social good converge. A manufacturer that insists on locking parts down is thereby required to build a real security fabric, which is also what makes the product theft-resistant; an owner who gains autonomy bears the trust decision. The protocol couples selfish to social and makes harm legible; it does not compel virtue. It aligns around structural, near-universal goods (theft-resistance, longevity, honest accounting, interoperability), and for contested values it witnesses and records rather than adjudicating.

## Names

- **Murmuration** is the system: the emergent whole that no node coordinates.
- **Murmur** is the protocol: the local rules each node speaks to its neighbours.
- **`murmurd`** is the reference daemon that speaks Murmur.

The lineage is MANET and swarm robotics (decentralised, no required infrastructure, no central ground), but Murmur is a contract layer above the network, not a routing protocol.

## Contributing

The specification ([spec.md](spec.md)) and its rationale ([primer.md](primer.md)) live alongside this README, with the open questions stated honestly in the specification. The most useful contributions at this stage are objections to those open questions, field accounts from domains that feel the underlying pain (embedded fleets, shared physical resources, updates that cascaded into failure), and demonstrations that extend the witness into a harder corner.

This specification was drafted with heavy use of AI; the intent behind it is the author's. Contributors are sought to refine both.

---

*Early-stage and openly specified, under the Apache License 2.0. Designed to compose with, not replace, the systems it names.*
