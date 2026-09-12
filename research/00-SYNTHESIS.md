# Research synthesis: designing a lightweight, modular intent-spec format

Date: 2026-09-12. Four background reports (01-04 in this folder) were run on Leveson's intent
specifications, the Rasmussen/Vicente abstraction hierarchy they derive from, existing
lightweight traceable formats, and how frameworks handle recursive multi-level design.
This file condenses what matters for format design. Open questions are at the end.

## 1. What Leveson's format actually is

Seven levels (in *Engineering a Safer World*, 2011; the 2000 paper had five, numbered 1-5):

| Level | Name | Language it is written in |
|---|---|---|
| 0 | Program management | Plans, status |
| 1 | System purpose | English goals, requirements, constraints, assumptions, limitations, hazards |
| 2 | System design principles | Domain physics / engineering principles (for TCAS: tau, DMOD, ALIM) |
| 3 | Blackbox behavior / architecture | Component interfaces, state machines over inputs and outputs |
| 4 | Design representation | Pseudocode, HCI design, hardware design |
| 5 | Physical representation | Code, hardware assembly |
| 6 | Operations | Manuals, training, audit procedures, change requests |

Crossed with four columns: environment, operator, system, verification and validation.
Third axis: refinement and decomposition, which happen *within* a level, never between levels.

The test for a means-ends step is that the language changes. Each level is a complete,
different model of the same system, not a more detailed version of the level above.
Adjacent levels answer why (up) and how (down). Links are many-to-many.

Notation in the 1999 TCAS document: bracketed tag on its own line (`[SC4.5]`), links in
trailing parentheses with arrows (`↓2.1, 2.32`, `↑SC.7.1`, `→FTA-405`), plus optional
`Assumption:` and `Rationale:` sub-paragraphs under any item. Tag prefixes are declared in
the preface (G, EA, EC, OP, L, C, SC, FTA). Conventions drift even within that one document.

Leveson's own scope statement: "The exact number and content of the means-ends hierarchy
levels may differ from domain to domain." Rasmussen and Vicente say the same about the
five-level abstraction hierarchy. The domain-specific level set is by design, not accident.

### Generic core vs safety/control-specific

Generic: the means-ends stack with a language change per level; refinement confined within
a level; the four-column split; tagged items with bidirectional links; Assumption and
Rationale attached to any item; the distinction goal / requirement / design constraint /
limitation (accepted risk); evaluation criteria for resolving conflicts; and the rule that
design decisions with no higher purpose are allowed but must be visibly unlinked.

Safety/control-specific: hazards and hazard log, safety-constraint vs other-constraint split,
operator task analysis and HCI models, environment component failure models, an executable
state-machine language at Level 3 (SpecTRM-RL), and the operations level for auditing
assumptions in service.

## 2. How nesting has been done

Leveson's answer for a single spec: the enclosing system *is the environment*. Anything not
newly built goes in the environment column as assumptions (EA) and constraints (EC).

Her students did explicit multi-document nesting (Weiss et al. 2006, a spacecraft):
mission spec, then subsystem spec (TeleSub), then component specs (transmitter, receiver,
antenna). Cross-document links prefix the target document: `[TeleSub EC.2] [Transmitter EA.3]`.
A child's environment assumptions "are justified by tracing them to the section in the other
intent specifications that validates them." Level 2 of the parent (orbit) flows into Level 2
of the child (data rate, power). The JPL 2007 methodology chose the other option: one document
with element-prefixed tags (`A&AC-G1`, `C&DH-SC2`) nested inside each level.

Every mature framework surveyed nests the same way:

| Direction | What crosses the boundary | Source |
|---|---|---|
| Parent to child | Parent's design-level element becomes child's purpose-level statement | ISO 15288 allocation; Capella system-to-subsystem transition; KAOS expectation becomes requirement |
| Child to parent | Child's environment assumptions become parent obligations | Assume/guarantee contracts; GSN away goals; SpecTRM-GC conditions of use |
| Child to parent | Child goals with no parent ("derived") must be acknowledged by the parent | ARP4754A / DO-178C derived-requirement feedback |
| Shared | The interface is owned once and referenced by both | Capella exchanges; Parnas interface spec |

Three candidate patterns with the tradeoffs from report 04:

- (a) Upward `realizes:` references in the child only. Cheap, but the child's assumptions have
  nowhere to go and the parent has no record of its children.
- (b) Allocation table in the parent only. Integration review in one place, but the parent
  grows with every child and a child cannot be reused under a second parent.
- (c) A contract per parent-child edge (GSN contract module, A/G contract). Symmetric,
  assumptions first-class, child reusable, but a third artifact.

Report 04's recommendation: (c) embedded, not separate. The child spec opens with a Context
block that is the contract (parent doc, parent items realized, interface reference,
environment assumptions each with a `discharged-by:` pointer, and a list of derived items).
The parent gets a generated allocation table projected from its children's Context blocks.

## 3. Conventions that survive in plain-text traceability tools

From Doorstop, StrictDoc, Sphinx-Needs, OpenFastTrace, SARA:

1. Stable typed IDs independent of titles and filenames. Level in the prefix so a checker can
   verify a link points where it should. Slug form (`dsn~store-settings`) reads better than
   numeric (`REQ-042`) and survives renumbering.
2. Declare each link type once with its inverse; write only one direction; generate the
   reverse view. Hand-written bidirectional links are where drift starts.
3. Links live in structured metadata (front matter, a `Covers:` line), not only in prose.
4. A change marker so downstream items know upstream changed: Doorstop stores a content
   fingerprint on the link; OpenFastTrace puts a revision in the ID.
5. A small closed vocabulary of link types.

Nothing existing derives from Leveson. Closest tools: SARA (markdown + front matter typed
relations, multi-repo), OpenFastTrace (markdown-native `type~slug~rev` with `Covers:` and
`Needs:`), Sphinx-Needs (typed links, external needs with an ID prefix namespace).

Spec-driven-development formats for AI coding agents (Spec Kit, Kiro, OpenSpec, Tessl) have
per-feature folders, local numeric IDs, prose-only cross-references, and no checker. Drift
between layers is their dominant reported failure.

"Intent specification" is now a crowded name (intent-based networking, LLM agent
constitutions, intent-driven.dev). No project is literally named "IntentSpec".

## 4. What the abstraction-hierarchy literature warns about

- Lind (2003): the semantics of levels and links are vaguely defined; the commitment to a
  fixed number of levels should be abandoned; there is no composition rule for nesting.
- Independent analysts modelling the same domain agree on purposes but diverge on structure.
- The upper levels are intentional (purpose, values, functions); the lower two are physical.
  In intentional domains (software included) "abstract function" is reinterpreted as
  values and priorities.
- Means-ends links are adjacent-level only in every mainstream formulation; insert an
  intermediate node rather than skip a level.
- Frameworks with a built-in cross-scale composition rule: QFD ("the hows of one phase become
  the whats of the next"), Axiomatic Design (zigzag FR to DP), composed FBS, and Alexander's
  pattern languages (each pattern names the larger patterns it completes and the smaller
  ones that complete it). The abstraction hierarchy itself composes only by convention.

## 5. Open design questions

See the conversation log / PLAN.md once decisions are made. Headline questions:

1. Domain scope: software only, or domain-agnostic with per-project level declaration?
2. Primary reader and writer: humans, AI agents, or both? Determines how much goes into
   structured metadata vs prose.
3. Nesting: pattern (c)-embedded as recommended, or something else? File boundary = spec
   boundary? Must children be reusable under multiple parents?
4. Keep the four columns (environment, operator, system, V&V) as first-class structure?
5. Syntax: markdown with front matter and `[[sys:ID]]` links, or a small DSL?
6. Generalise hazards/safety constraints to a risk/obstacle module, or drop?
7. Link vocabulary: Leveson's bare arrows, or typed links?
8. A checker from day one, and a real running example (ideally two nested systems)?
