# L3 — Decisions

The format's settled decisions, each with the date and the reason. Bodies in
ARCHITECTURE.md; the rows are the index.

## Decisions

## S1 — Numeric ids, not slugs
status: adopted
serves: D15
source: user decision 2026-09-12; ARCHITECTURE.md § 4 (Ids)

`G2`, not `G-beauty`: what the first project already cited, and `show` answers
"what is G2" instantly. A `slug:` alias can come later.

## S2 — The header is the contiguous key: value lines under a heading item, unfenced
status: adopted
serves: D14
source: user concern about length 2026-09-12; ARCHITECTURE.md § 4

## S3 — Sub-items may be bullets, carrying inline links only
status: adopted
serves: D14
source: user question on G5.2.3 2026-09-12; ARCHITECTURE.md § 4

Dotted ids are refinement; nested bullets are nested refinement.

## S4 — A mention is checked for existence but is not an edge
status: adopted
serves: D14
source: the first deployment's disambiguation ruling; ARCHITECTURE.md § 5

## S5 — Kind letters are unique across a spec; `L` is reserved
status: adopted
serves: D15
source: the first deployment's id-collision incident; ARCHITECTURE.md § 4

## S6 — Free kinds need no level prefix; a written one is checked
status: adopted
serves: D15
source: 2026-09-13, after the first deployment's L0 filled with world-facts; ARCHITECTURE.md § 4
supersedes: S6.1

### S6.1 — Per-level kinds carry a mandatory level prefix
status: superseded
source: 2026-09-12 (the original rule, kept for the record)

## S7 — Legacy citation keys become aliases
status: adopted
serves: D15
source: 2026-09-12, the numbered laws of the first deployment; ARCHITECTURE.md § 5 (`aka`)

Each law sits at the level its content has and keeps "law N" as `aka`, so
`explain "law 16"` resolves and the numbers never change.

## S8 — Build state is separate from decision state
status: adopted
serves: D16
source: adopter issue #2, 2026-09-13; ARCHITECTURE.md § 5 (`built`), § 9

`built:` splits `unserved` into unrealized and unguarded once stated; unbuilt
rows are a count, not 431 reports.

## S9 — Open questions are items of kind Q
status: adopted
serves: D18
source: every family of the first transcription carried pending owner questions; ARCHITECTURE.md § 14

Proposed while open; the answer supersedes it; `questions` lists them with what
they block.

## S10 — until: names the condition under which an item stops serving its end
status: adopted
serves: D18
source: the Fire charter's own rule-to-end table; ARCHITECTURE.md § 14

## S11 — The error classes
status: adopted
serves: D16
source: ARCHITECTURE.md § 9

Duplicate id; kind at the wrong level; prefix disagreeing with the path;
unknown id in a relation; unknown namespace; unknown key or relation name;
malformed header; serves pointing downward; refinement of an undefined parent;
a malformed accepted-links line; a part-of that is undefined, self, or a cycle.

## S12 — The report classes
status: adopted
serves: D16
source: ARCHITECTURE.md § 9

Orphan, unserved, unrealized, unguarded, skip-level, same-level same-kind
serves, unresolved mention, undischarged assumption, missing ref, section
absent, section prose-only, unresolvable namespace, index stale, supersedes
unmarked, suspect link, untracked links, boundary crossing, component cycle,
interface without component, question adopted.

## S13 — The isolated count is the settlement measure
status: adopted
serves: D16
source: adopter issue #3, 2026-09-13; ARCHITECTURE.md § 9

Items with no link in either direction; refinement counts, mentions do not.
It only falls, and cannot be moved by trading one report class for another.

## S14 — A same-level serves between items of the same kind is reported; between kinds it is silent
status: adopted
serves: D16
source: 2026-09-12, a constraint serving a goal at L0 is Leveson's own layout; ARCHITECTURE.md § 9

## S15 — An unresolvable parent or child is a report, and its ids are not checked
status: adopted
serves: D16
source: ARCHITECTURE.md § 8, § 9

## S16 — A profile section that holds prose but no items is reported
status: adopted
serves: D16
source: user question 2026-09-12 (do sections contain items or prose); ARCHITECTURE.md § 9

Prose outside an item has no fingerprint, so drift in it is invisible.

## S17 — Cross-spec fingerprints travel in the export index; a stale snapshot is reported
status: adopted
serves: D13
source: ARCHITECTURE.md § 12

## S18 — The bare first argument means show
status: adopted
serves: D17
source: user, 2026-09-12 ("what's g2"); ARCHITECTURE.md § 9

## S19 — Adjacency is a goal, not a hard constraint
status: adopted
serves: D16
source: user decision 2026-09-12 (never block an author on a missing middle level); ARCHITECTURE.md § 6

A skip-level link is a report that a middle item may be waiting to be named;
a downward serves is an error.

## S20 — The standard project documents map onto the levels; PLAN.md stays outside
status: adopted
serves: D19
source: user agreement 2026-09-12; ARCHITECTURE.md § 11

MISSION_STATEMENT is L0's mission, REQUIREMENTS is L0, ARCHITECTURE is L2 with
its decisions at L3, DEVELOPMENT is L4; PLAN.md is Leveson's Level 0, program
management, orthogonal to the stack.

## S21 — Source files cite rows; the checker reads the citations only through a scanned child index
status: adopted
serves: [D12, D13]
source: fitribe audit 2026-09-24 (explain issue #6); ARCHITECTURE.md § 12

`spec: S49, D30` and `spec-guard: S1` are the two citation forms, each id
optionally `@fingerprint`. `scan` makes the index; `check` never opens
source, so a spec is checkable without its code.

## S22 — covers answers "what governs this file" from refs, the file's own citations and child indexes
status: adopted
serves: D17
source: explain issue #6; ARCHITECTURE.md § 9, § 12

With a line, the nearest citation at or above it wins; every row found is
followed by its chain to the top, so one call replaces `grep` plus `why`.

## S23 — A suggested parent is a promotable note, never a link
status: adopted
serves: [D16, P5]
source: explain issue #6; the first deployment's "Suggested parent (unrecorded in source)" convention

`orphans --suggested` lists the rows carrying the note with the ids it
names; promotion is a human writing `serves:` into the header.

## S24 — With no path, the spec is found the way git finds a repository
status: adopted
serves: D17
source: user, 2026-09-24 ("explain g1" instead of a module path and a spec path); ARCHITECTURE.md § 9

`spec.yaml` or `spec/spec.yaml` here, then in each parent. An explicit path
is taken as given and never walked upward.
