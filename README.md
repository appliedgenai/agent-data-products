# Data Products for the Agent Economy

## How enterprises publish knowledge graphs, semantic metrics and retrieval indexes for agents to use

**Mohit Mittal · Independent architecture proposal · September 2026**

As enterprises deploy agents across business functions, each team needs business entities and relationships, consistent measures and supporting evidence. If every team reconstructs that knowledge, writes its own metric queries and builds a private document index, the organization acquires many interpretations of the same business—and many copies to secure, evaluate and maintain.

**Publish enterprise meaning as reusable, governed data products that agents can discover and consume.** A knowledge product supplies approved entities and relationships. A semantic metrics product supplies executable business measures. A retrieval product supplies authorized evidence through a maintained vector or hybrid index. Each product has a named owner, an explicit contract and measurable commitments to its consumers.

This paper uses **agent economy** for an ecosystem in which agents across teams—and, where authorized, partner organizations—consume shared enterprise capabilities to perform work. The first economic test is internal reuse: can the next agent use an existing product with less duplicated engineering, interpretation and review effort?

For a CIO, CTO or Chief Architect, the design creates four decisions:

1. Which recurring relationships, measures and evidence should become shared products?
2. What meaning, access, freshness, failure behavior and evidence may an agent rely on?
3. Which engines should be bought, and which product contracts and decision rights must remain enterprise-owned?
4. Does a second consumer demonstrate reuse without shifting hidden work into operations or control teams?

## Reference architecture

Publish domain-owned knowledge, calculation and retrieval capabilities above the existing data estate. Agent applications discover released products, resolve compatible versions and invoke only the operations permitted for the task. Evaluated outcomes return to accountable owners for diagnosis and reviewed product releases.

![Three classes of owned data products supply several enterprise agents through governed discovery and consumption.](diagrams/01-agent-product-architecture.png)

*Figure 1. The reference architecture comes before the example. Solid paths show publication and consumption. Dashed paths carry observations to owner review and reviewed releases back to the products. Product and application interfaces enforce the relevant controls.*

| Responsibility | Accountable outcome |
|---|---|
| Enterprise data foundation | Authoritative inputs, validated transformations and source access |
| Domain product owners | Business meaning, supported operations, quality, lifecycle and consumer support |
| Discovery and consumption | Version resolution, verified identity, bounded invocation and usage records |
| Agent application owners | Task intent, product composition, result acceptance, disclosure and any separately authorized action |
| Product operations and evaluation | Service health, representative tests, incident diagnosis and reviewed releases |

These are logical responsibilities. A platform may implement several of them, and one product may use several engines. The boundaries matter because they assign meaning, access, change and failure to an owner.

## Three products, three promises

| Product | Consumer promise | Returned evidence | Failure that must remain visible |
|---|---|---|---|
| **Knowledge graph product** | Resolve permitted entities and approved relationships for a declared effective date | Stable IDs, relationship paths, validity, provenance and product version | Unresolved identity, conflicting relationships or incomplete coverage |
| **Semantic metrics product** | Calculate an approved measure for a specified population, period and breakdown | Definition version, grain, components, time bounds, source snapshot and calculation reference | Unsupported dimension, incompatible population, unsafe join or stale coverage |
| **Retrieval product** | Return relevant, permitted passages from a declared corpus | Source/version, location, dates, retrieved passages and retrieval/index version | Missing entitlement, stale index, weak retrieval or no supported evidence |

The product is the maintained business capability and contract, not its storage engine. A relational service can implement a knowledge product when its relationships are simple. A graph engine earns its cost when representative traversal and explanatory paths require it. A metric product may use a semantic layer, and a retrieval product may use vector, lexical or graph-assisted retrieval. The enterprise keeps the product promise stable when an implementation changes.

## The contract an agent can check

A catalog entry needs more than an endpoint name. It should publish purpose, supported questions, definitions, owner, approved versions, access route, service objectives, qualification evidence, cost model and deprecation policy.

| Contract part | Producer publishes | Consumer checks |
|---|---|---|
| Business promise | Meaning, permitted uses, namespace, grain, effective-time and correction rules | Whether the product can answer the intended question |
| Invocation | Typed inputs/outputs, operations, delegated identity, limits and error behavior | Whether the call is authorized, compatible and within budget |
| Evidence and service | Provenance, coverage metadata, evaluation cases, freshness/availability and support | Whether this result meets the task's acceptance conditions |
| Change and retirement | Compatible versions, migration, consumer inventory, retention and deletion obligations | Whether a release, correction or retirement affects the application |

Verified identity and scope come from credentials and policy. Agent-supplied identity fields cannot authorize access. Keep contract version, implementation release, data snapshot and current policy distinct; one identifier cannot stand in for the others.

Individually valid products do not automatically form a valid answer. The consuming application checks population and entity compatibility, time and correction basis, and whether retrieved evidence applies to the same entities and period. Required checks fail closed for the affected conclusion. Current authorization still constrains final disclosure and any downstream action.

## Build on the data estate already in place

Operational systems, master data, lakehouses, warehouses and document repositories remain the foundation. In a medallion estate, Bronze can preserve captured inputs, Silver can supply validated detail and identities, and Gold can supply business-ready models and measures. An optional local **Platinum** label may identify semantic and knowledge products served to agents; it is not an established fourth medallion quality grade.

![Medallion refinement feeds owned graph, metric and retrieval products through suitable detailed and business-ready inputs.](diagrams/03-foundation-to-products.png)

Do not force every product through the same physical sequence. A graph may need validated entity detail, metrics need models at the correct grain and retrieval needs eligible content. Each product owns its dependencies, synchronization, access and recovery commitments. Gold definitions should not be copied merely to create a new label.

## Buy engines; own the products

Buy or configure engines when they meet security, geography, scale, interoperability and operating requirements. Build or extend where domain relationships, calculation behavior, retrieval quality or cross-platform controls differentiate the business.

The enterprise still owns:

- definitions, permitted use and product acceptance;
- identity mapping, authorization and disclosure policy;
- source lineage, evaluation sets and quality thresholds;
- service objectives, incidents, corrections and consumer migration;
- product economics and the decision to expand, replace or retire.

Buying implementation does not transfer business accountability. Compare full lifecycle cost: platform consumption, integration, data movement, controls, evaluation, specialist operations, change, resilience and exit.

## A composition example

A fictional metric agent answering a renewal-performance question resolves the permitted customer cohort from a knowledge product, requests an approved renewal-rate calculation from a metrics product and retrieves supporting policy evidence from a retrieval product. The products remain independently reusable; the application owns the task-specific composition and disclosure.

![A metric agent resolves a cohort, obtains an approved calculation and retrieves supporting evidence under three product contracts.](diagrams/02-product-composition.png)

The application rejects incompatible populations or periods, retains product and calculation references, and states when supporting evidence is unavailable. Retrieval relevance cannot repair a failed metric calculation, and a plausible metric cannot establish that the cited evidence applies.

## Adopt through a second consumer

Begin with one funded agent task and the smallest product surface it needs. Establish current duplicated work, interpretation errors, support effort and time to onboard a consumer. Publish a contract, operate it with the first consumer and test access denial, stale data, incompatible versions, source correction and recovery.

Then onboard a materially different second consumer. Expand only when it can reuse the product without private definitions or bypass paths and when total onboarding, review and operating effort improves. Product owners review evaluated failures and usage patterns; they release corrections through normal change controls. Raw prompts, traces or feedback do not silently become trusted definitions.

Useful measures include time to onboard a new consumer, duplicated pipelines or private indexes retired, contract conformance, freshness and availability, cost per successful call, product-caused task failures, correction time and consumer retention. Connect those measures to the funded business outcome; reuse alone is not value.

## Read the full architecture

The [full paper](PAPER.md) contains the detailed product contracts, access and failure semantics, evaluation loop, people and decision rights, sourcing tests, worked example and adoption gates. See [Sources and claim boundaries](SOURCES.md).

This paper is one part of [The Agentic Enterprise Blueprint](https://github.com/appliedgenai/agentic-enterprise-blueprint). The blueprint defines the enterprise planes; this paper defines how the Data Plane publishes reusable meaning for the Knowledge & Context Plane and agent applications.

**Mohit Mittal · Chief Architect · 22+ years.** Experience includes production LLM/RAG at Chegg and target-state architecture for an AI-native healthcare platform. This is an independent architecture proposal; examples are synthetic and tool combinations require evaluation.

[CC BY 4.0](LICENSE.md)
