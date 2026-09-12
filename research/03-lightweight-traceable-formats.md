# Survey: lightweight, modular, text-based design and specification formats with explicit cross-references

Prepared 2026-09-12 for the intent-specification format design. Scope: what exists, how each item structures levels/views, how IDs and cross-references work, how it composes across documents or systems, how lightweight it is, and known weaknesses. Synthesis at the end.

## A. Goal-oriented requirements engineering and assurance cases

### KAOS

- What: goal-oriented RE method (van Lamsweerde). Sources: [KAOS tutorial](https://www.cse.msu.edu/~cse870/Materials/GoalModeling/KaosTutorial-2007.pdf), [MSU lecture notes](https://www.cse.msu.edu/~cse870/Lectures/Sp2021/02c-KAOS-goal-modeling-notes2021.pdf), [goal-driven RE with KAOS](https://posomas.isse.de/Practices/aose.practice.req.goal_driven_requirements_elicitation.base/guidances/supportingmaterials/goal_driven_re_with_kaos_47BC83D3.html).
- Levels: a single goal graph refined through AND/OR refinement until each leaf can be assigned to one agent. A leaf assigned to a software agent is a *requirement*; to an environment agent, an *expectation*; *domain properties* are the third leaf kind. Obstacles are goal negations with their own refinement trees and *resolution* links back to goals. *Conflict* links between goals are explicit. Responsibility links tie leaves to agents; operationalisation links tie requirements to operations.
- IDs and cross-references: graph edges inside the Objectiver tool. No text syntax in common use, no ID convention.
- Modularity: none beyond the graph. No notion of one model as a component of another.
- Lightness: heavy, tool-bound; the optional formal layer uses real-time LTL.
- Weaknesses: unwieldy graphs, no portable text form. What is worth stealing: the fixed vocabulary of link types (refines, conflicts-with, obstructs, resolves, responsible-for, operationalises) and the stopping rule "refine until a single agent is responsible".

### i* / iStar 2.0 / Tropos

- Sources: [iStar 2.0 Language Guide](https://arxiv.org/pdf/1605.07767), [piStar tool](https://www.cin.ufpe.br/~jhcp/pistar/).
- Structure: actors (role, agent), dependencies between actors (depender, dependum, dependee), intentional elements (goal, quality, task, resource) and four typed links between them: refinement (AND/OR), needed-by, contribution (make/help/hurt/break), qualification.
- IDs and cross-references: none in a text sense; piStar is a browser editor with JSON export and enforces which link types are legal between which element types.
- Modularity: actor boundaries are the only scoping. No document composition.
- Lightness: tool-only.
- Weaknesses: social/strategic modelling, not a design hierarchy; no text syntax.

### GRL / URN (ITU-T Z.151)

- Sources: [jUCMNav paper](https://www.researchgate.net/publication/221222288_Modeling_and_analysis_of_URN_goals_and_scenarios_with_jUCMNav), [Adding a textual syntax to GRL](https://link.springer.com/chapter/10.1007/978-3-319-24912-4_12).
- Structure: URN combines GRL goal models with Use Case Map scenarios in one standard. *URN links* are typed, named links between any two elements across the two views (goal to scenario responsibility, for example). This is the closest standardised precedent for "every element densely linked across views".
- IDs and cross-references: XML interchange defined in Z.151; a textual syntax (TGRL) was added later via Xtext.
- Modularity: none across models.
- Lightness: Eclipse plugin (jUCMNav), heavy.
- Weaknesses: tool-bound, dated.

### GSN v3 and the modular extension

- Sources: [SCSC GSN standard page](https://scsc.uk/gsn-standard) (standard SCSC-141C), [Adelard modular GSN extension](https://www.adelard.com/asce/gsn/modular-gsn-extension/), [Argevide on GSN and SACM modular cases](https://www.argevide.com/2025-06-modular-assurance-cases/), [contract-based modular assurance](https://arxiv.org/pdf/2402.12804), [Astah GSN](https://astah.net/products/astah-system-safety/gsn-goal-structuring-notation/).
- Core: goal, strategy, solution, context, assumption, justification, undeveloped marker. Relations: SupportedBy, InContextOf.
- Modular extension (directly relevant to composition):
  - A *module* is a self-contained argument. Elements can be marked *public*, meaning they may be referenced from other modules.
  - *Away goal*, *away context*, *away solution*, *away assumption*, *away justification*: a stub inside module A that cites an element in module B, labelled with B's module identifier. The stub cannot be altered locally; it is a pure reference.
  - *Module reference*: cites a whole remote module. *Contract reference* / *contract module*: records that a claim in one module is sufficient to support a claim in another, and under what context that support holds. A goal can be marked "solved by contract" before the contract is written.
  - Argevide summarises three inter-module relation strengths: away element (link only, weakest), supported-by-module (a plain SupportedBy across the boundary), and contract (a verified mapping with stated context, strongest).
- IDs: element IDs like G1, S1, Sn1, C1, plus module identifiers. Tool-specific in practice.
- Lightness: diagram-first; XML or tool interchange. Tools: ASCE, Astah GSN, D-Case Editor, AdvoCATE. There is no canonical plain-text GSN; YAML-based renderers exist that support modules and check dangling references within a file set, worth a look if a ready-made checker for a GSN-like layer is wanted.
- Weaknesses: graphical notation, argument-only (no design layer), tooling is commercial or academic.

### SACM 2.x, Assurance 2.0, CAE, eliminative argumentation

- Sources: [OMG SACM 2.2](https://www.omg.org/spec/SACM/2.2/PDF), [Making modular assurance cases work with SACM](https://www.researchgate.net/publication/371947060_Making_Modular_Assurance_Cases_Work_Using_Structured_Assurance_Case_Metamodel_SACM), [Assurance 2.0](https://www.csl.sri.com/users/rushby/assurance2.0), [Defeaters and eliminative argumentation in Assurance 2.0](https://arxiv.org/abs/2405.15800), [Adelard CAE](https://www.adelard.com/asce/cae/).
- SACM formalises modularity: ArgumentPackage, ArgumentPackageInterface (citations of the elements a package exposes), ArgumentPackageBinding (argument elements that connect cited elements of two or more packages). Argevide extends this with *provided* vs *required* interfaces, and required interfaces are subdivided into the three GSN relation strengths.
- Assurance 2.0 / CAE: claims, arguments, evidence, with five CAE *blocks* (decomposition, substitution, evidence incorporation, concretion, calculation/proof) and *defeaters* (rebutting, undercutting) as first-class elements. Eliminative argumentation: refute all reasons the top claim could be false.
- Weakness: metamodel-level standards with XMI; not authoring formats.

## B. Design rationale notations

- IBIS / gIBIS ([overview](https://people.engr.tamu.edu/furuta/436slides/ch26.pdf)): issues, positions, arguments with supports/objects-to links; a simple indented-text form exists; records the *process* of design. Tools: gIBIS, Compendium.
- QOC ([original paper](https://dl.acm.org/doi/10.1207/s15327051hci0603%25264_2), [summary](https://acawiki.org/Questions,_Options,_and_Criteria:_Elements_of_design_space_analysis)): questions, options, criteria with assessment links; positioned as a *product* of design rather than a transcript.
- DRL (Lee): decision problem, alternative, goal, claim, with many typed claim relations (supports, denies, presupposes, is-sub-decision-of). The most expressive and never lightweight. QOC is described as mapping closely to DRL but much simpler.
- ADRs ([adr.github.io templates](https://adr.github.io/adr-templates/), [MADR primer](https://ozimmer.ch/practices/2022/11/22/MADRTemplatePrimer.html), [MADR format and tool support paper](https://ceur-ws.org/Vol-2072/paper9.pdf), [adr.zone comparison](https://www.adr.zone/adr-template)):
  - Nygard: title, status, context, decision, consequences; one numbered markdown file per decision (`0007-use-postgres.md`); status carries "superseded by [ADR-0009]".
  - MADR: adds decision drivers, considered options with pros and cons, decision outcome with confirmation, "more information". Full and minimal variants.
  - Y-statement (Zimmermann): "In the context of X, facing Y, we decided Z and neglected W, to achieve A, accepting that B." MADR sections map onto the Y-statement clauses.
  - Cross-references: sequential numeric ID in the filename, relative markdown links, "supersedes / superseded by / amends" in status. Tools: adr-tools (`adr new -s N` writes supersede links both ways, `adr link`), [log4brains](https://www.npmjs.com/package/log4brains) (renders a site, parses status links), Structurizr `!adrs` attaches an ADR folder to a workspace, system, or container ([docs](https://docs.structurizr.com/dsl/adrs)).
  - Weaknesses: decisions link to decisions, rarely to the requirements they satisfy or the components they shape; decision drivers stay prose; no ADR tool checks dangling links.

## C. Architecture documentation frameworks

- C4 and Structurizr DSL ([DSL reference](https://docs.structurizr.com/dsl/language), [workspace extension](https://docs.structurizr.com/dsl/cookbook/workspace-extension/), [enterprise usage](https://docs.structurizr.com/workspaces/enterprise), [scaling C4 with Structurizr](https://medium.com/@viorel.contu/scaling-c4-with-structurizr-part-1-workspaces-acc7c23bfc39)):
  - Four zoom levels of one model (context, container, component, code). View consistency is guaranteed because every diagram is rendered from one element set.
  - Text form: DSL identifiers (`api = container "API"`), `!include` to split files (documented as "small scale", not for an uber-workspace), `!extends` to inherit all identifiers of a base workspace, and a "system catalog" workspace pattern for organisation-wide composition. `!docs` and `!adrs` attach markdown to elements.
  - Weaknesses: stops at structure; no goal, requirement or rationale layer; identifiers are DSL-local.
- arc42 ([overview](https://arc42.org/overview)): 12 sections (introduction and goals, constraints, context and scope, solution strategy, building block view, runtime view, deployment view, crosscutting concepts, architectural decisions, quality requirements, risks and technical debt, glossary). Sections 1, 4, 5, 9, 10 should cross-link but arc42 gives no mechanism; AsciiDoc anchors and docToolchain are the usual answer. arc42 maps some sections onto C4 diagrams.
- ISO/IEC/IEEE 42010:2022 ([conceptual model](http://www.iso-architecture.org/42010/cm/), [ISO page](https://www.iso.org/standard/74393.html), [INCOSE update](https://www.omgwiki.org/MBSE/lib/exe/fetch.php?media=mbse%3Aincose_mbse_iw_2022%3Aiw2022_iso_iec_ieee_42010_update.pdf)): viewpoints built from model kinds; *correspondences* are named relations between AD elements; *correspondence rules* govern them within or between architecture descriptions. Listed kinds: equivalence, composition, refinement, consistency, traceability, dependency, constraint, satisfaction, obligation. Not text-level, but a defensible taxonomy to name link types after.
- Views and Beyond (SEI, Clements et al., [book](https://books.google.com/books/about/Documenting_Software_Architectures.html?id=ASc9HYPkr4sC)): viewtypes (module, component-and-connector, allocation), plus an explicit "mapping between views" section and rationale. Prose, no IDs.
- Design docs and RFCs ([Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/), [Oxide RFD 1](https://rfd.shared.oxide.computer/rfd/0001), [Oxide blog](https://oxide.computer/blog/a-tool-for-discussion), [Pragmatic Engineer survey](https://blog.pragmaticengineer.com/rfcs-and-design-docs/), [Rust RFCs](https://github.com/rust-lang/rfcs)): context, goals and non-goals, design, alternatives considered, cross-cutting concerns; numbered documents with a state (draft, discussion, published, abandoned). Oxide keeps RFDs as AsciiDoc in git, one directory per number, discussed in PRs. Links are prose hyperlinks; nothing is checked.

## D. Plain-text requirements traceability tooling

### Doorstop

- Sources: [repo](https://github.com/doorstop-dev/doorstop), [item reference](https://github.com/doorstop-dev/doorstop/blob/develop/docs/reference/item.md), [validation](https://github.com/doorstop-dev/doorstop/blob/develop/docs/cli/validation.md).
- One YAML file per item; filename is the UID; UID is `PREFIX + separator + number` (REQ001, REQ-001) or a custom name. Fields: `active`, `normative`, `derived`, `level`, `header`, `text` (markdown), `links`, `references`, `reviewed` (SHA-256 fingerprint).
- Links point upward only, to parents, each optionally with the parent's fingerprint:

```yaml
links:
- REQ001: avwblqPimDJ2OgTrRCXxRPN8FQhUBWqPIXm7kSR95C4=
```

- A parent change makes the link *suspect* until `doorstop clear` re-accepts it. Documents form a tree via `.doorstop.yml` naming the parent document prefix. Child links are derived, never written.
- Validation: errors for unknown UIDs, inactive parents, missing external references; warnings for non-derived normative items with no links, links to non-normative items, self links, cycles, suspect links, unreviewed changes, missing child-document links. `--strict-child-check` available.
- Weaknesses: file-per-item is noisy for a design document; numeric UIDs carry no meaning; only parent/child semantics.

### StrictDoc

- Source: [user guide](https://strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_01_user_guide.html), [DO-178C tool requirements trace](https://strictdoc.readthedocs.io/en/stable/stable/docs_extra/DO178_requirements-TRACE.html).
- Own `.sdoc` grammar:

```
[REQUIREMENT]
UID: REQ-001
STATEMENT: >>>
See [LINK: REQ-002].
<<<
RELATIONS:
- TYPE: Parent
  VALUE: SYS-001
  ROLE: Refines
```

- Relation roles are declared once in a `[GRAMMAR]` block with `ROLE` and `REVERSE_ROLE`, so the reverse direction is computed. `[DOCUMENT_FROM_FILE]` composes documents. `[ANCHOR: x]` / `[LINK: #x]` for in-text anchors. Source files linked with `TYPE: File` relations and in-code markers (function or range scope).
- Validation: dangling parent UIDs, cycles, duplicate UIDs; links display only if both ends have UIDs. Exports: HTML with traceability screens, traceability matrix, ReqIF import/export.
- Weaknesses: its own syntax rather than markdown (markdown/RST allowed inside multiline fields); aimed at safety-standard projects; Python web server.

### Sphinx-Needs

- Sources: [need directive](https://sphinx-needs.readthedocs.io/en/latest/directives/need.html), [configuration](https://sphinx-needs.readthedocs.io/en/latest/configuration.html), [needimport](https://sphinx-needs.readthedocs.io/en/latest/directives/needimport.html), [dead links issue](https://github.com/useblocks/sphinx-needs/issues/116), [ID namespaces discussion](https://github.com/useblocks/sphinx-needs/discussions/1088).
- RST or MyST directives: `.. req:: Title` with `:id: REQ_001` and `:links: REQ_002; REQ_003`. Custom typed links are declared once in `needs_extra_links` with `outgoing` and `incoming` names ("tests" / "is tested by") and become directive options; the reverse list is rendered automatically. `needs_id_regex` and `needs_id_required` enforce ID shape. Conditional links `REQ_001[status=="open"]` since 8.0.
- Validation: a link to a missing ID warns "outgoing linked need X not found", which fails a `-W` build unless `allow_dead_links` is set. `needs_warnings` lets you write custom coverage rules as filter expressions (every req must have a test, etc.). Every build exports `needs.json`.
- Composition across projects is the strongest of any tool here: `needs_external_needs` takes `base_url`, `json_url`, `id_prefix`, `css_class`, so another project's needs are linkable read-only under a namespace prefix; `needimport` copies needs in from a `needs.json` with `:id_prefix:` and `:version:`.
- Weaknesses: Sphinx build weight, RST/MyST rather than plain markdown, configuration volume.

### OpenFastTrace (OFT)

- Sources: [user guide](https://github.com/itsallcode/openfasttrace/blob/develop/doc/user_guide.md), [OFT's own system requirements in its format](https://github.com/itsallcode/openfasttrace/blob/main/doc/spec/system_requirements.md), [design doc](https://github.com/itsallcode/openfasttrace/blob/main/doc/spec/design.md).
- Markdown-native. An item is a heading followed by an ID `type~slug~revision` in backticks, a `Needs:` line naming the artifact types that must cover it, and a `Covers:` list of upstream IDs:

```markdown
### Store settings
`dsn~store-settings~2`
Covers:
* `req~persist-settings~1`
Needs: impl, utest
```

- Code carries tags `[impl->dsn~store-settings~2]`; `>>` forwards coverage to further types (`[impl->req~x~1>>utest,itest]`). Artifact types are arbitrary strings, so a chain purpose -> principle -> behavior -> design -> impl is just a `Needs:` chain.
- Report: uncovered items, outdated coverage (revision mismatch), orphaned coverage (target missing), duplicate IDs, unwanted coverage (a type the item does not need). Works across arbitrarily many markdown and source files.
- Weaknesses: single relation semantics ("covers"); revisions bumped by hand; Java runtime.

### ReqIF, Jama, Capella

- ReqIF is an OMG XML exchange format (SpecObjects, SpecRelations, SpecTypes), not an authoring format. Supported by StrictDoc, Jama ([Jama Interchange for ReqIF](https://www.jamasoftware.com/datasheet/jama-connect-interchange-for-reqif/)), Capella's requirements viewpoint ([capella-requirements-vp](https://github.com/eclipse-capella/capella-requirements-vp)).
- Jama Connect exports Word, Excel, ReqIF ([export docs](https://help.jamasoftware.com/ah/en/getting-to-know-jama-connect-features/exporting-documents-from-jama-connect.html)); I found no native markdown export. Item IDs are project-key plus set-key plus number style.
- Capella stores `.capella`/`.aird` XML with a git adapter that declares them text. The text route is [py-capellambse](https://github.com/dbinfrago/py-capellambse), whose declarative YAML modelling language (since 0.5) describes model changes against the semantic model; [capella2polarion](https://capella-polarion.readthedocs.io/en/latest/configuration/sync.html) uses YAML to configure sync. Component *ports* and exchanges are how Arcadia composes components, but they live in the XML model. I could not find any public Elektrobit Capella YAML export.

### Lighter requirements-as-code tools

- [SARA](https://github.com/cledouarec/sara) ([write-up](https://dev.to/tumf/sara-a-cli-tool-for-managing-markdown-requirements-with-knowledge-graphs-nco)): markdown files with YAML front matter `id`, `type`, `name`, and typed relations `refines`/`is_refined_by`, `derives_from`/`derives`, `satisfies`/`is_satisfied_by`, `depends_on`/`is_required_by`; reverse links inferred; validates broken references, orphans (no upstream parent) and cycles; multi-repo aggregation via `sara.toml`. Rust, Apache-2.0. Closest existing thing to the target format.
- [ReqToCode / Ariadne](https://arxiv.org/html/2603.13999): each requirement ID becomes a language-level constant (`SWR_101_VALIDATE_SENSOR_RANGE_ON_INPUT`) referenced via `@TracesSWR(...)` / `@VerifiesSWR(...)`, so the compiler catches dangling references; bidirectional change detection by comparing requirement timestamps with commit history. Java, C, C++.
- [rmtoo](https://github.com/florath/rmtoo) (text/YAML requirements as a directed graph, LaTeX/HTML/graph outputs), [reqstool](https://deepwiki.com/reqstool/reqstool-client) (YAML requirements, implementation and verification links, compliance reports), [git-reqs](https://github.com/niradynamics/git-reqs) (YAML plus networkx), [shtracer](https://github.com/qq3g7bad/shtracer) (POSIX shell traceability matrix from markdown tags), [reqtrace](https://github.com/wonkodv/reqtrace), [traceability-tool](https://github.com/konstantin-hatvan/traceability-tool), [Reqflow](https://goeb.github.io/reqflow/). Comparison of rmtoo/Doorstop/StrictDoc: [Pi Stack](https://www.pistack.xyz/posts/2026-06-15-self-hosted-requirements-management-rmtoo-doorstop-strictdoc/). RTEMS documents its own Doorstop-based tooling ([RTEMS req tooling](https://docs.rtems.org/docs/main/eng/req/tooling.html)).

## E. Wiki-link and knowledge-graph approaches

- Obsidian: `[[note]]`, `[[note#heading]]`, `[[note^block]]`, `[[note|alias]]`; links resolve by filename; unresolved links are surfaced as "dangling"; Dataview queries can list orphans ([finding orphans](https://www.cgoodman.com/blog/2025-05-05-obsidian-orphans/)). Dataview inline fields `key:: value` (or `[key:: value]` inline) add typed metadata.
- [Breadcrumbs](https://github.com/SkepticMystic/breadcrumbs): typed directional edges (up/down/same/next/prev plus custom) read from frontmatter, `up:: [[note]]` inline fields, lists, tags, folders, or Dendron-style names; user-defined hierarchies; *implied edges* (if A is up from B then B is down from A). [Juggl](https://juggl.io/link-types.html) renders typed edges from `type:: [[link]]` and integrates with Breadcrumbs ([integration](https://juggl.io/features/breadcrumbs-integration.html)).
- Logseq: block-level outliner, `key:: value` properties, `((block-id))` references; property syntax does not round-trip to Obsidian ([comparison](https://itsfoss.com/comparison/obsidian-vs-logseq/)). Neither tool builds typed knowledge graphs natively.
- [Dendron](https://wiki.dendron.so/notes/c5e5adde-5459-409b-b34d-a0d75cbb1052/): hierarchy encoded in note names (`cli.cmd.deploy`), validated against schema YAML (`id`, `parent`, `children`, `pattern`, `namespace`, `template`); unmatched notes flagged; cross-vault links `[[dendron://vault/note]]`.
- Semantic MediaWiki ([properties](https://www.semantic-mediawiki.org/wiki/Help:Properties_and_types), [RDF](https://www.semantic-mediawiki.org/wiki/RDF)): `[[Has property::value]]` typed links, queryable with `#ask`, exportable as RDF. The longest-lived typed-link syntax in a wiki and the origin of the `::` convention.
- [Markdown-LD](https://github.com/ozekik/markdown-ld/blob/master/SPEC.md): heading levels map to graph name, subject, predicate; list items are objects; Turtle terms in inline code. [Semantic Markdown](https://hackmd.io/@sparna/semantic-markdown-v0) (Sparna, V0): attribute annotations `{.foaf:Person}` (type), `{foaf:name}` (property), `{=wdt:Q42}` (subject URI); no tooling.
- Weaknesses across the group: IDs are filenames (renames break links unless the app rewrites them), typed-link syntax is plugin-specific, no CI-grade checker for typed links or cross-vault references.

## F. Spec-driven development for AI coding agents (2025-2026)

- GitHub Spec Kit ([repo](https://github.com/github/spec-kit), [methodology](https://github.com/github/spec-kit/blob/main/spec-driven.md), [spec template](https://github.com/github/spec-kit/blob/main/templates/spec-template.md), [Microsoft blog](https://developer.microsoft.com/blog/spec-driven-development-spec-kit/)): constitution (immutable project principles), then per feature `specs/001-name/` holding spec.md, plan.md, research.md, data-model.md, contracts/, tasks.md. IDs: `FR-001` functional requirements, `SC-001` success criteria, numbered user stories with P1..P3 priority, `[NEEDS CLARIFICATION: ...]` markers, `[P]` parallelisable tasks. Commands: constitution, specify, clarify, plan, tasks, analyze, implement. Cross-layer links are prose mentions of IDs; analyze checks consistency and constitution compliance.
- AWS Kiro ([feature specs](https://kiro.dev/docs/specs/feature-specs/), [design-first variant](https://kiro.dev/docs/specs/feature-specs/tech-design-first/)): requirements.md in EARS form ("WHEN ... THE SYSTEM SHALL ...") with hierarchical numbering (1.1, 2.3), design.md, tasks.md where each task ends with `_Requirements: 1.1, 2.3_`; steering files hold project-wide rules; an "analyze requirements" step between phases.
- OpenSpec ([repo](https://github.com/Fission-AI/OpenSpec), [explainer](https://codemyspec.com/blog/openspec-explained)): capability-scoped `openspec/specs/<capability>/spec.md` as the source of truth; `openspec/changes/<id>/` with proposal.md, design.md, tasks.md and delta specs marked ADDED / MODIFIED / REMOVED. Requirements are `### Requirement:` headings with `#### Scenario:` WHEN/THEN blocks (SHALL wording). Archiving merges deltas into the main specs; `openspec validate` checks structure, concreteness of scenarios and task correspondence. The only one with a system-level spec that changes are applied to.
- Tessl ([concepts](https://docs.tessl.io/introduction-to-tessl/concepts), [launch](https://tessl.io/blog/tessl-launches-spec-driven-framework-and-registry), [SDD tile](https://github.com/tesslio/spec-driven-development-tile)): `.spec.md` files with YAML frontmatter; directives `@generate` (code from spec), `@describe` (spec from code), `@use` (import another spec), `@test` (bind a capability sentence to a test file); links to generated code and test files by path. Registry of "tiles" (skills/methodologies).
- Others: BMAD, [Augment Intent](https://rywalker.com/research/augment-intent), Google Antigravity; landscape in [dev.to 2026 guide](https://dev.to/krlz/spec-driven-development-in-2026-what-it-is-the-tooling-and-how-teams-actually-use-it-2fk2) and [thebcms guide](https://www.thebcms.com/blog/spec-driven-development/); [agentic engineering field study](https://github.com/ianhxu/agentic-engineering-field-study/blob/main/04-spec-driven-development.md); [Structured spec-driven engineering paper](https://arxiv.org/pdf/2605.02455).
- Strengths: cheap, agent-neutral, in-repo, lower layers regenerated from upper ones; a Feb 2026 arXiv result reports human-refined specs cut LLM code errors by up to about half.
- Weaknesses: drift is the dominant complaint. A Kiro user quoted in [Kiro vs OpenSpec](https://codemyspec.com/blog/kiro-vs-openspec): "it just keeps drifting and drifting until you have duplication and contradictions across specs". [The prose-spec drift trap, reborn](https://dev.to/tmfrisinger/spec-driven-development-is-the-prose-spec-drift-trap-reborn-4p99) argues a natural-language spec's relation to code is opaque to every tool; [SDD headed toward its death](https://medium.com/codetodeploy/spec-driven-development-is-headed-toward-its-death-and-i-watched-the-best-defense-of-it-1f37b49a5c91); Thoughtworks keeps SDD at Assess. Secondary: per-feature folders (Spec Kit, Kiro) have no system-level view; IDs are local to one document; no tool checks a dangling `FR-007` reference; no typed links between layers.

## G. Naming collisions for "intent specification"

- Leveson's original: [Intent Specifications (TSE)](http://sunnyday.mit.edu/papers/intent-tse.pdf), [NASA final report](https://ntrs.nasa.gov/api/citations/19990089302/downloads/19990089302.pdf), [reusable specification components](http://sunnyday.mit.edu/papers/incose.pdf); seven levels, SpecTRM-RL at the blackbox level, hyperlinks up and down.
- Intent-Based Networking: [RFC 9315](https://datatracker.ietf.org/doc/rfc9315/) (IRTF NMRG, 2022, informational): intent = declarative operational goals and outcomes without the how; TM Forum Intent Ontology ([TIO-SHACL](https://arxiv.org/pdf/2604.27359)).
- LLM agents: "Intent Specification (ISpec)" as an agent constitution with objective, constraint, policy and verification layers in [Securing LLM Agents Need Intent-to-Execution Integrity](https://arxiv.org/html/2605.16976); [Intent Formalization: a grand challenge](https://arxiv.org/html/2603.17150v1); [SpecBench: turning intent into specifications](https://arxiv.org/abs/2606.20585); [FASTRIC prompt specification language](https://arxiv.org/abs/2512.18940); [Auto-Intent](https://arxiv.org/html/2410.22552v1) for web agents.
- Industry: [intent-driven.dev](https://intent-driven.dev/) is a training site (Hari Krishnan, Polarizer) promoting OpenSpec; Augment Intent is a desktop product. Android "Intent" API is a trivial collision.
- I found no project literally named "IntentSpec". The name is free, but "intent spec" is now crowded with the agent-constitution meaning; qualifying it (e.g. "intent specification in the Leveson sense", or a distinct product name) will avoid confusion.

## Synthesis

### 1. Most proven ID and cross-reference conventions for plain-text, multi-file documents

Five patterns recur across every tool that actually validates links.

1. Stable, typed IDs independent of titles and filenames. Numeric form `REQ-001` (Doorstop, StrictDoc, Sphinx-Needs, Spec Kit) or type-plus-slug (`dsn~store-settings~2` in OFT, `SWR_101_VALIDATE_SENSOR_RANGE` in ReqToCode). The slug form survives renumbering and reads in prose. Putting the level in the prefix (`P-`, `G-`, `B-`, `D-`, `I-`, or `pur~`, `prn~`, `beh~`, `dsn~`, `impl~`) lets a checker verify that a link points to the level it should.
2. Declare each link type once with its inverse and write only one direction. Sphinx-Needs (outgoing/incoming), StrictDoc (ROLE/REVERSE_ROLE), Breadcrumbs (implied edges) and SARA all do this. Hand-written bidirectional links are where drift starts; the reverse view is generated.
3. Links live in structured metadata, not only in prose: YAML front matter (SARA, Doorstop), a `Covers:` line (OFT), directive options (Sphinx-Needs). Prose `[[links]]` can be allowed as extra, but the checker reads the metadata.
4. A change marker so downstream elements know an upstream changed: Doorstop's content fingerprint stored on the link, or OFT's revision number inside the ID. Without it, "suspect link" detection is impossible.
5. A small, closed vocabulary of link types. Recommended: one family per vertical direction (`serves` upward, `realized-by` downward, with generated inverses) plus a few lateral kinds named after ISO 42010 correspondence kinds and KAOS (`depends-on`, `conflicts-with`, `constrains`, `obstructs`/`resolves` if obstacles are modelled). Sphinx-Needs shows that arbitrary extra link types are fine as long as each is declared.

Concrete syntax with the most tool support: `[[ID]]` wikilinks (Obsidian, lychee, Breadcrumbs, Juggl all read them) combined with `key:: [[ID]]` or front-matter `key: [ID, ID]` for typing. Sphinx-Needs' `id_prefix` and Dendron's `vault/note` show a namespace separator (`sysname:ID` or `sysname/ID`) is enough for cross-document references.

### 2. Mechanisms that best support composing one system's spec as a component of a larger spec

All the working mechanisms share three parts: a namespace, a declared interface, and a stub in the consumer.

- GSN modules are the clearest model: elements marked public; *away* stubs in the consumer that cite `module.element` and cannot be edited locally; *contracts* when the support needs its own justification and context. SACM's ArgumentPackageInterface and ArgumentPackageBinding formalise the same shape, and Argevide's provided/required split maps directly to "goals this spec serves for its parent" versus "assumptions this spec requires from its environment" (which is also KAOS's requirement/expectation split and assume-guarantee contracts).
- Sphinx-Needs external needs are the text-tool equivalent: `id_prefix` namespace, `base_url`, and a read-only import of the other project's exported ID list (`needs.json`). SARA's `sara.toml` multi-repo aggregation is the lighter version.
- Dendron cross-vault links and Structurizr `!extends` plus a system catalog show that a namespace in the link syntax is enough for the checker; Structurizr also shows the failure mode (`!include` does not scale to an uber-workspace).
- OFT composes only vertically (artifact-type chain), and Capella composes via component ports, but only inside its XML model.
- Recommendation: each spec has an explicit interface section listing its public elements (provided: the goals/behaviors a parent may cite) and its required environment assumptions; a parent spec references a child element as `child-name:ID` and may only reference public ones; each spec exports a machine-readable ID list (a `needs.json` analogue) that the checker resolves against; a "contract" element type records when a child's element satisfies a parent's element under stated context.

### 3. Tools that could validate link integrity for a custom markdown format with least effort

In increasing order of effort and decreasing order of fit:

1. A short custom script (Python or a remark plugin) that parses front matter and inline `key:: [[ID]]` fields across the tree and reports unknown IDs, orphans (no upward link), uncovered items (no downward link where the level demands one), cycles, cross-level violations, and fingerprint/revision mismatches. Every tool surveyed with real checks is essentially this plus rendering; SARA already implements most of it and is the first thing to evaluate before writing one.
2. [lychee](https://lychee.cli.rs/recipes/wikilinks/) with `--include-wikilinks --base-url <dir> --fallback-extensions md` checks `[[id]]` links if each ID resolves to a file or anchor; [remark-validate-links](https://github.com/remarkjs/remark-validate-links) checks `[text](file.md#anchor)` offline. Neither knows link types, levels, or coverage, so they are a supplement, not the checker.
3. Adopting OFT's `type~slug~rev` syntax verbatim in the markdown gives uncovered, orphaned, outdated and duplicate reports with no code written, at the cost of a single "covers" semantics and a Java runtime.
4. Adopting Sphinx-Needs via MyST markdown gives typed links, generated reverse links, external-project composition, `needs_warnings` coverage rules and JSON export, at the cost of a Sphinx build and RST-flavoured directives.
5. Obsidian with Breadcrumbs, Dataview and Juggl is good for authoring and interactive graph inspection but not for CI.

Recommended path: custom front-matter checker (or SARA if its relation set can be adapted), plus lychee for prose wikilinks, plus an exported ID list per spec to support cross-spec references.
