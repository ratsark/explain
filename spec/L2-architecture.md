# L2 — Architecture

The tool's components and the format's doctrines. Bodies in ARCHITECTURE.md
and in the module docstrings.

## Components

## D1 — The parser
status: adopted
built: shipped
component: true
hides: how markdown text becomes items, links and mentions
serves: [P2, P3]
refs: [explain/parse.py]

Levels from `L<n>-` paths, heading and bullet items, the fenceless header,
typed inline links, mentions, fenced blocks ignored. Every regex it matches is
declared at the top of the file and printed by `--patterns`.

### D1.1 — Interface: the Spec object
interface: true
refs: [explain/parse.py]

`parse_spec(root)` returns items, links, findings, sections and the accepted
links; nothing else reads markdown.

## D2 — The checker
status: adopted
built: shipped
component: true
hides: what counts as an error and what counts as a report
serves: [P6, P5]
refs: [explain/checks.py]

Id and kind rules, link resolution (local and cross-spec), completeness
reports, drift, questions, sections; plus the queries (`downstream`,
`upstream`, `connectivity`, `questions`) and the export index.

### D2.1 — Interface: findings
interface: true
refs: [explain/checks.py]

`run_checks(spec)` returns Findings with severity, code, message, file, line;
the CLI and adopters' corpus checks consume nothing else.

### D2.2 — Interface: the export index
interface: true
serves: P8
refs: [explain/checks.py]

`export_index(spec)`: ids, levels, kinds, titles, statuses and fingerprints, the
whole cross-spec contract. A child pins a snapshot of it or resolves it live.

## D3 — Components and boundaries
status: adopted
built: shipped
component: true
hides: how membership, interfaces and crossings are computed
serves: P10
refs: [explain/components.py]

Membership from `part-of` and refinement, the boundary classification of every
link, component edges, cycles, cohesion, cross-cutting and overdetermined
items.

## D4 — The command line
status: adopted
built: shipped
component: true
hides: how findings and queries are printed
serves: [G1, G3]
depends-on: [D1.1, D2.1, D2.2]
refs: [explain/cli.py]

One command per question: check, show (the default for a bare id), serves,
why, orphans, isolated, questions, outline, export, assumptions, accept,
drift, review, coupling, interfaces.

## D5 — Profiles
status: adopted
built: shipped
component: true
hides: which levels, kinds and sections a spec may use
serves: [G6, P9]
refs: [explain/profile.py, explain/profiles/software.yaml]

A shipped `software` profile; a project overrides with `profile.yaml` in its
spec root. Free kinds are declared once for all levels.

## D6 — The YAML subset
status: adopted
built: shipped
component: true
hides: how much of YAML the tool understands
serves: C3
refs: [explain/miniyaml.py]

Mappings, block and flow lists, scalars, comments; nothing else, and every
deviation raises with a line number. Exists so that PyYAML is not a dependency.

## Doctrines

## D10 — The fingerprint
status: adopted
serves: [P7, G2]
refs: [explain/parse.py]

A short hash of an item's title and body and of its refinements'. Header
fields are excluded: a status change never makes dependants suspect; a wording
change always does.

## D11 — The boundary rule
status: adopted
serves: P10
refs: [explain/components.py]

A `serves`, `depends-on` or `assumes` link from inside one component into
another must target that component or one of its interface items. Reaching up
is fine; a cross-cutting source is a `part-of` candidate, not a crossing;
`verifies` is exempt.

## D12 — The nesting contract
status: adopted
serves: P8
refs: [examples/aircraft, examples/cas]

Parents and children declared in `spec.yaml` by path or by a committed index
snapshot; a child's L0 items serve the parent's design element; child
assumptions carry `discharged-by`; derived child items are reported until the
parent cites them.

## D13 — The drift protocol
status: adopted
serves: [G2, P7]
refs: [explain/checks.py]

`accept` records each link's target fingerprint in `accepted-links.txt`;
`check` reports a suspect link when it no longer matches; `drift` groups them
by changed target; re-reading, then `accept`, clears them. Opt-in per link so a
fresh spec is not buried in noise.

## D14 — The item grammar
status: adopted
serves: [P2, P1, G4]
refs: [ARCHITECTURE.md]

Heading and bullet items, the unfenced header, typed links in headers and
prose, mentions, refinement by dotted id. ARCHITECTURE.md § 4 and § 5.

## D15 — The id scheme
status: adopted
serves: P3
refs: [ARCHITECTURE.md]

Kind letter plus number, kinds unique per spec, `L` reserved, free kinds at
any level, aliases for legacy keys, `was:` for level moves. ARCHITECTURE.md § 4.

## D16 — The report taxonomy
status: adopted
serves: [P6, C1, C2]
refs: [ARCHITECTURE.md]

Two classes and no third; the closed lists of error and report codes; the
summary counts that measure settlement. ARCHITECTURE.md § 9.

## D17 — The command-line conventions
status: adopted
serves: [G4, G3]
refs: [ARCHITECTURE.md]

One command per question, a bare id means show, exit codes follow the grep
idiom, every answer is greppable text. ARCHITECTURE.md § 9.

## D18 — Questions and conditions
status: adopted
serves: [P7, P9]
refs: [ARCHITECTURE.md]

Open questions as items that answers supersede; `until:` as the condition
under which a link holds. ARCHITECTURE.md § 14.

## D19 — The directory layout
status: adopted
serves: [P1, G4]
refs: [ARCHITECTURE.md]

One spec is one directory; a level is a file or a directory named `L<n>-`;
files within a level are for navigation only; the standard project documents
map onto the levels, with PLAN.md staying outside as program management.
ARCHITECTURE.md § 2 and § 11.
