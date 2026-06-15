# Ownership transfer and salvage (extension)

**Status: optional extension.** This extension deepens the device-lifecycle machinery of core Section 4.6. The core fixes the axioms: operability and ownership are orthogonal, identity is born on-device with two separated keys, the owner operates at the policy layer, ownership is held at the domain, the handoff path always has a valid target, and the three layers of bringing a part into a system MUST NOT collapse. This extension specifies the worked mechanics a base implementation needs only when it relays ownership through intermediaries, recovers a failed transfer, re-homes a salvaged part, or pins a part to one system.

Section references are to the core specification unless stated otherwise. Where this extension and the core appear to disagree, the core wins. The rationale is in the [primer](../primer.md#the-grandfathers-axe).

## The core hook

The core keeps the lifecycle axioms (Section 4.6) and the rule that physical presence buys only the one bootstrap claim, never authority to act. This extension adds propagation through intermediaries, the transfer failure modes and their layered recovery, retained-ownership legibility, the salvage claim window, the containment pole, and the compute floor. It adds requirements for implementations that use those mechanisms; it never weakens a core rule.

## Propagation through intermediaries

Subordinate devices with no uplink of their own receive owner-signed changes relayed through intermediaries. Acceptance is content-trusted and relay-agnostic: the subordinate verifies the owner's signature, never the relay's say-so. Trusting the relay would let a compromised intermediary hijack ownership of everything behind it (see Section 7.3). Propagation is eventually consistent; mixed states are safe in the interim.

## Transfer failure modes

A forgotten transfer, a deliberately retained root, and a dead vendor produce the same end state: the root is held by a non-current-owner who is not completing the handoff. Three layered defences:

1. **Legibility.** Ownership state is an inspectable declared fact, so an unfinished transfer is visible at the point of sale rather than discovered later.
2. **Proof-of-purchase recovery.** A path to complete a transfer after the fact from the buyer's side; ideally the claim voucher travels physically with the device.
3. **Forced physical re-commissioning.** A destructive last resort (factory-reset then claim), with theft-resistance from friction plus forensic logging. This floor guarantees the protocol never permanently locks out a legitimate owner.

Honest limit: root holder gone, no recovery oracle, and re-commissioning locked down leaves the buyer stuck. This is strictly better than today's invisible and unrecoverable locks, and not perfect.

## Retained ownership

The protocol cannot force a manufacturer to transfer ownership. On-device key generation at least prevents the manufacturer from holding the device identity key. Beyond that, the defence is legibility: "is this device genuinely owner-transferable" is a declared, attestable, inspectable property, so retained ownership is conspicuous and contestable by markets, regulators, and repair law, rather than buried.

## Salvage bootstrap

A salvaged part MUST be re-homeable by anyone with physical access: no vendor, no account, no app. A physical reset puts the part into a claimable state for a bounded window; it joins the domain of the first node to issue a deliberate claim in that window (pairing-mode shaped, never "the first packet on the air"). The reset MUST be physical (a jumper, a button held through power-on, a disassembly step), never a software command alone, and the part can always be reset again: the most recent physical possessor wins. A reset salvaged part still cannot attest into an attestation-gated system; theft-resistance lives at admission and attestation, not at the part.

## The containment pole

Some parts must refuse to operate anywhere but their authorized system (a safety interlock, a dosing controller, an immobilizer). This is the same machinery with the dials reversed: a grant naming one specific system, plus a declared safe state of "inert" when not bound into it. Absolute, permanent non-transferability is deliberately not offered at the protocol level; un-resettable binding is the same mechanism as brick-forever and is refused. Useless-if-removed, where required, is a hardware tamper response below the protocol. Permanence and exclusivity MUST themselves be declared, inspectable properties: legible non-fungibility is permitted and contestable; silent non-fungibility is forbidden.

## Compute floor

The above requires elliptic-curve verification and ideally a secure element. That is feasible on most modern microcontrollers, but it is a real floor: a truly trivial part with no secure element cannot participate.

## Open questions

This extension carries open question 28 (device lifecycle composition: the salvage claim-window mechanism and the reset-difficulty dial at both poles) and open question 29 (ownership transfer machinery: the bearer-versus-bound voucher trade, the re-commissioning difficulty dial, and recovery oracles). Those entries in the core specification carry the current state of each.
