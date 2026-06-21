# Forensic plane (extension)

**Status: optional extension.** This extension deepens the forensic plane of core Section 12. It is required only where stakes justify a tamper-evident audit record: a vehicle or grid system that must reconstruct events for liability or regulation. A synth rig, and most simple devices, run the recovery plane only and implement none of this.

Section references are to the core specification unless stated otherwise. Where this extension and the core appear to disagree, the core wins.

## The core hook

The core keeps the recovery plane and the principle that the protocol witnesses at the edge of its own authority (Section 12). This extension adds the forensic plane: the immutable, tamper-evident record that survives disputes, attached as an optional sink where stakes justify it. It adds requirements for implementations that attach a recorder; it never weakens a core rule.

## The forensic plane

The forensic plane and the recovery plane observe the same event stream and diverge in retention and integrity. Where recovery is mutable, ephemeral, and in the failover path, the forensic record is immutable, write-once, tamper-evident (a hash chain), and never in the control path. The same event enters both: recovery holds a note-on until its note-off and then forgets; forensics appends it, hash-linked, forever.

Per domain, the recorder is **passive** (logs what it observes; the default) or **active** (events must be durably logged before they may act; used only where regulation mandates write-before-act, with the cost noted below).

The forensic plane is where the protocol's attribution lives. A quorum-attested action's members (the settlement extension), a canary's distress report (the updates extension), and a capability's stake classification (Section 13.3) are all recorded here.

## What a log proves, and who keeps it

A logged entry is self-authenticating evidence, not the logger's testimony. The events a forensic plane records are already signed by their originators: a command by the keyholder, a grant by the steward, an attestation by the attester. Verifying the source of an entry is therefore verifying those signatures, the same check the live protocol performs, and a logger cannot fabricate content it holds no key to sign. The hash chain then proves the entry has not changed since it was written. Source authenticity and data integrity are both covered, and neither rests on trusting the logger.

What a single-writer log does not prove is **completeness**. The hash chain shows that what is in the log is intact; it cannot show that nothing was left out. A single logger can omit an inconvenient event, mis-order, or withhold the log entirely, and it is a single point of failure for availability. Signatures do not touch this, so who keeps the record matters, and it depends on the trust domain:

- **Within one trust domain** (a single-owner system), a single recorder is acceptable. It is the owner's own, there is no adversary inside to deceive, and its availability is a replication concern, not a trust one.
- **Across a trust boundary**, there is deliberately no single trusted logger. Each party keeps its own signed log, and the per-party logs cross-check: A's record of "I sent X to B" must match B's record of "I received X from A", so an omission or a re-ordering surfaces as a contradiction between two logs rather than hiding inside one. A forensic record that must be trusted across a trust boundary MUST NOT rest on a single writer; cross-checked per-party signed logs are preferred over a shared ledger.

The **active** recorder (write-before-act) is the sharp edge of this in the liveness dimension. Making durable logging a precondition of action turns the recorder into a liveness dependency, so it is used only where regulation demands write-before-act, and is made redundant there.

The honest residue is that no protocol can compel a party to log its own malfeasance. What the cross-check buys is detection: the counterparty's log contradicts the silence, turning a hidden omission into a visible dispute that the external authority (a court, a regulator, the source of truth) resolves. The forensic plane witnesses the discrepancy; it does not compel honesty, because compelling it would require the central trusted party the architecture refuses.

## Verifiable without a live service

A log that cannot be verified later is a backup, not recovery. A forensic record MUST be independently verifiable: every logged event MUST be checkable from the record alone, decades on, with no registry, certificate authority, or origin service still running. Self-certifying identity is what makes this affordable, because the signer's public key is recoverable from its identifier (Section 3), needing no external lookup.

For any logged event, the record MUST make the following resolvable:

- the signer's self-certifying identifier and the public key it certifies;
- the authority chain (the grant or delegation that permitted the action) as it stood at the time, terminating in a trust root the record anchors;
- the definition the event was typed by (content-addressed, Section 7.2);
- a sequence anchor placing the event against the validity of the above (the monotonic sequence fencing already uses, Section 10); an absolute timestamp MAY be added where a node has trustworthy time, but is never required.

These are **referenced, not duplicated**. An event carries content-addressed references (an identity is its self-certifying identifier, and a grant or a definition is content-addressed), and the record holds each referenced artifact once, deduplicated, in a keyed store the references resolve against, which MAY be a separate log. The same key signs thousands of events and the same grant authorizes many, so storing either per event would be absurd. The requirement is on the format's completeness, that everything referenced is resolvable within the record, never on per-event bloat.

Verifying "valid at the time" is done against the monotonic sequence, not a clock: the event's position in the issuing authority's sequence falls within the grant's validity, and fencing (Section 10) rejects anything a later decision superseded. The record therefore needs no synchronized wall-clock time, which a small, long-disconnected device cannot provide, and an absolute timestamp stays optional metadata. Two pieces stay genuinely open: trust roots move by attested transfer, so the record must anchor which root was in force when; and because the general identifier is rotation-surviving (question 11, resolved), the record must hold the slice of key-event history that makes an old signature verify against the key current then, which the durable-principal question deepens (open question 20).

## Open questions

This extension interlocks with open questions 6 and 25 (whether any domain needs agreement on shared history among distrusting parties), and, for the verifiability of an old record, question 11 (the identifier construction, now resolved as rotation-surviving, which decides whether key-event history must be held) and open question 20. Those entries in the core specification carry the current state of each.
