# Prior art: the contract seam in cyber-physical systems

**Status: non-normative research note, June 2026.** This document backs the claims made in the README's ["Relationship to existing systems"](../README.md#relationship-to-existing-systems) and the primer's ["Why declared failure semantics are the core"](../primer.md#why-declared-failure-semantics-are-the-core). It is a due-diligence pass in kill-or-continue form. Every system named is one the project admires and intends to compose over; where this note records a limitation, the source is in each case the system's own maintainers or published literature, not this project's opinion.

A companion note covers the same question for the pure-software and agent domain: [declared failure semantics in the software and agent domain](2026-06-declared-failure-semantics-software.md).

## The claims under test

Two claims, tested by actively searching for the project that already does this and would make this one unnecessary:

1. **Declared, capability-specific failure semantics** (safe state on loss of liveness as a first-class contract property, fenced at the resource) is a column no neighbouring system provides.
2. **The unification itself** (identity, capability typing, granted authority, and failure semantics in one local-first, transport-agnostic contract) has no owner: each neighbour holds two or three of the columns, none holds the contract that spans them.

A killer would be a single project occupying both. The most valuable outcome of the exercise is finding one.

## Method, honestly

This was an active kill-search across four neighbour clusters: industrial and robotics buses; capability and identity security; datacenter and cloud-native; local-first and CRDT systems. It was AI-assisted and run in June 2026. Each claim was then put through an adversarial verification pass, in which an independent agent tried to refute it against the primary source. That pass corrected several details, noted inline where it matters. The most consequential correction is that Matter, unlike Zigbee, does cross transports and administrative domains. The areas known to move fast are still flagged, because they will move again. The original exercise also assessed standards-body mechanics; that is project strategy rather than prior art, and is not republished here.

## Findings

### The strongest neighbour: Zenoh

If any single project killed this one, it would be Eclipse Zenoh. Its stated aim, one protocol from microcontroller to datacenter with no brokers and no topology constraints, is close to this project's own pitch, and it is real: a production Rust implementation, single-digit-byte wire overhead (4 to 6 bytes), a microcontroller build that has run in the low hundreds of bytes on its embedded target, ROS 2 integration via `rmw_zenoh`, and a peer-to-peer topology that can run with no single point of failure (a brokered router mode is also available). It unifies publish-subscribe, query, and storage.

Where it stops is precisely where this specification lives, and Zenoh's own maintainers say so:

- Authorisation is static, per-node ACLs. A Zenoh feature request (eclipse-zenoh/zenoh #1432, "Add trust-based authorization", now closed but unimplemented as of the 1.8.x release) observes that ACLs based on username or certificate common name do "not seem to scale well for larger and dynamic environments", with a drone swarm in which every vehicle must be authorised to join as the example: exactly the discovery-then-admission case. ACL configuration still cannot be updated at runtime; a change requires an instance restart.
- There is no capability-as-interface typing. Routing is by hierarchical key expression; nothing expresses "a thing that satisfies this interface".
- Identity is the TLS certificate common name. There is no self-certifying public-key identity and no delegation.
- There are no declared failure semantics. Zenoh provides connectivity and liveness primitives; no contract states what a capability does on link loss.
- End-to-end payload encryption is a noted limitation, left to the application (census-labs security analysis, 2025).

The reading this note settled on: Zenoh is a superb data plane, arguably the best candidate substrate for the transport binding (specification, Section 6), and it is not a contract, identity, authority, or failure layer. "Murmur over Zenoh" is a coherent story, and Zenoh moves from killer to leading potential host.

### Industrial and robotics buses: DDS, ROS 2, OPC-UA

DDS under ROS 2 is the incumbent cyber-physical data bus, with discovery, QoS, and a security layer (DDS-Security, SROS2). The published security literature has independently named the problems this specification targets. Deng et al. ("On the (In)Security of Secure ROS2", ACM CCS 2022) document four design vulnerabilities, three of them stated to be independent of the underlying protocol: a permission-replacement and refused-restart attack by which a compromised node retains access after its certificate is revoked (the expiry-beats-revocation argument of specification Section 14, arrived at from the other direction); an outdated-node-service failure whose suggested mitigation, that all participants leave and rejoin on a policy update, underlines the absence of clean dynamic admission; and a default mis-configuration that leaks topology to passive listeners (the concern behind specification Section 4.7). The authors' certificate-revocation mitigation has since been merged into ROS 2 rolling, but the dynamic-permission gap remains structural. A 2024 review criticises SROS2's access control for rigidity and poor dynamic permission management in multi-robot environments. OPC-UA is an industrial information-modelling standard, heavyweight and client-server shaped (a later publish-subscribe mode exists): adjacent, not a unifying local-first contract layer.

The reading: strong corroboration of need. The robotics world has the data plane, and its authority story's limitations are documented in its own literature, at the design level rather than the implementation level.

### Identity and authority: SPIFFE, UCAN, DIDs, Keyhive

**SPIFFE/SPIRE** is the workload-identity standard (CNCF graduated, 2022) and validates one of this specification's stances directly: because its certificates are short-lived, traditional revocation is usually unnecessary. It is identity only, by deliberate scope; it is centralised (the SPIRE server signs) and shaped for datacenters with reliable connectivity to that server. The boundary is clean: SPIFFE answers "who", and does not attempt "what kind", "may it act here", or "what happens on failure".

**UCAN** is the closest existing model to this specification's authority axis: trustless, local-first, offline-verifiable, delegable capabilities with expiry, on public-key identity, at v1.0.0-rc.1. It even lists time-limited device control among its use cases. It is authorisation only: no discovery, no capability typing, no failure semantics, no role binding. Its own community notes that capability-model adoption still needs education.

**Keyhive** (Ink & Switch, by the researcher behind UCAN) is the closest research neighbour: local-first access control with capabilities and end-to-end encryption, including revocation, done by serious people. Decisively for this note, its authors deliberately exclude identity ("leave name registration/discovery and user verification to a future layer") and discovery, and scope it to local-first collaborative applications, with documents as the concrete domain: no transport contract, no real-time concerns, no declared failure semantics, no role binding. The single most reassuring finding of the whole exercise is that the best people in the local-first authority space drew their boundary exactly where this specification begins.

**DIDs** are the self-certifying identifier substrate several of these build on; maturity varies by method and should be confirmed per method before depending on one.

### The production proof of capability typing: Zigbee, ZCL, and Matter

The strongest "the model works" evidence in the field is also not a killer. The Zigbee Cluster Library is capability-as-interface in production at the scale of hundreds of millions of devices over two decades: a cluster is a capability definition, a device advertises which clusters it supports, and devices interoperate by agreeing on cluster semantics at join. Matter inherited the cluster data model and added public-key device attestation and commissioning. This is the specification's feature-capability axis (Section 3), shipped, and it validates the central design bet.

What Zigbee itself does not have: a self-certifying identity that travels across domains, delegable and revocable authority, declared failure semantics, or transport generality. Two of those limitations soften for Matter and must be scoped with care. Matter is multi-transport (Wi-Fi, Ethernet, and Thread, not one radio), and its multi-fabric model lets a device hold operational credentials in more than one administrative domain at once. What neither Zigbee nor Matter has is delegable, revocable, user-held authority or declared per-capability failure semantics; both of those columns stay empty, and the cluster registry stays consortium-governed (CSA). One boundary note matters for any future binding: only the lower half of the Zigbee stack (802.15.4, optionally its mesh layer) is usable as a Murmur transport. ZCL is a capability layer of its own, so "Murmur over Zigbee" means over the radio, never over ZCL. The ZCL semantics did later migrate to IP as Dotdot, which became Matter's data model, but that is a competing capability layer, not a transport. The CSA's positioning of Zigbee, Matter, and Thread keeps shifting, so any description should be checked against the live state rather than a fixed snapshot.

### Datacenter power coordination

The datacenter findings validated the primer's most tentative thread (the datacenter case, gated by open questions 12 and 13) more strongly than expected:

- LLM training nearly fully utilises provisioned power and produces large swings; power capping is the accepted mitigation (Microsoft POLCA, ASPLOS 2024; DynamoLLM; power-stabilisation work, 2025). Training headroom is a few percent, inference substantially more. This confirms the split the primer draws: the training hot path is not this protocol's, and supervisory power coordination plausibly is.
- The fast-versus-supervisory boundary (open question 12) is real and now has a number: rack-level throttling must act in under roughly 15 ms (US patent 12,560,987), which is hardware and firmware territory, while facility-level capping is slower and software-managed.
- Battery-to-GPU coordination needs close state-of-charge coordination, identified as a co-design requirement in the 2025 engineering literature though not yet a named protocol primitive: a concrete instance of the envelope and telemetry contract (specification, Section 7).
- Grid-interactive datacenters have been field-demonstrated (Phoenix, 2025), using a proprietary grid-signal interface, and the demonstration's authors call standardisation an open problem. The Open Compute Project is the venue actively pursuing open datacenter power and telemetry standards, on the explicit framing that no single vendor or hyperscaler can solve it alone.
- The incumbents (POLCA, DynamoLLM, vendor power controls) are hardware- and firmware-level point solutions. No coordination-layer standard with identity, envelopes, and fail-safe semantics exists across multi-tenant trust boundaries.

This cluster moves fast; the specific "unsolved" claims should be re-verified before being relied on anywhere that matters.

### Local-first and CRDTs

CRDT infrastructure matured into a tailwind rather than a competitor: Automerge has had a production Rust core since 2.0 (2023), and version 3.0 (2025) cut its memory use by more than tenfold, so the state-convergence machinery a control plane needs is now reusable rather than research. The adoption reality cuts the other way: local-first software remains intellectually ascendant but early in uptake, which calibrates expectations for any adoption curve this project hopes for.

## The column test, summarised

Strength of each neighbour against the columns this specification claims to unify. "Strong" marks the systems this project would compose over for that column.

| | Identity | Capability typing | Granted authority | Discovery | Declared failure semantics | Local-first, rootless | Cross-domain |
|---|---|---|---|---|---|---|---|
| Zenoh | weak (cert CN) | no | no (static ACLs) | yes | no | yes | yes |
| DDS / ROS 2 | yes (certs) | partial | no | yes | no | partial | no |
| SPIFFE/SPIRE | strong | no | no | no | no | no (central signer) | no (cloud) |
| UCAN | via DIDs | no | strong | no | no | strong | partial |
| Keyhive | excluded by design | partial | strong | excluded by design | no | strong | no (documents) |
| Matter | yes | yes (clusters) | partial | yes | partial (commissioning) | partial | no (home) |
| Zigbee/ZCL | partial | strong, at scale | no | yes | no | partial (mesh) | no (one radio) |
| Dapr | partial | partial | no | yes (cloud) | no | no | no |

The failure-semantics column is empty for every row, and no row is filled across. The specification's claim is the missing row, and it is a claim, not an achievement.

## The case against

The honest risks, none of which the exercise found to be a kill:

1. **Unifying abstractions are the most over-attempted, under-adopted category in protocol design.** Breadth is the pitch and the existential risk. The mitigation is the project's existing discipline: one witness, one domain proven, generality demonstrated rather than asserted.
2. **Every individual column has a well-resourced incumbent.** A standalone fight on transport, identity, or authority loses. The only defensible position is the unifying contract with the failure column as the core, explicitly composing the incumbents.
3. **The clusters point at different communities** with different cultures (cloud-native, industrial, power, local-first). Serving all of them early dilutes everything.
4. **Adoption curves here are long**, and a cross-domain protocol inherits every constituent field's adoption friction at once.
5. **A specification without a strong reference implementation and independent adopters goes nowhere**, and that is a multi-year commitment, not a writing exercise.

## Verdict

**Continue, but reposition.** No project occupies the seam. The strongest single piece of evidence is convergence: the incumbents are independently growing toward the gap from different sides, and each has publicly documented the limitation this design anticipates (Zenoh's dynamic-authorisation roadmap issue, the ROS 2 revocation findings, Keyhive's deliberate identity and discovery exclusions, OCP's open call for coordination standards). That convergence is what a real and timely gap looks like.

The repositioning the evidence forces is the one the specification has since adopted as its identity: not a new transport, identity scheme, or token format, but the contract model that composes them, with declared failure semantics as the genuinely novel core. The biggest genuine risk is not novelty but adoption breadth, and the mitigation is the witness-first discipline the project already follows.

What would change this verdict: a neighbour shipping declared per-capability failure semantics as a contract property, or a credible project unifying the four columns. Issues citing primary sources are the most useful contribution.

## Key sources

- Eclipse Zenoh: zenoh.io; dynamic-ACL roadmap: github.com/eclipse-zenoh/zenoh issue 1432; security analysis: census-labs.com (2025)
- Deng et al., "On the (In)Security of Secure ROS2", ACM CCS 2022; ROS 2 key-challenges review (2024)
- SPIFFE/SPIRE: spiffe.io; CNCF graduation (2022); ephemeral-certificate revocation guidance
- UCAN: github.com/ucan-wg/spec (v1.0.0-rc.1); ucan.xyz use cases
- Keyhive: inkandswitch.com/keyhive and the Beehive notebook (identity and discovery exclusions stated there)
- Zigbee/ZCL and Matter: IEEE 802.15.4; Zigbee Cluster Library documentation (NXP MCUXpresso, 2025); Connectivity Standards Alliance material on the Matter data model
- Datacenter power: Microsoft POLCA (ASPLOS 2024); DynamoLLM; power-stabilisation work (2025); grid-interactive field demonstration, Phoenix (2025); US patent 12,560,987 (sub-15 ms rack throttling); Open Compute Project statements on telemetry and load-signalling standards
- Local-first and CRDTs: Automerge 2.0 (2023, Rust core) and 3.0 (2025, memory redesign); FOSDEM 2026 local-first devroom; "Why Local-First Apps Haven't Become Popular?" (2025)
