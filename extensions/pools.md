# Pools, handoff, and steward failover (extension)

**Status: optional extension.** This extension deepens the pool and steward-failover machinery of the core specification (the section on pools and steward failure). The core fixes the degenerate case (a single binding is a capacity-1 pool with no promotion), the fail-safe steward default, and the rootless fencing rule. This extension specifies what a base implementation needs only when it uses multi-member pools, promotion and failover, stateful handoff, or a steward that fails over rather than fails safe.

Section references are to the core specification unless stated otherwise. Where this extension and the core appear to disagree, the core wins. The rationale is in the [primer](../primer.md).

## The core hook

The core commits to the pool *structure* (a pool is slot-shaped from the outside, and a single binding is its degenerate case) without committing to any single failover semantics. It also fixes two rules a base implementation always obeys: a steward may fail safe rather than fail over, and a rootless topic MUST fence at every actuator and declare its quorum rule. This extension adds the redundancy pool, the candidate state machine, state projection and handoff, and the pool-backed virtual steward. It adds requirements for implementations that use those features; it never weakens a core rule.

## Multiplicity and redundancy

A **pool** is an optional construct usable anywhere a single slot is. It is slot-shaped from the outside (same required interface, presents one winner), so a singleton slot can be upgraded to a pool-backed one without the steward changing anything.

Two patterns the word MUST NOT conflate:

- **Multiplicity slot**: capacity above one, all members active at once (four wheel slots, each capacity-1). Failure means the slot goes unfilled and the steward redistributes; there is no slot-level failover.
- **Redundancy pool**: one active member plus warm standbys; failover is promotion (two keyboards contending for one role; redundant IMUs; an aggregator choosing among inverters).

Model:

- A single binding is the degenerate pool: capacity 1, promotion policy none. The structure is committed to; no single failover semantics is.
- Candidate states: `eligible` (discovered, satisfies the interface, not admitted), `admitted-standby` (pre-granted, live heartbeat, idle), `active`, `stale`.
- Promotion policy is a pluggable slot-level declaration, the same shape as transport properties and election policy.
- The data interface stays transparent through the virtual winner, but the control interface MUST emit promotion as an event: degradation reasoning depends on knowing what is currently live.

A pool presents one capability while internally orchestrating many; this is capability composition, with the pool as the degenerate case where all sub-members satisfy the same interface. A composing node is a steward downward (to its members) and a producer or consumer upward (to its own steward) at once. Heterogeneous composition, where sub-members satisfy different interfaces, is recognized but deliberately out of model (Section 15.1).

## State projection and handoff

Stateful capabilities make pure selection insufficient: a freshly promoted standby that does not know a note is held produces stuck or dropped notes.

- **State projection belongs at the consuming endpoint.** The node already receiving the winner's stream maintains "what is currently live" as a side effect of consumption. On promotion it replays resume-state into the new winner, or patches the seam itself (emitting the releases the new source cannot know to send).
- **Recover from observation, not replication**, wherever the state is fully observable from the consumed stream. This adds no new failure mode; the consuming endpoint is already the liveness anchor for that edge.
- Full stream-observability is the exception, not the rule. Most real capabilities carry hidden state (a sensor's internal calibration, an inverter's charge model, and the steward's own ledger). **That set, and only that set, requires member-side checkpointing or replication.** Identifying it per domain is open question 4.
- In a fan-out or rootless topic, each subscriber projects independently; there is no single consuming endpoint.
- Per slot, standbys are **pre-admitted** (keys exchanged and grant issued, so promotion pays no authorization handshake; always do this) and optionally **pre-warmed** (already receiving a shadow of the projection, making the switch sub-perceptual; a continuous cost, paid only where the slot warrants it).

## The pool-backed virtual steward

A pool is a logical principal, not necessarily a physical node; its logic is co-located at the steward boundary. A free-standing pool component is a single point of failure holding the very state the pool exists to protect.

The recursion bottoms out. Pools and topics close under composition (a pool of pools, a steward of stewards), but there is always a root steward whose liveness is the trust anchor, made reliable by other means than another pool. There is deliberately no coordinator-of-the-whole to promote anything into.

Failing over a steward is categorically harder than failing over a member: the steward holds authoritative state (the ledger), is the trust root issuing grants, and is what producers are pointed at. Two honest options, chosen per capability:

- **Fail safe (harden a singular root).** The steward does not fail over; it fails safe. On steward death every slot goes stale from the top and fires its declared safe state. For most safety-critical stewards this is the correct, certifiable answer; in a vehicle, the motion controller is an internally redundant certified component, not something failed over by a discovery protocol. This is the core default.
- **Pool-backed virtual steward identity.** The steward becomes a slot backed by candidate stewards presenting one stable virtual identity, so producers do not re-point on switch. Costs: the steward's ledger becomes unobservable hidden state and MUST be replicated or checkpointed (the state projection above), and the virtual identity needs a real threshold credential (Section 11). Reserved for availability-critical stewards.

## Open questions

This extension carries open questions 1 (slot capacity and failover shape), 2 (which stewards must survive death), 4 (which capabilities have hidden state), and 5 (automatic-within-envelope versus re-consent on promotion). Those entries in the core specification carry the current state of each.
