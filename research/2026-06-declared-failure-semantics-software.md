# Prior art: declared failure semantics in the software and agent domain

**Status: non-normative research note, June 2026.** This document backs the claim made in the primer's ["A second witness: pure software"](../primer.md#a-second-witness-pure-software) section. It is a due-diligence pass in kill-or-continue form, not a survey of the field for its own sake. Every system named here is treated as a potential host to compose over, never as a competitor; that posture is the project's, stated in the [README](../README.md), and it is genuine.

## The claim under test

The specification's headline claim is that declared, per-capability failure semantics are a column no neighbouring system provides. Within cyber-physical domains that claim has its own due-diligence pass ([companion note](2026-06-contract-seam-cyber-physical.md)). This note tests the narrower form the claim takes when it crosses into pure software:

> Within one runtime and one trust domain, declared failure behaviour exists (Erlang/OTP supervision trees; saga compensation). Nobody offers it as a portable contract property between mutually distrusting organisations, composed over the transports those organisations already use.

The test has four parts, and a counterexample must hit all four:

1. The failure behaviour is **declared in a machine-readable contract, per capability**, not hard-coded in an implementation.
2. It covers **loss of liveness**: the caller vanishes mid-operation, a lease expires, a link drops.
3. It is **enforced at the resource side**, with stale authority fenced on return.
4. It holds **across organisational trust boundaries**, between parties who do not trust each other's implementations.

The most valuable outcome of the exercise is a counterexample. One counterexample in kind was found; it narrows the claim rather than killing it (see the verdict).

## Method, honestly

This survey was AI-assisted: a fan-out of web searches, primary-source extraction into discrete claims, then an adversarial verification pass in which each claim faced independent attempts to refute it against the primary sources. The verification ran in two rounds in June 2026: an initial automated pass, then a second pass that completed the claims the first had not reached. Every claim below has now been checked against its primary source.

The adversarial pass earned its keep. It killed two claims that rested on an MCP proposal (SEP-1391) that was never merged. It refuted an early draft's assertion that WS-BusinessActivity "was not designed for cross-organisational use": the OASIS specification says the opposite. It corrected an over-stated claim that WS-era transaction identifiers were left unstandardised, when in fact they are typed and did interoperate across vendors. And it fixed a citation that attributed per-edge reliability typing to the wrong session-types research line. All these corrections are reflected below.

## Findings

### Agent protocols: MCP and A2A

**MCP (Model Context Protocol).** The capability negotiation surface declares which protocol features are available (tools, resources, prompts, sampling, logging). No capability object carries any field for failure semantics, safe states, lease behaviour, or compensation. Timeout handling is uniform SHOULD-level guidance to implementations, configured caller-side per request, never declared by the capability provider. Cancellation is advisory: receivers SHOULD stop processing and MAY ignore the notification outright, so there is no resource-side enforcement of any behaviour on caller loss. Session termination is delegated entirely to the transport, leaving the disposition of in-flight side effects unspecified.

The experimental Tasks mechanism (spec revision 2025-11-25) gives long-running tool calls durable handles with a lifecycle, and adds a per-tool declared property for asynchronous execution support. Two observations matter for this note. First, the polarity is the opposite of behaviour-on-silence: when the caller vanishes, the prescribed behaviour is that the task keeps running and the client later re-attaches. Nothing declares what a held resource does on silence. Second, the per-tool contract surface is demonstrably extensible, which makes MCP a natural host for a declared-failure-semantics binding rather than a system that already has one.

**A2A (Agent2Agent), v1.0.0.** Agent Cards are machine-readable capability declarations that already span organisations (OAuth2 and mTLS security schemes are first-class). They contain no field for per-skill failure semantics, timeout behaviour, safe state on disconnection, or compensation. Task cancellation is exclusively client-initiated and explicitly best-effort. The specification defines no lease, no heartbeat-driven cleanup, no fencing of stale authority on reconnection, and no compensation concept; the closest primitive is optional duplicate detection via message identifiers. A2A therefore has exactly the shape of a host: the cross-organisational contract surface exists, and the failure column on it is empty.

### The field's own self-description

A 2025 academic survey of the four main agent interoperability protocols (MCP, ACP, A2A, ANP; arXiv 2505.02279) compares them along eleven dimensions: architecture, discovery, identity and auth, message format, components, transport, session support, scope, use case, strengths, limitations. Failure semantics, liveness, leases, fencing, and compensation appear in none of them. The column is not merely empty in the protocols; it is absent from the axes the field uses to describe itself.

### Agent frameworks and the research frontier

SagaLLM (2025) is the closest recent agent-framework work: it applies the saga pattern to multi-agent LLM planning, pairing every forward operation with a compensating transaction. The compensation logic is generated by LLM agents at planning time and orchestrated by a coordinator agent, with a separate validation agent holding full visibility over all agent state. It is a single-trust-domain design, and its authors independently corroborate the gap this note tests: they observe that mainstream frameworks (LangGraph, AutoGen) lack atomicity, compensation, and failure-recovery guarantees altogether.

Session-types research is the one place failure behaviour genuinely lives in the contract. Asynchronous multiparty session types have been extended with explicit crash-handling branches in the protocol types themselves (Barwell, Hou, Yoshida, Zhou and related work): well-typed processes get deadlock-freedom and liveness guarantees by construction, even under crashes. A separate fault-tolerant line (Peters, Nestmann, Wagner) annotates every communication edge with a declared reliability level. The limits are equally clear: enforcement is compile-time, all participants are built from one type-checked toolchain, the trust model is cooperative (some roles are simply assumed reliable), the failure model is crash-stop only, and there is no resource-side fencing and no notion of a party that lies. This is declared failure semantics within one engineering domain, formally grounded, and it is the right literature for a future binding to lean on.

### Durable execution: Temporal and Restate

Temporal's saga support is developer-written compensation code, enforced caller-side and best-effort: if the workflow itself dies, compensations may never run. Temporal Nexus is contract-shaped (callers bind to named endpoints, not to workflow internals) and is the most instructive data point in this group: durable-execution vendors have hit the boundary problem and answered it at *team* scale. Nexus crosses namespaces within one Temporal deployment or cloud account; its failure behaviour (retries, backoff, circuit breaking) is uniform platform machinery, not per-capability declaration, and it does not extend to mutually distrusting parties. Restate makes compensation ordinary user code, with no declarative compensation DSL; for the resource-side half it recommends that downstream APIs expose reserve/confirm patterns, which is design advice to a developer, not a contract property. Both are plausible hosts for the within-domain rungs of an agent witness.

### Classic distributed systems

The lease-plus-fencing-token argument (Kleppmann's stalled-leader case) establishes the design rule this project already builds on: timeout-based authority is unsound without resource-side enforcement, because a paused client can act after its lease expired, so the resource must reject stale tokens. The published pattern is an implementation technique inside one deployment, between a lock service and a cooperating storage service. No portable, cross-organisational contract format for it exists; the specification's contribution is to make that mechanism a declared contract property, not to invent it.

### The WS-era attempt

The SOAP-era transaction standards are the closest historical attempt at this exact column, and their failure is instructive in detail.

WS-Coordination and WS-AtomicTransaction defined a machine-readable transaction context, carried in every message header, declaring a transaction identifier, a timeout, and a coordinator reference. A declared liveness deadline travelling inside a portable cross-party contract did exist in 2005. But the behaviour bound to it was uniform two-phase-commit abort, identical for every participant; nothing was per-capability. More telling: the one place the standards touched declared behaviour-on-silence was left out. Transaction "heuristics", what a participant unilaterally did while the coordinator was unreachable, were not standardised at all. WS-AtomicTransaction defines no heuristic outcome; its only consistency-failure fault is the single generic InconsistentInternalState, so distrusting parties could not machine-read what actually happened. The lower layers did interoperate: the transaction identifier was standardised as xsd:anyURI, and independent vendor stacks were tested against each other. What never arrived was the declared, per-capability failure column above that floor.

WS-BusinessActivity, the long-running compensation-based sibling, was designed to interoperate "across trust boundaries and different vendor implementations" (the OASIS specification's own words; an earlier draft of this note claimed otherwise and was corrected by the verification pass). What it did not do is declare the failure behaviour: compensation is application business logic, its ordering is explicitly left to the implementation, and behaviour on loss of connectivity to the coordinator is undefined.

The WS-era verdict for this note: the cross-organisational *intent* existed at the era's high-water mark, the per-capability declared failure column did not, and the wreckage argues for exactly the postures this specification already takes elsewhere: no required coordinator, semantics declared per edge, and identity that does not depend on agreement between implementations.

### The counterexample in kind: Lightning

The Lightning Network's BOLT specifications are the strongest known counterexample in kind, and they deserve to be stated at full strength. Behaviour on counterparty silence resolves without cooperation: once a node decides a peer is unresponsive, broadcasting the last signed commitment to force-close is a normative obligation. The threshold for declaring the peer unresponsive is left to the implementation, but the on-chain resolution that follows is not. The failure semantics are per-capability-instance: every in-flight conditional payment (HTLC) carries its own machine-readable deadline, and timed-out payments are resolved independently, with timeout-driven undo propagating hop by hop between channel peers as a normative obligation. Stale authority is fenced: a peer that broadcasts a revoked commitment is penalised via revocation keys, and the delay that makes this enforceable is negotiated per channel and enforced by script. Enforcement is resource-side, because every node watches the settlement substrate; it is trust-free only while a node stays online within that negotiated delay window. Reconnection assumes nothing: liveness loss is a first-class protocol state with a defined reconciliation handshake (channel_reestablish).

That is all four parts of the test, met, between mutually distrusting parties, in production for years. The narrowing is in what it took and what it covers. The domain is one capability (conditional payment) with one safe-state vocabulary (refund or settle, expressed in value). And the resource-side enforcement is bought by importing a global consensus substrate as the shared resource, the one architectural element the specification refuses for dispatch paths (specification, Section 14). Lightning proves the column is achievable across distrust; it does not provide it as a general-purpose, transport-composable contract layer.

## The column test, summarised

| Candidate | Declared in contract | Per capability | Resource-side, fenced | Across org distrust |
|---|---|---|---|---|
| MCP (incl. Tasks) | no | no | no | n/a |
| A2A v1.0 | no | no | no | contract surface yes, column no |
| LangGraph / AutoGen / SagaLLM | no (framework code) | no | no (coordinator) | no |
| Temporal / Nexus / Restate | no (user code) | no | no (caller-side, best-effort) | team scale only |
| Leases + fencing tokens | no (technique) | yes in effect | yes | no (one deployment) |
| WS-AT / WS-Coordination | partially (context + timeout) | no (uniform 2PC) | participant-side, heuristics unstandardised | intended, thin in practice |
| WS-BusinessActivity | no (compensation is app logic) | no | no | intended |
| Session types (crash-stop MPST) | yes (in the types) | per edge | no (compile-time) | no (one toolchain) |
| Lightning (BOLTs) | yes | yes (per HTLC) | yes (via global settlement substrate) | **yes** |

## Verdict

**Continue, repositioned narrower.** The defensible form of the claim, after this pass:

> No general-purpose, transport-composable contract layer makes declared, per-capability behaviour-on-silence a resource-side-enforced contract property between mutually distrusting organisations. The financial special case proves the pattern is achievable across distrust, at the price of a global settlement substrate and a one-capability safe-state vocabulary. The type-theory literature proves the declaration is expressible and checkable, within one cooperative toolchain. The general column remains empty, and the field's own comparison axes show it is not yet even a recognised dimension.

Hosts to compose over, should the primer's second witness ever be built: MCP (the per-tool contract surface is extensible; Tasks supplies a lifecycle to hang leases on), A2A (Agent Cards and extensions already cross organisations), and Temporal or Restate for the within-domain rungs. The session-types literature is the formal grounding to cite, the WS-TX history is the cautionary design input, and Lightning is the proof of feasibility and the measure of its cost.

What would change this verdict: a counterexample meeting all four parts of the test outside the payments domain, or evidence that one of the agent protocols has since grown a per-capability failure-semantics field. Both would be welcomed; an issue with a primary source is enough.

## Sources

Primary sources consulted by the survey and its verification pass:

- MCP specification, revisions 2025-06-18 and 2025-11-25 (lifecycle, cancellation utility, experimental Tasks): modelcontextprotocol.io/specification
- MCP proposals SEP-1391 (not merged; rejected in favour of SEP-1686 Tasks): github.com/modelcontextprotocol/modelcontextprotocol, issues 1391 and 1686
- A2A specification v1.0.0 and canonical protobuf definitions: a2a-protocol.org/latest/specification; github.com/a2aproject/A2A
- Survey of agent interoperability protocols (MCP, ACP, A2A, ANP): arXiv 2505.02279
- SagaLLM: transactional guarantees for multi-agent LLM planning (2025): arXiv
- OASIS WS-TX 1.1/1.2: WS-Coordination, WS-AtomicTransaction, WS-BusinessActivity: docs.oasis-open.org
- Wenzel, Freudenstein, Nussbaumer, "Strengths and weaknesses of WS-BusinessActivity for cross-organizational SOA applications", PESOS (ICSE workshop), 2009
- Kleppmann, "How to do distributed locking" (the fencing-token argument), 2016
- Lightning Network BOLT specifications (notably BOLTs 2, 3, and 5): github.com/lightning/bolts
- Temporal Nexus documentation and announcement; Temporal saga-pattern material: docs.temporal.io, temporal.io/blog
- Restate documentation (sagas guide, invocation management): docs.restate.dev
- Multiparty session types with crash-stop failures (Barwell, Hou, Yoshida, Zhou and related); fault-tolerant multiparty session types with per-edge reliability annotations; further trail: Carbone/Honda/Yoshida 2008, Viering et al. ESOP 2018, Neykova and Yoshida 2017, Adameit/Peters/Nestmann 2017
