# Recursive / multi-level design: how existing frameworks nest one system's spec inside another's

Research note. Two hosts were unreachable during research (sunnyday.mit.edu and ResearchGate), so the Leveson and Kelly details below come from prior knowledge of those papers, with URLs given for verification.

## 0. The core observation

Every mature framework surveyed handles nesting with the same move: **a design element at level N becomes the "system of interest" at level N+1, and the parent's design-level description of that element becomes the child's purpose-level description.** What differs is (i) which artifact owns the link, (ii) whether the child's *assumptions about its environment* are treated as first-class obligations on the parent, and (iii) how unparented "derived" items in the child are fed back up. Those three questions are what an intent-spec nesting scheme must answer.

## 1. Systems engineering standards: 15288, INCOSE, ARP4754A, DO-178C

**ISO/IEC/IEEE 15288** is explicitly recursive. The standard says its processes "can be applied to systems of interest, their system elements, and to systems of systems," that "a system element may be a system," and that each enabling system "has a life cycle of its own" and is treated as a system-of-interest in its own right ([ISO OBP text](https://www.iso.org/obp/ui#!iso:std:iso-iec-ieee:15288:ed-2:v1:en)). SEBoK restates the rule: "In each decomposition layer and for each system, the System Definition processes are applied recursively because the notion of 'system' is in itself recursive; the notions of SoI, system, and system element are based on the same concepts" ([SEBoK, Applying Life Cycle Processes](https://sebokwiki.org/wiki/Applying_Life_Cycle_Processes)). The INCOSE Handbook describes "a recursive application of SE to levels of system element with each application representing a system project" ([SEBoK, Applying the Systems Approach](https://sebokwiki.org/wiki/Applying_the_Systems_Approach)).

The interface between levels is **allocation**: "the process by which the requirements at one level of the physical architecture are assigned to entities at the next lower level ... that have a role in the implementation of the allocated requirement" ([SEBoK, System Requirements Definition](https://sebokwiki.org/wiki/System_Requirements_Definition)). Key detail: the *parent's* allocated/system requirements become the *child's* stakeholder requirements. The child project then runs the full requirements-definition, architecture, and verification cycle against them. So the child's "Level 1" is, by construction, a projection of the parent's "Level 2/3."

**ARP4754A** makes the tiers concrete: aircraft function -> system -> item (hardware DO-254, software DO-178C). Its five development processes include "allocation of aircraft functions to systems" and "allocation of system requirements to items" ([Jama ARP4754A guide](https://www.jamasoftware.com/requirements-management-guide/aerospace-and-defense/arp4754a/)). Every requirement at a tier must trace to the tier above, *except* **derived requirements**: requirements that arise from design decisions at the lower tier and have no parent. The rule is that they cannot simply live at the lower tier; "when the processes of DO-254 and DO-178C create new 'derived requirements', they must feed these requirements back up to the system (ARP4754A) and safety (ARP4761A) processes to ensure they do not adversely affect safety" ([AFuzion](https://afuzion.com/arp4754a-introduction-avionics-systems/); [Springer, DO-178C lifecycle with ARP4754A](https://link.springer.com/article/10.1007/s42401-026-00455-4)). This is the ends-means integrity mechanism: the child is *allowed* to invent goals the parent never asked for, but the parent must explicitly acknowledge them, because a child-level design decision can create a new aircraft-level failure condition. TCAS is a textbook case: TCAS's own design decision to issue Resolution Advisories creates the aircraft-level hazard "RA induces a near-miss with a third aircraft," which the aircraft-level safety assessment must own.

## 2. Arcadia / Capella and SysML v2

**Arcadia's four layers**: Operational Analysis (stakeholder needs, no system yet), System Analysis (the system as a black box with actors and functional exchanges), Logical Architecture (white-box decomposition into logical components), Physical Architecture (physical components, nodes, deployments). Each layer is linked to the one above by **realization/transition links** on functions, components, and exchanges; Capella's "transition" commands generate a skeleton of the lower layer from the upper one and keep trace links ([mbse-capella features](https://mbse-capella.org/features.html); [Capella tutorial, Logical Architecture](https://gettingdesignright.com/GDR-Educate/Capella_Tutorial_v6_0/LogicalArchitecture.html)).

A hard constraint drives the nesting mechanism: **a Capella model's System Analysis can contain exactly one "System."** Subsystems can only appear as components inside the parent's LA or PA. So to give a subsystem its own four-layer analysis you must create a *separate model* whose System *is* that component ([Capella forum thread](https://forum.mbse-capella.org/t/system-to-subsystem-transition-system-analysis-in-subsystem/3788)).

The **System to Subsystem Transition add-on** automates this ([GitHub, capella-sss-transition](https://github.com/eclipse-capella/capella-sss-transition); [DeepWiki summary](https://deepwiki.com/eclipse-capella/capella-sss-transition); [usage instructions](https://github.com/eclipse-capella/capella-sss-transition/blob/master/plugins/org.polarsys.capella.transition.system2subsystem.doc/html/User%20Manual/14.2.%20Usage%20instructions.mediawiki)). It offers three strategies:

- **Scoped horizontal extraction**: copy a subset of the parent LA or PA (a component and its dependency closure) into a new model at the same layer.
- **Vertical transition (SA)**: the selected logical/physical component is promoted to the *System* of a new model's System Analysis. Its sibling components and the parent's actors become the child's **actors**. The functional exchanges and component exchanges that crossed the selected component's boundary in the parent become the child's **external functional exchanges and interfaces**. The functions allocated to the component in the parent become the child's system functions. "Subsystem will be named based on the selected Component."
- **Vertical transition (SA-LA-PA, "multiphase")**: same, but also populates the child's LA and PA from the parent's deployed sub-structure.

Two properties make this the reference design for spec nesting. First, the **contract is computed, not written**: the child's external interface is exactly the parent's boundary of that component, and the add-on "will try to ensure that [functional] chain remains valid" when a chain crosses the boundary. Second, it is **iterative**: on re-run, a Diff/Merge dialog shows differences between the new transformation result and the child model, letting the subsystem team "selectively merge changes," while "strict traceability via system-wide IDs" preserves links. That is, the parent-to-child edge is a *generated, re-synchronizable projection*, and the child may elaborate freely below it.

Note what Capella does **not** do: it has no first-class "derived requirement feedback" from child to parent. Child-level findings that should change the parent are handled by re-running the transition after editing the parent (or by requirements tooling outside Capella).

**SysML v2** handles decomposition by nesting part usages: "A part definition is composed of parts that are defined by part definitions ... This pattern applies recursively down the system hierarchy" ([Friedenthal, SysML v2 Basics](https://www.omgwiki.org/MBSE/lib/exe/fetch.php?media=mbse%3Asysml_v2_transition%3Asysml_v2_basics-incose_iw-sfriedenthal-2024-01-28.pdf)). Requirements are constraints with an explicit `subject`; a requirement usage on a nested part, `satisfy` relationships, and `allocate` relationships give per-level traceability in one model. SysML v2 is more monolithic than Arcadia: it favors one model with deep nesting over separate models per subsystem, and relies on the "subject" of a requirement (which part it constrains) to establish level. That is fine for a single organization and weak at organizational boundaries.

## 3. Leveson: STPA hierarchical control structures and intent specifications

STAMP models a system as a **hierarchy of control loops**: each controller has responsibilities, a control algorithm, a process model, control actions, and feedback ([STPA Handbook](https://www.flighttestsafety.org/images/STPA_Handbook.pdf)). Nesting is native: the controlled process of one loop is itself a controller in the loop below (e.g., FAA -> airline -> flight crew -> aircraft automation -> aircraft). The rule linking levels is that **safety constraints at a higher level are enforced by the responsibilities of the controllers below it**: you derive a lower controller's responsibilities from the higher-level constraints it must enforce, and STPA Step 3 (unsafe control actions) at each level yields refined constraints for the next level down. Derived responsibilities are reconciled by running STPA on the whole structure, not on one loop.

On **multiple intent specifications**: in the TSE paper ([Intent Specifications, TSE 2000](http://sunnyday.mit.edu/papers/intent-tse.pdf); host unreachable today) and in *Engineering a Safer World* ch. 10, the TCAS spec is written as one document, but Level 1 explicitly situates TCAS as one component of the larger airspace system: it contains an *Environment description*, *Environment assumptions* (numbered EA-n, e.g., assumptions about transponder equipage and altimetry), and interface descriptions to the Mode-S transponder, altimeters, and displays that are, structurally, the aircraft-level obligations TCAS depends on. Leveson does not write a separate aircraft intent spec, but the closest she comes to a nesting mechanism is the **SpecTRM-GC ("generic component")** work with Weiss and Ong ([Reusable Specification Components for Model-Driven Development](http://sunnyday.mit.edu/papers/incose.pdf); [Weiss & Leveson, AIAA JACIC](http://sunnyday.mit.edu/AIAA-Weiss.pdf)). There, each reusable component has its **own intent specification** whose Level 1 states the component's purpose, its *conditions of safe use*, and the assumptions it makes about its environment; the system-level spec then integrates component specs, and the integrator's job is to show that the system design discharges each component's assumptions. This is precisely pattern (c) below, expressed in Leveson's own vocabulary.

## 4. Contract-based design (Benveniste et al.)

An assume/guarantee contract is a pair (A, G): "A is an assumption describing the expected behavior of the environment, and G is a guarantee describing the behavior that the system must ensure whenever the environment satisfies A" ([Benveniste et al., Contracts for System Design, 2018 monograph PDF](https://people.rennes.inria.fr/Albert.Benveniste/pub/ContractsMonograph2018.pdf); [ACM entry](https://dl.acm.org/doi/10.1561/1000000053)). Three operations matter for nesting:

- **Refinement**: C' refines C iff A' is weaker than or equal to A and G' is stronger than or equal to G (child assumes less, guarantees more). Parent-level design element to child-level top-level contract is a refinement obligation.
- **Composition**: composing components C1 and C2 yields a contract whose guarantee is G1 and G2 and whose assumption is (A1 and A2) *weakened by what the siblings guarantee*. Each child's assumption is discharged either by a sibling's guarantee or becomes an assumption of the composite (i.e. an obligation the parent must pass further up).
- **Independent implementability**: if each child satisfies its own contract, the parent's contract holds, so child teams can work in isolation.

Mapping to an intent spec: the child's "environment assumptions" section is A; its Level-1 goals/constraints are G; the parent's design section must show, for each child assumption, which sibling guarantee or which parent-level assumption discharges it. Any child assumption not discharged is exactly ARP4754A's derived requirement in another guise. Tools like Pacti implement this algebra ([Pacti, ACM TCPS](https://dl.acm.org/doi/full/10.1145/3704736)).

## 5. Software analogs

**Parnas module guide** ([Parnas, Clements, Weiss 1985](https://cse.msu.edu/~cse870/Input/SS2002/MiniProject/Sources/parnas84-mod-structure.pdf)): the A-7E guide is "hierarchically structured; the structure of the document mirrors that of the system," and "states only the secret of each module." Each node names the design decision it hides; leaves get separate *module interface specifications*. The nesting contract is thus: the parent node's *secret* is a partition of decisions, the child's secret is one of those decisions, and the interface spec is a separate document owned by the module but consumed by its users. Parnas also keeps a separate **uses hierarchy**, i.e., dependency and decomposition are different structures.

**DDD bounded contexts and context maps** ([DDD Reference](https://www.domainlanguage.com/ddd/reference/); [Fowler, BoundedContext](https://martinfowler.com/bliki/BoundedContext.html)): each context has its own model/spec; the *context map* is the inter-document contract, with named relationship types (Partnership, Shared Kernel, Customer/Supplier, Conformist, Anticorruption Layer, Open Host Service, Published Language, Separate Ways). Upstream/downstream makes the *direction of obligation* explicit: a Conformist downstream accepts the upstream's model as-is; an ACL downstream isolates itself. This is the richest vocabulary for "what kind of dependency is this edge."

**C4** ([c4model.com](https://c4model.com/); [abstractions](https://c4model.com/abstractions/component)) is a pure recursive zoom (system context -> container -> component -> code) inside one system; the context diagram of a child system is exactly the container diagram of the parent restricted to that container's neighbors, which is the Capella move done informally.

**Team Topologies' Team API** ([teamtopologies.com](https://teamtopologies.com/key-concepts-content/category/Team+API); [TeamAPI-as-code](https://github.com/TeamTopologies/TeamAPI-As-Code)): the owning team publishes an explicit interface (scope, ownership, artifacts, SLOs, communication channels, change cadence). This treats the *organizational* edge as the contract, parallel to Kelly's safety-case contracts and Conway's law.

**Monorepo per-package design docs**: the common practice (Google-style design docs plus ADRs per package) is an informal version of pattern (a): each package doc has a "Context" section linking to the parent's doc and an ADR trail. No canonical published spec exists for it, so none is cited.

## 6. Goal modeling: KAOS and modular GSN

**KAOS** ([van Lamsweerde, KAOS overview](https://webperso.info.ucl.ac.be/~avl/gore.php); [Lapouchnian survey](https://www.cs.utoronto.ca/~alexei/pub/Lapouchnian-Depth.pdf)) refines goals until each leaf is assignable to a single *agent*. The boundary rule is the important part: a leaf "assigned to the software-to-be" is a **requirement**; a leaf assigned to an environment agent is an **expectation**. Nesting therefore means: the parent's expectation of agent X is the child spec's top-level requirement when X is the child. Alternative responsibility assignments ("OR responsibility links") let you move the boundary. KAOS also has obstacle analysis for refuted expectations, which is the goal-model analog of derived-requirement feedback.

**Modular GSN** is the most explicit inter-document contract mechanism. The GSN Community Standard's modular extension ([v1 PDF via FAA](https://www.faa.gov/about/office_org/headquarters_offices/ang/redac/redac-sas-201503-gsn-community-standard-v1.pdf); [Adelard summary](https://www.adelard.com/asce/gsn/modular-gsn-extension/); [SCSC GSN](https://scsc.uk/gsn)) defines:

- **Module**: a self-contained argument with public and private elements. Public goals/contexts may be referenced from outside.
- **Away Goal / Away Context / Away Solution** (also Away Assumption, Away Justification): a reference in module A to a public element of module B, drawn as the ordinary shape with a lower compartment naming the module ID.
- Three inter-module relationships: *away elements*, *supported by module* (a goal is solved by an entire module), and *supported by contract*.
- **Contract module**: a small module recording *only* the mapping "goal Gp in the supported module is solved by goals Gc1, Gc2 in supporting modules, under context Ck and assumptions Aj," with a table of participating modules. Kelly's original formulation ([Managing Complex Safety Cases](https://link.springer.com/chapter/10.1007/978-1-4471-0653-1_6); [Bate & Kelly, Safety Case Composition Using Contracts](https://link.springer.com/chapter/10.1007/978-1-84628-806-7_9)) requires each module's **interface** to declare: objectives addressed (public goals), evidence presented, context/assumptions defined, and *arguments requiring support from other modules* (away goals, i.e., its assumptions).

Sketch of the notation, TCAS inside aircraft:

```
Module ACFT (aircraft safety case)
  G-A1  "Aircraft avoids mid-air collision"           [public]
    |- supported by contract  C-A1-T1

Contract module C-A1-T1
  supported goal:   ACFT.G-A1
  supporting goals: TCAS.G-T1 "TCAS issues correct RAs within 1 s", TCAS.G-T2 ...
  context:          TCAS.C-T3 "Own aircraft has a Mode-S transponder"   (away context)
  assumption:       ACFT.A-7  "Altimeter error < 100 ft"                 (away assumption)
  participating modules: ACFT, TCAS, ALTIMETER

Module TCAS (TCAS safety case)
  G-T1 ... [public]
  Away goal ALTIMETER.G-L2 "Altitude data accurate to 100 ft"   <- TCAS's assumption, owned elsewhere
```

The design insight here is that GSN puts the contract in its **own module** so that (i) both parent and child stay reusable, (ii) the contract can be re-validated in isolation when either side changes, and (iii) every child assumption must be visibly discharged by an away reference to somebody's public goal. Argevide's SACM/GSN comparison shows the same idea carried into SACM's "artifact/assurance-case packages" ([Argevide](https://www.argevide.com/2025-06-modular-assurance-cases/)).

## 7. Conceptual framing: why nested means-ends hierarchies should be self-similar

Simon's *Architecture of Complexity* ([1962 PDF](https://pespmc1.vub.ac.be/books/architectureofcomplexity.pdf)) argues complex systems are **nearly decomposable hierarchies**: intra-subsystem interactions dominate inter-subsystem ones, so "little information is lost by representing them as hierarchies," and each level can be described by an interface that abstracts the level below. Koestler's **holon** ([Holon](https://en.wikipedia.org/wiki/Holon_(philosophy))) is the unit that is simultaneously a whole to its parts and a part to its whole. Beer's **Viable System Model** ([VSM](https://en.wikipedia.org/wiki/Viable_system_model)) makes recursion a structural axiom: every viable system contains and is contained in a viable system with the *same* five-subsystem anatomy, and Beer stresses that "no higher centre can process sufficient variety to direct every action in detail," so lower levels must have local autonomy bounded by the level above. Translated to specs: a child spec must have the full intent-spec shape (its own Level 0 through 7), the parent must not try to write the child's internals, and the parent-child edge must carry both *purpose downward* and *variety (surprises) upward*.

## Synthesis: three candidate nesting patterns

Framework consensus on what crosses the boundary:

| Direction | Content | Framework source |
|---|---|---|
| Parent -> child | Child's purpose = parent's design element (allocated functions, constraints, interfaces, sibling actors) | 15288 allocation; Capella S2SS; KAOS expectation -> requirement |
| Child -> parent | Child's environment assumptions become parent obligations | A/G contracts; GSN away goals; SpecTRM-GC conditions of use |
| Child -> parent | Unparented (derived) child goals/constraints must be acknowledged by parent | ARP4754A / DO-178C derived-requirement feedback |
| Both | Interface (ports, exchanges, data) owned once, referenced by both | Capella exchanges; Parnas interface spec; Team API |

### Pattern (a): Upward references in the child

Each child Level-0/1 item carries `realizes: <parent-doc>#<parent-item-id>`; items without one are tagged `derived`. This is the DO-178C/ARP4754A trace model and C4-style zoom.

*Pros*: cheap, local, machine-checkable, child can be written by a different team, tooling can list all derived items for review.

*Cons*: the parent has no record that a child exists unless you index the reverse links; the child's *assumptions* have nowhere to go (a `realizes` link says what the child does for the parent, not what it needs from it); ID drift in the parent silently orphans children; derived-item feedback becomes a convention, not a structure.

### Pattern (b): Allocation section in the parent

The parent's Level-2/3 design lists, for each design element, the child spec that realizes it and the parent items it was allocated. This is 15288 allocation and Capella's "component becomes System."

*Pros*: the parent owns ends-means integrity in one place, integration review is a single table, missing children are visible.

*Cons*: the parent grows with the number of children and must be edited for every child change; it does not naturally hold the child's assumptions either (they end up as ad-hoc notes); it is asymmetric, so reusing a child in a second parent means duplicating knowledge.

### Pattern (c): A separate contract artifact per edge

A small document (or section pair) between parent and child stating: the parent items being realized, the child goals that realize them, the interface, the child's assumptions and which parent/sibling guarantee discharges each, and derived child items acknowledged by the parent. This is the GSN contract module, the Benveniste A/G contract, Capella's boundary exchanges, and the Team API.

*Pros*: symmetric; assumptions are first-class and discharged explicitly; child reusable across parents (SpecTRM-GC); re-validation is scoped to the edge when either side changes; naturally expresses DDD-style relationship type (conformist vs ACL).

*Cons*: a third artifact to maintain; for a system with two components it is ceremony; needs tooling to stay consistent with both ends.

### Recommendation

Use (c) as the model but embed it rather than making a separate file until the system has organizational boundaries. Give the child spec a mandatory **"Context" block** at the top of Level 1 that *is* the contract:

- parent doc ID and the parent items realized (the downward projection),
- interface reference (owned once, referenced by both),
- environment assumptions, each with a `discharged-by:` pointer to a parent or sibling item,
- a `derived:` list of child Level-1 items with no parent.

Give the parent a generated **allocation table** (pattern b) that is a projection of all children's context blocks, so it cannot drift. That combination reproduces Capella's computed subsystem contract, GSN's module interface, and ARP4754A's derived-requirement feedback with one hand-written block per child and one derived table per parent.

The invariants to enforce with a checker:

1. Every child Level-1 goal either realizes a parent item or is marked derived and appears in the parent's acknowledged-derived list.
2. Every child environment assumption has a discharger (a parent-level assumption or a sibling guarantee).
3. Every parent design element that names a child appears in that child's context block.
4. The parent's Level-3 interface for the component and the child's Level-3 environment interface are the same artifact, or one is generated from the other.

Mapping between intent-spec levels across the edge (the Capella S2SS rule restated for intent specs):

| Parent level | Becomes in child |
|---|---|
| Level 2 design rationale for the component | Level 1 goals and rationale ("why this component exists") |
| Level 3 blackbox component: allocated functions, constraints | Level 1 high-level requirements and design constraints |
| Level 3 interfaces to siblings and actors | Level 1 environment description; Level 3 environment/interface spec |
| Parent-level hazards allocated to the component | Level 1 safety constraints |
| (none) | Child derived items, fed back to parent Level 1/2 |
