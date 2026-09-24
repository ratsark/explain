# Architecture: the format and the tool

This document is the body; `spec/` is the index. Every section here is cited by
a row in explain's own spec (`python3 -m explain check spec`, `python3 -m explain
why S7 spec`), which is the format applied to itself.

Status: v0, 2026-09-12. Sections 1 through 8 and 11 were reviewed with the user
on 2026-09-12 (unique prefixes, hybrid links, file structure, relation to the
standard docs). Research behind it: `research/00-SYNTHESIS.md`. Prior art it
must respect: the first deploying project's existing intent hierarchy and the
lessons it recorded, summarised in section 10. That project is private; its
integration notes live in its own repo, and nothing specific to it is here.

## 1. What a spec is

A **spec** describes one system as a means-ends hierarchy. It is one directory.
Levels are subdirectories or files of that directory. Items are markdown
headings or list items inside those files. Every item has a stable id, optional
header fields, and a prose body. Every link is typed, and the tool reads links
from headers and from prose alike, so the graph never depends on where an
author chose to put a link.

A spec can name **parent specs** (systems it is a component of) and **child
specs** (its components). Cross-spec references carry the other spec's name as a
namespace. Parents and children may live anywhere: another directory, another
repo, or only as an exported index file.

The level set is not fixed. A **profile** declares the levels, the item kinds
allowed at each, and the optional sections each level may grow. A spec names its
profile in its manifest. The first profile is `software`; a business-proposition
profile is planned.

## 2. Directory layout

```
<spec-root>/
  spec.yaml                 manifest (section 3)
  L0-purpose.md             a level as a single file...
  L1-principles.md
  L2-architecture/          ...or as a directory of files
    00-components.md
    fire-charter.md
    surfaces/
      surface-doctrine.md
  L3-specs/
    countdown.md
  L4-realization.md         mostly pointers into code and tests
  README.md                 ignored by the tool (no L-prefix)
```

Rules:

- A top-level entry named `L<n>-<name>.md` or `L<n>-<name>/` belongs to level n.
  Everything under a level directory is at that level, however deep. The level of
  an item is therefore known from its path. This is what lets the tool detect
  skip-level links, which the first project's earlier index tool could not.
- Anything without an `L<n>-` prefix at the top level is not part of the spec
  and is ignored. Levels may be absent; a spec with only `L0-purpose.md` is
  valid.

### Files within a level

The tool reads a level as if all its files were one document. Ids are global,
nothing references a file path, so file placement is purely for human
navigation. The organizing principle is part-whole decomposition (Leveson's
third axis): one file per component, subsystem, or topic, or one file per
profile section (goals, constraints, environment). Subdirectories inside a level
group files further and carry no other meaning.

- A level starts as one file and becomes a directory when it grows:
  `git mv L0-purpose.md L0-purpose/00-goals.md`, then split. No link changes.
- Files and directories sort by name in `outline`; an optional numeric prefix
  controls order.
- A file's first heading without an id is its title. Headings without ids are
  section headings and never items.
- Moving an item between files inside a level changes nothing in the graph.
  Moving it between levels is a level move and re-prefixes its id (section 4).

## 3. The manifest: `spec.yaml`

```yaml
name: cas                      # namespace used by other specs to cite this one
title: Collision avoidance system
profile: software              # which level set and kind vocabulary applies
adopted-through: L1            # review flow: levels the owner has signed off
parents:
  aircraft:                    # the name the parent calls itself
    path: ../aircraft          # optional: resolve live from a local checkout
    index: parents/aircraft.index.json   # or: a committed snapshot
children:
  - path: ../display           # optional; lets the parent build its allocation view
root: G0                       # optional: the mission; every other top-level goal is taken to serve it
```

`root:` names the item at the top level that everything else at that level of
the same kind serves: the mission. With it declared, a goal needs no
`serves: G0` line (the tool adds an implied link, shown as such), an explicit
one draws no same-level report, and the mission is never reported unserved
or isolated.

Parents and children are both optional. A child that names a parent by index
file only is loosely coupled: the parent can be in another repo or another
version-control system, and the child commits a snapshot of the parent's ids.
The tool reports when the snapshot is older than the parent's live export, if
both are reachable.

## 4. Items

An item is either a heading or a list item whose text starts with an id, then a
separator (an em dash, hyphen, or colon), then a title.

```markdown
## G2 — Avoid collision with other aircraft
status: adopted
source: certification basis, 2026-09-01

In all meteorological conditions, with or without ground control. The
protected volume and the advisory logic are L1 mechanisms [[serves G1]],
each replaceable.

- G2.1 — Detect: track every transponder-equipped aircraft in range
- G2.2 — Resolve: advise the crew of an escape manoeuvre [[depends-on C1]]
  - G2.2.1 — Coordinate: two equipped aircraft choose complementary senses
- G2.3 — Display: show nearby traffic to the crew
```

Rules:

- **Heading items** may carry a header and a body. The heading depth (`##`,
  `###`) is free; structure comes from ids.
- **Bullet items** carry a title, inline prose, and inline links only. Nested
  bullets are nested refinement. This is how sub-goals stay compact.
- The **header** is the contiguous run of `key: value` lines directly under a
  heading item (a blank line or any other line ends it). It is optional. No
  fence. Keys come from the closed vocabulary in section 5.
- The **body** is everything after the header until the next item at the same
  or shallower depth, or the next heading.
- **Editorial matter is separable.** A body paragraph whose first line starts
  with `Editorial:`, `History:`, `Provenance:`, `Note:` or `Transcription:` is
  editorial: it stays in the file for editors, but `show` and `review` leave
  it out (`show --editorial` prints it) and the fingerprint ignores it, so a
  change to provenance never makes dependants suspect. Inside a level
  directory, `README.md`, `NOTES.md`, `HISTORY.md` and `*.notes.md` are
  skipped entirely: the place for file-level editorial matter. Prose before
  the first item of a spec file is not part of any item and is never rendered.
  The line between the two: a reason that justifies the item as it stands
  ("means-free, so that the art style can change without touching the goal")
  is design, because a reader applying the item needs it to interpret it.
  History ("this used to be G5"), form choices ("written as a requirement
  rather than a constraint because...") and process caveats matter only when
  changing the item, and are editorial.
- **Links are typed wherever they appear, and placement carries no meaning.**
  `serves: G2` in a header and `[[serves G2]]` in a sentence are the same edge.
  Put a link in the header when it applies to the whole item; put it inline
  when it belongs to one sentence. Untyped `[[G2]]` is a mention: checked for
  existence, never an edge. Bare `G2` in prose is plain text.

### Ids

An id is a **kind letter** and a number, with optional dotted refinement:
`G2`, `C1`, `P10`, `G6.2`, `D3.1.4`.

- Kind letters are declared by the profile and are unique across the spec, so a
  kind implies a level and `G2` never needs qualifying. This is the rule the
  first project adopted after an id collision between two levels, made
  structural.
- **Free kinds.** A kind that legitimately exists at every level is declared
  under `free-kinds` in the profile: verification, assumptions, limitations,
  hazards and evaluation criteria in the shipped profile (Leveson's environment
  and verification columns exist at every level). Its numbers are unique per
  kind across the spec like any other, its level comes from the path, and it
  needs no level prefix; a written prefix (`L4-V3`) is checked against the
  path. Every other kind is fixed to one level.
- Ids are immutable within a level. A level move re-prefixes (a goal demoted
  to a principle goes from `G5` to `P5`). A `was:` field lets stray references
  resolve.
- **Dotted ids are refinement, not means-ends.** `G6.2` is a more detailed part
  of `G6` at the same level. It needs no `serves:` line; the tool infers
  containment. Splitting a level into files is decomposition, also within a
  level.
- Numbers need not be dense or ordered. `P10` may be proposed before `P8` is
  adopted.
- Slug ids (`G-safety`) are not in v0. Numeric ids are what the first project
  already cites, and `show` answers "what is G2" instantly. A `slug:` alias
  field can come later.

### Cross-spec ids

`<spec-name>:<id>`, for example `aircraft:D1`. The spec name comes from the
target's manifest and must be declared under `parents:` or `children:` in the
citing spec's manifest.

## 5. Link types and header fields

The closed vocabulary. Unknown keys and unknown inline relation names are
errors, so a typo cannot silently create a relation nobody reads.

Relations (valid in a header and inline as `[[<relation> <id>]]`):

| Relation | Meaning | Direction |
|---|---|---|
| `serves` | The ends this item exists for. The means-ends link. Targets should be one level up; may be cross-spec. | up |
| `assumes` | Assumption items (kind `A`) this item rests on. | lateral |
| `discharged-by` | On an assumption: the item (usually in a parent or sibling spec) that guarantees it. | up or lateral |
| `verifies` | On a verification item: the items it checks. Any level. | up |
| `depends-on` | Needs this other item to exist or hold; not a purpose relation. | lateral |
| `conflicts-with` | Recorded tension; the body says how it is reconciled. | lateral |
| `supersedes` | This item replaces that one. The target should carry `status: superseded`. | lateral |

Header-only fields:

| Field | Meaning |
|---|---|
| `status` | `draft`, `proposed`, `adopted`, `superseded`, `rejected`. |
| `built` | `unbuilt`, `building`, `shipped`, `removed`: the realization's state, separate from the decision's. Changes what `unserved` means (section 9). |
| `derived` | `true` when an item deliberately has no `serves:` (a decision with no higher purpose, allowed and marked, per Leveson). |
| `owner` | Free text: who maintains this item. |
| `was` | Previous ids of this item after a level move or renumber. |
| `source` | Free text or path: where the body's authority comes from. |
| `refs` | Paths into code, tests, docs. Checked for existence only. |
| `aka` | Other names this item is cited by, e.g. `law 16`; unique across the spec; `show`, `why`, `serves` resolve them. Lets a legacy numbering survive as aliases when items move to the level their content has. |
| `component` | `true` to declare an item a component: its dotted sub-items are inside it, and other items may declare `part-of` it (section 13). |
| `part-of` | The component this item belongs to. Items with no component are cross-cutting. |
| `interface` | `true` on the items that are a component's published surface: the only things inside it another component may link to. |
| `hides` | The design decision this component encapsulates, one line (Parnas's secret). Declares the item a component. |
| `until` | The condition under which this item stops serving its end, one line. A means-ends link is valid only while it holds; `review` prints it beside the links. |

Inverses are never written. `served-by`, `assumed-by`, `verified-by`, and
`depended-on-by` are computed. Hand-written bidirectional links are where every
surveyed format started drifting.

Header values are a single id or a list: `serves: G2` or
`serves: [G2, G3, biz:G1]`. Inline links take one id each.

## 6. Levels and adjacency

Adjacent-level `serves:` links are the goal, not a hard rule. The tool reports a
skip link as a **warning** with the suggestion that a middle item is waiting to
be named. Nobody is blocked from finishing a document because the intermediate
level is missing. A `serves:` that points downward is an error.

At L1 and below, an item with no `serves` and no `derived: true` is an
**orphan** warning. L0 items need no `serves` unless the spec has a parent, in
which case a top-level item that serves nothing in the parent is a warning
labelled "derived from the parent's point of view", which is the ARP4754A rule.

## 7. Profiles

A profile is a YAML file shipped with the tool (or placed in the spec root as
`profile.yaml` to override). It declares levels, kinds, and the optional section
tree per level:

```yaml
name: software
free-kinds:                  # allowed at any level; a written L<n>- prefix is checked
  V: verification
  A: assumption              # a world-fact this level's items rely on
  X: limitation              # an accepted gap ("L" is reserved for level prefixes)
  H: hazard                  # a named risk with a measurement
  E: evaluation criterion
  Q: open question           # proposed until an answer item supersedes it
levels:
  - n: 0
    name: purpose
    kinds:
      G: goal
      C: constraint          # pass/fail; never traded for goal progress
      R: requirement
    sections:                # the optional heading tree; elided until used
      - Mission
      - Goals
      - Constraints
      - Environment:
          - Assumptions
          - External constraints
      - Users and operators
      - Limitations
      - Risks:
          - Hazards
          - Safety constraints
          - Security threats
      - Evaluation criteria and priorities
      - Verification
  - n: 1
    name: principles
    kinds: {P: principle}
    sections: [Principles, Budgets, Never-list, Verification]
  - n: 2
    name: architecture
    kinds: {D: design element}      # charters, doctrines, components, interfaces, behaviors
    sections: [Components, Interfaces, Behaviors, Charters and doctrines, Environment models, Operator tasks, Verification]
  - n: 3
    name: specs
    kinds: {S: spec}                # rulings, detailed specs, ADRs, acceptance criteria
    sections: [Rulings, Specs, Decisions, Acceptance criteria, Verification]
  - n: 4
    name: realization
    kinds: {I: implementation}      # code pointers
    sections: [Code, Guards, Tests, Operations]
```

These are the first deploying project's five levels under generic names: its
"charters and doctrines" are design elements, its "rulings and specs" are
specs, its "code and guards" are realization plus `L4-V` items. Directory
names can be a project's own (`L2-charters/`); the tool keys on the `L<n>-`
prefix only.

Sections are the answer to Leveson's four columns (environment, operator,
system, verification at every level). They become optional standard sections
per level, declared once in the profile and present in a document only when
they have content. The environment column is the `A` kind plus the Environment
section; the operator column is Users and operators; verification is the
per-level `V` kind and the `verifies` link. `outline` lists which profile
sections a level has not yet filled in, which is what "elided until it comes
up" needs to stay honest.

A second shipped profile, `business` (2026-09-13), keeps the same kind letters
and renames the levels for a venture and the product that realizes it:
purpose (mission, market thesis, goals, constraints, requirements, customers
and market), strategy (principles, positioning, never-list), model (offer,
channels, pricing, product definition, components, interfaces, partners),
plans (decisions, milestones, policies) and execution (initiatives, metrics
and experiments, operations). The Leveson seven-level set may follow as
documentation of the mapping.

## 8. Nesting

A child spec declares its parent in `spec.yaml`. Then:

- The child's L0 items that exist because of the parent carry
  `serves: parent:ID`. That is the downward projection: the parent's design
  element becomes the child's purpose.
- The child's assumptions about its environment are `A` items. Each carries
  `discharged-by: parent:ID` or `discharged-by: sibling:ID` when something
  guarantees it. An assumption with no discharger is a warning: an obligation
  nobody has accepted.
- Child L0 items with no parent target are reported as derived. The parent
  acknowledges them by citing them (`depends-on: child:G4`) or the child marks
  `derived: true` with a body that says why.
- The parent runs `explain allocations` to see, per parent item, which child
  items serve it, across all declared children. Generated, never hand-written.
- A child may be declared by `path` (a directory with `spec.yaml`) or by
  `index` (the JSON that `export` emits: `items` with fingerprints, `links`
  with `from`, `relation`, `to` and, where the child has accepted the link, an
  `accepted` fingerprint). A generated index is the natural form for a child
  whose items are test files or review-rule sections: nobody hand-writes a
  spec mirroring nine hundred tests. Once declared, the child's links into
  this spec join the re-evaluation sweep (`serves` lists them under "in
  children") and drift (`drift` and `check` report a child link whose target
  row moved since the child accepted it, as `child-link-suspect`; the re-read
  and the acceptance happen in the child).

The contract between parent and child is exactly: the parent's exported index,
the child's `serves` links into it, and the child's `A` items with dischargers.
No third document. When the two sides are owned by different groups, the child
commits the parent's index snapshot and the tool reports staleness.

## 9. The tool

One command, Python 3 standard library only, one file or a small package so it
can be copied into any repo's `tools/`. The tool and the project are named
`explain` (chosen 2026-09-12). Design stance inherited from the first project's earlier index tool: dumb and greppable
over clever, and never silently incomplete. Every pattern it matches is printed
by `--patterns`; every known miss is declared.

Header lines and manifests are parsed as a strict, documented YAML subset
(scalars, flow lists, block lists, one level of nesting for the manifest)
rather than by PyYAML, to keep the tool dependency-free.

Commands, v0:

| Command | Answers |
|---|---|
| `explain init NAME [DIR] --profile P` | Scaffold a new spec: manifest, one file per level with the profile's sections, a README stub. |
| `explain check [path]` | All errors and reports for a spec, with file and line. Exit 1 on errors, 0 otherwise; `--strict` promotes reports. |
| `explain covers PATH[:LINE] [path]` | Which rows and child items name a source file (refs, `spec:` citations in the file, child indexes), narrowed to the nearest citation when a line is given, and each row's chain to the top. |
| `explain scan DIR [path]` | A child index built from `spec:`/`spec-guard:` citations in source files under DIR (`-o FILE` writes it; `FILE --accept` refreshes one file's citation fingerprints). |
| `explain orphans --suggested [path]` | Rows carrying "Suggested parent (unrecorded in source): X" as a promotable list; promoting one means writing `serves: X` into its header. |
| `explain show ID` | "What is G2": heading, header, body (design paragraphs), location, computed inverses. `--editorial` adds the editorial paragraphs. |
| `explain serves ID` | Everything downstream via every relation, transitively, here and in declared children: the re-evaluation sweep (what to re-read if ID changes). `how` is the means-ends tree; `serves` is the blast radius. |
| `explain why ID` | The upward tree from ID to the top: what it exists for. |
| `explain how ID` | The downward tree from ID: what serves it, recursively, with refinements shown as parts. The mirror of `why`. |
| `explain orphans` | Items at L1+ with no `serves` and no `derived`. |
| `explain isolated` | Items with no link in either direction, by level. The settlement measure that only falls: it cannot be moved by trading one report class for another. |
| `explain questions` | Open questions (kind `Q`) by level, what each blocks (`depends-on` it), and which answers superseded the rest. |
| `explain outline` | Levels, files, items, one line each; profile sections not yet present. |
| `explain export` | The spec's index JSON for other specs to cite. |
| `explain allocations` | Parent view: per item, the child items that serve it. |
| `explain assumptions` | Every `A` item and what discharges it. |
| `explain allocations` | The parent's view: for each item here, the child items (from `children:` in the manifest) that serve it; the child assumptions this spec discharges; design elements no child serves yet. |
| `explain accept ID... \| --all` | Record that the links from these items were read against their targets as they are now (section 12). |
| `explain drift` | Accepted links whose targets changed since: what to re-read, grouped by changed target. |
| `explain review [L1]` | Walk a level item by item: status, links with target titles, flags, body. No level: status counts per level against `adopted-through`. |
| `explain coupling` | Components: cohesion, links between them, cycles, boundary crossings, cross-cutting and overdetermined items (section 13). |
| `explain interfaces [D201]` | A component's guarantees (interface items and who outside depends on them) and requirements (its assumptions and what discharges them). |

Checks, v0, in two classes and no third (MISSION_STATEMENT.md):

- **Errors** mean the graph is malformed and cannot be trusted. They fail
  `check`. Duplicate id; kind not allowed at this level; a level prefix
  disagreeing with the path; unknown id in any
  relation; unknown spec namespace; unknown header key or inline relation name;
  malformed header line; `serves` pointing downward; a refinement (`G6.2`)
  whose parent (`G6`) is not defined; a malformed line in `accepted-links.txt`;
  a `part-of` that points at an undefined item, at itself, or closes a cycle.
- **Reports** mean the graph is incomplete. They never fail `check`; they are
  the to-do list, and a goal added today is expected to have nothing under it.
  Orphan (L1+ item serving nothing, not marked derived); unserved (an item
  nothing serves and whose build state is unstated); unrealized (shipped, but
  no implementation row serves it) and unguarded (shipped, but nothing
  verifies it), which replace unserved once `built:` is stated, while unbuilt
  and building rows are counted as the roadmap rather than reported one by
  one; skip-level link; same-level `serves` between items of the
  same kind (a constraint serving a goal at L0 is fine); unresolved `[[ID]]`
  mention; undischarged assumption; `refs` path missing (an external pointer,
  not part of the graph); profile section not yet present; a declared parent
  or child that cannot be resolved; a committed parent index snapshot that
  differs from the live parent; `supersedes` target not marked superseded;
  a suspect link (its target changed since the link was accepted, section
  12); links never accepted, as one count; a boundary crossing, a component
  cycle, an interface item outside any component (section 13); a profile
  section that holds prose but no items (prose outside an item has no
  fingerprint). `--strict` promotes reports to
  errors for anyone who wants a release gate.

`status: draft` versus `adopted`, and the manifest's `adopted-through`, let a
reader tell an expected gap from an overdue one. The `check` summary line
also prints the isolated count (items with no link in either direction) and
the build-state counts; the isolated count is the honest measure of
settlement progress, because naming a distant true parent retires an orphan
but adds a skip-level report, so report totals barely move while the graph
genuinely improves.

Later, not v0: HTML rendering.

## 10. Lessons from the first deployment carried into the design

The first project to adopt the format had run a hand-rolled intent hierarchy
for weeks before this tool existed, and had written down what went wrong.
Each lesson below became a rule.

- Ids collided when one letter was used at two levels. Kind letters are unique
  per spec by profile rule; per-level kinds carry the level prefix; the tool
  errors on a kind at the wrong level.
- Skip links could not be detected because an item's level was not in the data.
  Level now comes from the path.
- Bare ids in prose were ambiguous with sim-guard names. Only typed links are
  edges; `[[ID]]` is a checked mention; bare text is text.
- Two copies of a law drifted. Bodies live in one place; a registry row points
  at a body via `refs` and `source`.
- A means got reified as an end because the real end was unrecorded. Orphan
  and derived reporting exist for this.
- "Keep it dumb and greppable" and "v1 may be incomplete but never silently
  incomplete" are adopted verbatim.

## 11. Relation to the standard project documents

The five standard documents (operating norms) map onto the hierarchy, with one
exception, and the end state is that the spec *is* those documents rather than
a parallel copy of them (the first project's own constraint: nothing left
standing that nothing reaches).

| Document | Becomes |
|---|---|
| MISSION_STATEMENT.md | The L0 Mission section. |
| REQUIREMENTS.md (numbered `R` items) | L0 goals and constraints, as `R` items or re-homed as `G` and `C`. |
| ARCHITECTURE.md | L2; its numbered key decisions are L3 material. |
| DEVELOPMENT.md | L4 and operations. |
| PLAN.md | Stays separate. It is Leveson's Level 0, program management: plans and status, orthogonal to the means-ends stack. Phases cite item ids. |
| README.md | Stays. An external view. |

Transition mechanics: ARCHITECTURE.md becomes a symlink or a one-line pointer
to `L2-architecture/`; the norm that mission wording needs explicit approval
becomes the rule that L0 items need `status: adopted` from the owner, the same
rule at finer grain. Changing the operating norms themselves is the user's
decision. This project will dogfood the format on itself (PLAN.md, Phase 5).

## 12. Drift: fingerprints and accepted links

The format cannot stop an item's wording from changing meaning while its
links stay intact. What it can do is notice that the wording changed and name
exactly what to re-read. This is Doorstop's mechanism, adapted.

- Every item has a **fingerprint**: a short hash of its title and body and of
  its refinements' titles and bodies. Header fields are excluded, so a status
  change or a new link on the target never makes anything suspect; a wording
  change always does.
- `explain accept P5` records, for each link from P5, the current fingerprint
  of the link's target, in `accepted-links.txt` in the spec root (one line per
  link: `FROM RELATION TO FINGERPRINT`; machine-written, sorted, diffable, and
  greppable). `explain accept --all` does it for every link. Accepting means
  "I have read the source item against the target as it is now."
- `explain check` reports a **suspect link** when an accepted link's target
  fingerprint no longer matches: "P5 serves G9, but G9 changed since this link
  was accepted; re-read P5, then `explain accept P5`". A report, not an error:
  the graph is intact, a human judgement is pending.
- `explain drift` lists the same, grouped by changed target, with the
  `accept` command to run once the dependants have been re-read. This is the
  re-evaluation sweep that used to be done by hand after a goal's wording
  moved.
- Links never accepted are counted in one report line, not checked. Drift
  detection is opt-in per link so a fresh spec is not buried in noise.
- Across specs, fingerprints travel in the exported index. A child that
  resolves its parent live sees the change at once; a child that pins a
  committed index snapshot sees it when the snapshot is refreshed, and a
  child that has both is told when the snapshot is stale. In the other
  direction, a child's exported links carry the fingerprint it accepted, so
  the parent's `drift` can say which child items (tests, review rules) must
  be re-reviewed because a row here moved.
- **Source citations.** Code is the last child. A source file may carry a
  comment line `spec: S49, D30` (this code serves those rows) or
  `spec-guard: S532.5` (this test verifies them), in any comment style; each
  id may carry `@<fingerprint>` recording the row as last read. `explain scan
  DIR -o code.index.json` turns every such line under DIR into a child index
  (one item per file, one link per citation, `accepted` from the `@`), and
  once the manifest declares that index under `children:` the parent's
  `drift` and `check` treat a stale citation exactly like a stale child link.
  `explain scan FILE --accept` rewrites a file's citations with the rows'
  current fingerprints after the code has been re-read. `check` never reads
  source itself: the citations reach it only through the scanned index, so a
  spec stays checkable without its code present. `explain covers PATH[:LINE]`
  answers the other direction: which rows name this file (through `refs`, the
  file's own citations, or any child index), and their chain to the top.

## 13. Components and boundaries

A means-ends hierarchy says why each item exists; it says nothing about what
can change independently. Those are different properties, and a traceable spec
can still describe an overdetermined system. Components make the second
property visible and checkable.

- **Declaring a component.** Any item becomes a component by carrying
  `component: true` or `hides:` (its secret, in one line), by being the target
  of another item's `part-of`, or by having an `interface: true` sub-item. Its
  dotted sub-items are inside it. Any other item, at any level, joins a
  component with `part-of: D201`; components nest the same way. Items with no
  component are **cross-cutting**: goals and principles usually, and the few
  doctrines that are meant to touch everything.
- **Interfaces are guarantees.** An item flagged `interface: true` is part of
  its component's published surface: a promise other components may rely on.
  The other half of the contract already exists: the component's `A` items are
  its requirements on the world, each `discharged-by` some other component's
  guarantee. `explain interfaces D201` shows both halves, with who depends on
  each guarantee from outside.
- **The boundary rule.** A `serves`, `depends-on` or `assumes` link from inside
  component A to an item inside a different component B must target B itself
  or one of B's interface items. Reaching up into an enclosing component is
  fine; reaching into a sibling's or a child's internals is reported as a
  **boundary crossing**. Links to cross-cutting items are never crossings, and a
  cross-cutting item that links into a component's internals is not a
  crossing either: `coupling` lists it as a candidate for `part-of`.
  `verifies`, `conflicts-with` and `supersedes` are exempt: a guard may look
  inside, and lateral bookkeeping is not a dependency. Components that depend
  on each other in a cycle are reported.
- **Measuring.** `explain coupling` reports, per component, its members,
  internal links, outgoing links that go through interfaces or nodes, outgoing
  crossings, incoming links, and cohesion (internal over internal plus
  outgoing); the component-to-component link counts; cycles; crossings; the
  cross-cutting items linked from more than one component; and overdetermined
  items, whose `serves` targets lie in three or more components. The
  re-evaluation sweep (`explain serves`) is the propagation-cost measure the
  design-structure-matrix literature uses; its cross-component fraction is
  what overdetermination looks like in this format.
- **Enforcing.** All of this is reports. A project that wants a gate promotes
  the boundary and cycle reports with `--strict`, or asserts in its own check
  that crossings do not increase. Design coupling is not code coupling: an
  `I` row's `refs` are where a code-level import check should attach later.

## 14. Questions and conditions

Two things every real corpus carried that the first format could not name.

- **Open questions** are items of kind `Q`, allowed at any level, status
  `proposed` while open. An item that waits on the answer says
  `depends-on: Q3`. When the answer arrives it is an ordinary item (a ruling,
  a decision) that `supersedes: Q3`, and the question's status becomes
  superseded, so the record keeps both the question and the answer.
  `explain questions` lists the open ones by level with what each blocks: the
  owner's review flow starts from the decisions still needed rather than from
  the rows already settled.
- **`until:`** records the condition under which an item stops serving its end.
  A means-ends link is only valid under stated conditions; this field names
  them, one line, in the item's own words ("stops serving when cards accumulate
  that no day made urgent"). It is the design-level twin of the rule that a
  guard must state the assumption it monitors, and `review` prints it beside
  the links so a reader can ask whether the condition has already been met.
