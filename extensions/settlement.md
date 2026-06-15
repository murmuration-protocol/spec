# Settlement and per-event attestation (extension)

**Status: optional extension.** This extension deepens Section 4.8 of the [core specification](../spec.md). It is required only for implementations of capabilities that gate on **per-event attestation**: multi-party settlement, conserved-value finality, and high-stake actions that need assent at the moment they are taken. The witness and the cyber-physical core do not use it, and an implementation that conforms to the core alone need not read it.

Section references are to the core specification unless stated otherwise. Where this extension and the core appear to disagree, the core wins. The rationale and a worked retail-settlement example are in the [primer](../primer.md#a-worked-quorum-settlement-over-ephemeral-nodes).

## The core hook

The core fixes two rules (Section 4.8). Per-event attestation MUST come from a decentralized authority, a quorum or a pool, never a single designated attester. And a capability that gates on it MUST declare a safe state for the case where assent cannot be obtained in time, and MUST take it rather than act unattested. This extension specifies the structure of that authority and the lifecycle of an attested action. It adds requirements for implementations that use per-event attestation; it never weakens a core rule.

## The authority is structured, not opaque

The attesting authority is structured, not opaque. An authority may be a single signer, a threshold quorum, or a delegation chain, and it is addressed as one in every case. The protocol's model of it is structured: a set of named member identities, a threshold, and, where members are not interchangeable, their roles. A threshold signature (Section 11) MAY transport a quorum's assent as a single object verifiable against a single key. That is the opaque case, and it is a degenerate configuration of the structured one, not a separate mechanism.

Structure is mandated rather than hidden because four properties are not expressible without it, and each is load-bearing in the protocol's harder domains:

- **Progress.** Under partition a node must reason about partial assent: how many of k have signed, who is missing, whether to wait, time out, or fail safe. An opaque threshold signature is binary and cannot express "in progress".
- **Attribution.** When a quorum-attested action is later found wrong, the forensic plane (Section 12) needs to know which members assented. Threshold signatures are designed to hide the individual signers, so opaque assent and attributable assent are in tension, and the attribution requirement forces the structured form wherever stakes demand it.
- **Heterogeneous roles.** "The sender and the receiver both assent" is not flat k-of-n; the members are required and non-interchangeable. This needs structure the protocol can see.
- **Membership change.** Quorum membership changes over time, and that change is itself an attested change the trust model must be able to reason about (Section 4.5). Membership hidden below the interface is invisible to it.

A verifier that needs only the fact of assent reads a structured attestation as one bit and never inspects its members. This preserves the legibility of low-stake domains, which run the degenerate single-signer or opaque-quorum case and touch no structure. A verifier that needs progress, attribution, or membership inspects the structure. The structure is present but ignorable. This is the pool pattern (Section 9) applied to authority: a quorum attester is a pool of attesters, exposed at the interface and ignorable, never erased below it. How much structure an implementation must carry before the legibility budget is breached is open question 31.

## Membership binds to durable principals

Quorum membership binds to a durable principal, never to a node. A seat in a quorum is a role bound to a stable identity, a bank or an institution or an owner, in the sense of Section 4.1. The node that presents a seat's assent need not be stable, and often is not. It holds a short-lived delegated grant to attest as the principal, rooted in the principal's key, and the verifier checks that the assent chains to the seat's bound identity and satisfies the seat's role. The presenting node's own identity is not part of the quorum. Churn is therefore handled by expiry, not by membership change: a vanished incumbent's grant lapses (Section 11), and the principal delegates afresh to whatever node is current, with no change to the quorum contract. A seat MAY itself be backed by a pool of such incumbents (Section 9). A quorum of stable principals then composes over fleets of ephemeral nodes: the seats are named and few, while the nodes behind each seat are many and replaceable.

## Standing and ephemeral quorums

A quorum's seats are filled in one of two ways, and the difference decides whether an inclusion steward exists at all. In a **standing** quorum the seats are enumerated ahead of time. A steward owns a contract naming the members, their roles, and the threshold, and that steward sits off the data path, consulted only when membership changes. In an **ephemeral** quorum the seats are bound at the moment of the transaction by the parties to it. A retail payment is the canonical case. The payer brings the payer's bank and the merchant brings the merchant's bank, and the pair forms a two-of-two quorum that exists for one transaction and never recurs in that exact form. An ephemeral pairwise quorum MUST NOT have a per-pair inclusion steward, because a standing party that authorized each pairing would be the central clearing house the architecture refuses.

For the ephemeral case the inclusion steward's role splits in two, and only one part is standing. The standing part is credentialing: an entity may hold a seat of a given kind only if it carries a per-property attestation to that effect (Sections 4.3, 4.5) from a regime the counterparty trusts, and there is no single such regime, by the no-consortium rule (Section 4.5). The per-transaction part is self-defining: each party binds its own seat by bringing the principal that rightfully represents its side, and the contract for this one-shot quorum is the transaction proposal the parties co-sign, not a list held by a third party. Legitimacy comes from the two composing. Neither party can seat an entity the credentialing regime has not vouched for, and neither can seat the other's side. The binding is the ordinary act of Section 4.1, performed late rather than ahead of time.

A standing scheme contract MAY still sit above an ephemeral quorum without becoming its steward. A payment scheme credentials its participants and fixes the dispute and settlement-finality rules, stewarded at the scheme level and off the data path. What it MUST NOT do is sit in the path of each transaction, or authorize each pairing. That distinction is the line between a rulebook and a clearing house (open question 25).

## The negative path: absence and dissent

Per-event attestation has a negative path, and absence and dissent are distinct events on it. Absence is a member that cannot be reached: the dead-man's switch fires and the capability takes its declared safe state. Dissent is a member that is reached and affirmatively declines, as a sending party with insufficient funds declines to attest. Dissent is information, not silence. It MUST be carried as a signed negative that propagates like a distress report (Section 12), never inferred from a timeout, and a node MUST distinguish the two: absence may be waited on or retried, while dissent is a decision. Whatever was staged in anticipation of assent is released by the negative path. A stage is a held resource whose declared safe state is release on loss of liveness or on signed refusal, the held note of Section 8.2 in another domain. The fencing token (Section 10) makes the release safe against a late assent: an assent arriving after a stage is released carries a token the resource has already superseded, and is rejected. Compensation for a refused multi-step action is the ordinary safe-state machinery, not a new mechanism.

## Stage, assent, commit, finality

Assent is not commit, and commit is not finality. A high-stake per-event action has a lifecycle the protocol carries requirements across but does not itself complete:

1. **Stage.** A held resource with a release safe state, as above.
2. **Assent.** The quorum agrees the action should commit. This is refusable and may be partial. It is not the commit.
3. **Commit.** A durable, idempotent write to the source of truth. The protocol requires that assent gate such a write; it does not provide the durability.
4. **Finality.** The durable, agreed, attributable record (Section 11). It lives in the source of truth the protocol defers to (Section 1), not in the protocol.

The source of truth resolves the uncertainty consensus cannot. When a confirmation is lost, with both parties having assented, the link dropped, and the outcome unknown, the resolution is a read against the source of truth keyed by a transaction identifier or fencing token, never a re-run of the quorum. The write MUST be idempotent so that the read-or-retry is safe. The protocol's role is to require that the gate terminates in a durable, idempotent commit and to witness the finality record. The durability, the ordering, and the truth of the balance remain the deferred authority's (Section 1). Outcomes that no read can undo are the irreversible-activation class (open question 17).

## Open questions

This extension is the live form of open question 25 (owner-held settlement without a central clearing house) and open question 31 (structured versus opaque attestation authority), and it interlocks with open questions 6, 17, and 29. Those entries in the core specification carry the current state of each.
