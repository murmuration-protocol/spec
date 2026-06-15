# Updates: distribution, propagation, and activation (extension)

**Status: optional extension.** This extension deepens the update story of the core specification (Section 7.2). It is required only for implementations that distribute or update definitions in the field. A device that ships fixed definitions and never updates implements none of it: it needs only the core's rules that a definition is content-addressed and signed, and that a failed update leaves the device in its declared safe state.

Section references are to the core specification unless stated otherwise. Where this extension and the core appear to disagree, the core wins. The rationale, the worked canarying design, and the threat model are in the [primer](../primer.md#canarying-without-a-coordinator).

## The core hook

The core fixes the coupling that carries the longevity claim (Section 7.2): definitions verify with no origin server alive; an update that cannot be verified or completed leaves the device in its declared safe state; a breaking change is a semantic disconnection handled like a dropped link; activation keeps the old definition hot, so apply has an unapply; and there is no separate rollout-safety subsystem. This extension adds the distribution, propagation, and activation machinery an updating fleet needs. It adds requirements for implementations that update in the field; it never weakens a core rule.

## Distribution

Definitions are distributed, verified, and updated in the field, including on devices with intermittent, low-bandwidth connectivity. A system that discovers capabilities at runtime must also be able to learn and update what they mean without a full redeploy. Trust comes from what the artifact is, never from where it came from: verification is byte-identical whether a definition arrived from the commons, a private registry, a peer, or a USB stick.

- Two registry kinds are first-class. A **public commons**: an open, neutral, ungated registry of common definitions, stewarded rather than owned; this shared vocabulary is the one thing a no-coordinator system legitimately coordinates. And **private registries**: an operator's curated, access-controlled, audited registries for its own fleet.
- Verification and certification ride on the open commons as signed attestations layered over it, never as a gate on the vocabulary itself.
- Distribution is control-plane (Section 5), eventually consistent, tolerant of arbitrary disconnection; provenance is a hash-linked signed log (Section 11).

## Trust model

Trusting a received update decomposes into four distinct questions (the decomposition established by The Update Framework and carried into vehicles by Uptane), which implementations MUST NOT conflate:

1. **Integrity and authenticity**: is this what publisher P published? Content address plus signature.
2. **Authorization and provenance**: is P allowed to define this capability? Trust root, delegation chain, or attestation.
3. **Freshness and anti-rollback**: a malicious peer can serve a genuinely signed but stale, since-revoked definition. Devices MUST enforce monotonicity over the signed decision sequence, not over the artifact version: each activation decision carries a sequence number above the highest seen, and a device rejects any decision below it. This is the fencing token (Section 10) applied to definitions. An authorized reversal is therefore not a rollback in this sense: it is a new, higher-sequence decision that activates an older artifact (Activation, below), moving forward through decisions while moving backward through artifacts. Replay stays defeated, because a replayed stale artifact arrives with no new signed decision. Pair with expiry and gossiped signed revocations.
4. **Availability and eclipse**: peers can withhold but cannot forge. A node that cannot confirm currency within its declared window MUST degrade rather than trust indefinitely old definitions: fail safe on stale.

A peer relaying an update, even a peer bound to the same slot, confers zero authority on the content. Transport trust is never content trust.

## Fleet propagation and versioning

A fleet update is not a transaction that completes. Under intermittent connectivity it is a wavefront that may never finish, so mixed-version operation is the designed-for steady state.

- There is no coordinated global rollout sequence; one would assume a coordinator and a completion guarantee the architecture forbids.
- The contract carries an explicit **compatibility relation**: a v2 definition declares whether it is backward-compatible with v1 (open question 14). Compatible changes make any arrival order safe.
- Version is per-edge and per-binding, never per-device. A node bound into slots owned by different stewards may speak v1 on one binding and v2 on another.
- Design rule: **stewards tolerate a range; providers speak one version.** The steward population is smaller, more capable, and easier to update, so it absorbs compatibility; the larger provider population migrates lazily in any order behind that tolerance.
- A breaking incompatibility is a semantic disconnection: the binding goes stale and fires its declared safe state (Section 13), with the same machinery as a dropped link. There is no separate rollout-safety subsystem.

## Activation and canarying

Distribution and activation are separate. Distribution (getting verified bytes in place) is lazy, eventual, and peer-tolerant. Activation (switching the running contract) is a distinct, guarded event.

- Activation MUST be gradual and canaried with automatic halt, and nothing central stages it (fleet propagation, above): canarying is a discipline each node applies to itself. A node holds activation until it has accumulated evidence proportional to its declared stake; it counts only fresh attested silence, and only attested exposure of earlier waves, as that evidence, since silence it cannot verify as live, or silence from a population that never activated, is no evidence. A node that activates and trips its safe state publishes a signed distress report, or its steward does on its behalf when it dies unspoken, and that report halts further activation wherever it propagates. Widening is emergent, never a go signal from a rollout controller. The mechanics (wave derivation, the freeze-attack defence, the partition and isolated-system cases, and the substitute evidence where no lower-stake population exists) are developed in the primer and are open question 16. The mixed-version window is the blast-radius limiter, not a problem to eliminate.
- Synchronized fleet-wide activation is an anti-pattern wherever failure can be irreversible. It converts independent small risks into one correlated large risk, destroys mid-rollout observability, and is itself a physical hazard in shared systems (a thousand inverters hitting safe state at once is a grid event).
- Reversibility is first-class: the old definition stays resident and hot, so apply has an unapply. "Can this be rolled back" is a property of an update, not an afterthought. Updates with physically irreversible side effects are a named class requiring stronger gates (open question 17).
- An update is **routine** unless its publisher declares it **remedial** against a named defect. A routine update MAY be held indefinitely; the wavefront never finishing is the designed-for steady state (fleet propagation, above). Continuing on the current version is operationally safe by construction (the shipped safety case still holds, and a hold creates no new hazard) but not indefinitely secure once a remedial update exists, since exposure on the named defect accumulates with time. Remedial holds MUST therefore be bounded, with deadlines scaled to declared stake. The remedial claim is itself attestable and auditable, and making it raises the publisher's evidence burden rather than lowering it: the rush attack (every update declared an urgent fix) is the dual of the freeze attack, and both are claims to be made legible, never trusted outright.
- A capability MAY declare a readiness predicate that delays activation ("only when idle, between cycles"). For a routine update the predicate may hold as long as it likes; for a remedial update it is bounded by the same deadline as every other hold, because an unbounded hold on a fix is a denial-of-service vector: delaying for smoothness is fine, indefinite delay of a fix is worse than a capability-scoped safe-state trip. At expiry the node MUST NOT simply continue as if no clock had run: it activates if its evidence bar is met, and otherwise escalates by degrading the affected capability toward its own declared safe state, shedding high-stake authority first and function last, which bounds exposure without activating unvetted code. Escalation is per capability, never per system: the blast radius of a stuck update is the capability it is stuck on, and a system-wide response to one capability's stuck update is forbidden.
- **Reversal is not only automatic.** The canary halt has a manual sibling. An owner MAY sign a reversal across their domain, and a steward MAY sign one across its topic: ordinary scoped governance acts, expressed as forward decisions that activate the resident older definition (the trust model, above). Reversing a remedial update is within the owner's sovereignty but MUST be conspicuous and forensically logged; the re-accepted exposure becomes an attestable fact.
- **Supersession and the compromised publisher.** A publisher MAY supersede an in-flight update. Supersession propagates at the same priority as distress, and a node that never activated the superseded version skips it under the decision-sequence rule. Whether a superseding fix inherits accumulated evidence is open (questions 14, 16); fresh evidence is the default. A compromised publisher will not sign the cure, so reversal escalates through other authorities at their own scopes: canary halt, steward hold, owner reversal, and finally revocation of the publisher's authority itself through ordinary trust governance, the same attested-transfer machinery that handles a dead vendor (Sections 4.5, 4.6.5).

## Open questions

This extension carries open question 14 (the compatibility relation), open question 15 (OTA update mechanics for constrained, intermittently connected devices), open question 16 (coordinator-free canarying), and open question 17 (irreversible activations). Those entries in the core specification carry the current state of each.
