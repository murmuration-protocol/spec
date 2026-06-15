# Ownership transfer and salvage (extension)

**Status: optional extension.** This extension deepens the device-lifecycle machinery of core Section 4.6. The core fixes the axioms: operability and ownership are orthogonal, identity is born on-device with two separated keys, the owner operates at the policy layer, ownership is held at the domain, the handoff path always has a valid target, and the three layers of bringing a part into a system MUST NOT collapse. This extension specifies the worked mechanics a base implementation needs only when it relays ownership through intermediaries, recovers a failed transfer, re-homes a salvaged part, or pins a part to one system.

Section references are to the core specification unless stated otherwise. Where this extension and the core appear to disagree, the core wins. The rationale is in the [primer](../primer.md#the-grandfathers-axe).

## The core hook

The core keeps the lifecycle axioms (Section 4.6) and the rule that physical presence buys only the one bootstrap claim, never authority to act. This extension adds propagation through intermediaries, the transfer failure modes and their layered recovery, retained-ownership legibility, the salvage claim window, the containment pole, and the compute floor. It adds requirements for implementations that use those mechanisms; it never weakens a core rule.

## Propagation through intermediaries

Subordinate devices with no uplink of their own receive owner-signed changes relayed through intermediaries. Acceptance is content-trusted and relay-agnostic: the subordinate verifies the owner's signature, never the relay's say-so. Trusting the relay would let a compromised intermediary hijack ownership of everything behind it (see Section 7.2: transport trust is never content trust). Propagation is eventually consistent; mixed states are safe in the interim.

## Transfer failure modes

A forgotten transfer, a deliberately retained root, and a dead vendor produce the same end state: the root is held by a non-current-owner who is not completing the handoff. Three layered defences:

1. **Legibility.** Ownership state is an inspectable declared fact, so an unfinished transfer is visible at the point of sale rather than discovered later.
2. **Proof-of-purchase recovery.** A path to complete a transfer after the fact from the buyer's side; ideally the claim voucher travels physically with the device.
3. **Forced physical re-commissioning.** A destructive last resort (factory-reset then claim), with theft-resistance from friction plus forensic logging. This floor guarantees the protocol never permanently locks out a legitimate owner.

Honest limit: root holder gone, no recovery oracle, and re-commissioning locked down leaves the buyer stuck. This is strictly better than today's invisible and unrecoverable locks, and not perfect.

## Retained ownership

The protocol cannot force a manufacturer to transfer ownership, and it cannot verify how a device's identity was born. On-die key generation is the intended practice, but nothing in the protocol confirms it happened: a maker can inject a key generated elsewhere, or burn one static identity into every chip (the cheaper path, since identical chips cost less to produce), neither is visible in a single conformance sample, and a maker who never claims attestation is never asked. The cheap path is the non-compliant one, so the incentive engine does not align it on its own; the only structural pressure is the attestation-and-exclusion coupling (core Section 4.3), which forces per-device identity on exactly the makers who want to lock the aftermarket down. Where identity birth is assured at all, the assurance is a per-key attestation from the secure-element regime, not the maker's word.

Otherwise the defence is the usual one: legibility plus the floor. "Is this device genuinely owner-transferable" is a declared, attestable, inspectable property, so an escrowed or static identity is conspicuous to anyone who checks, and a self-asserted one is legibly self-asserted. The floor bounds the harm only partway: a held or cloned device key buys impersonation and cloning, never authority, because authority is the re-rootable owner root. So identity integrity and theft-resistance, unlike authority, are not fully cured, and rest on legibility plus the secure element's key non-exportability, which is an opt-in regime property the protocol never provides itself.

## Salvage bootstrap

A salvaged part MUST be re-homeable by anyone with physical access: no vendor, no account, no app. A physical reset puts the part into a claimable state for a bounded window; it joins the domain of the first node to issue a deliberate claim in that window (pairing-mode shaped, never "the first packet on the air"). The reset MUST be physical (a jumper, a button held through power-on, a disassembly step), never a software command alone, and the part can always be reset again: the most recent physical possessor wins. A reset salvaged part still cannot attest into an attestation-gated system; theft-resistance lives at admission and attestation, not at the part. The physical reset MUST also clear the part's binding and fencing state, the grants it held and any fencing high-water mark it tracked as a resource, so a salvaged part neither carries stale authority into its new home nor rejects its new authority's grants as stale (core Section 10).

## The containment pole

Some parts must refuse to operate anywhere but their authorized system (a safety interlock, a dosing controller, an immobilizer). This is the same machinery with the dials reversed: a grant naming one specific system, plus a declared safe state of "inert" when not bound into it. Absolute, permanent non-transferability is deliberately not offered at the protocol level; un-resettable binding is the same mechanism as brick-forever and is refused. Useless-if-removed, where required, is a hardware tamper response below the protocol. Permanence and exclusivity MUST themselves be declared, inspectable properties: legible non-fungibility is permitted and contestable; silent non-fungibility is forbidden.

## Compute floor

The above requires elliptic-curve verification and ideally a secure element. That is feasible on most modern microcontrollers, but it is a real floor: a truly trivial part with no secure element cannot participate.

## Open questions

This extension carries open question 28 (device lifecycle composition: the salvage claim-window mechanism and the reset-difficulty dial at both poles) and open question 29 (ownership transfer machinery: the bearer-versus-bound voucher trade, the re-commissioning difficulty dial, and recovery oracles). Those entries in the core specification carry the current state of each.
