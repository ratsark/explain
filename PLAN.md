# Plan

Managed by Claude. Phases with acceptance criteria. Status as of 2026-09-12.

The first deploying project is private. Its integration notes, corpus check,
and handover status live in that repo (under its `spec/README.md`); this plan
refers to it only as "the first project".

## Feedback loop (step 0)

Success is measured three ways, all runnable without the user:

1. **Tool tests.** Small specs built in temp dirs per test under `tests/`.
   Every error and report class in ARCHITECTURE.md section 9 has a test that
   triggers it and asserts the exact report. `python3 -m unittest` is the gate.
2. **A real corpus.** The first project's L0 and L1 in the format, checked in
   that repo by a corpus script that asserts zero errors, the expected report
   classes, and that every id cited on a `serves:` line in the project's older
   documents resolves in the spec.
3. **Query fidelity.** Hand-verified answers to "what serves X" and "why does
   Y exist" on the examples and on the real corpus.

Only the format's readability to humans needs the user, and that is what the
level-by-level review of a real spec is for.

## Phase 0 — Research and format v0 _(complete 2026-09-12)_

Background research on Leveson, Rasmussen, existing traceable formats, and
recursive design (`research/`). Format v0 written as ARCHITECTURE.md.

**Acceptance:** met. Mission wording approved 2026-09-12; format reviewed
section by section (unique prefixes, hybrid links, file structure, relation to
the standard docs, error-versus-report rule). Named `explain` 2026-09-12.

## Phase 1 — The tool _(complete 2026-09-12)_

`explain` CLI: Python 3 stdlib only. Parser for the directory layout, heading
and bullet items, header lines and inline typed links, profiles, and manifests.
Commands: `check`, `show`, `serves`, `why`, `orphans`, `outline`, `export`,
`assumptions`. `--patterns` prints every regex and every declared miss.
Cross-spec resolution by parent path or index snapshot.

**Acceptance:** met. All tests green, one per error and report code; the
example specs report exactly what they were written to show; `show` prints
heading, header, body, location, and computed inverses.

## Phase 2 — First real corpus _(complete 2026-09-12)_

The first project's L0 and L1 transcribed into the format inside its own repo,
with the tool vendored there byte-identical (`VENDORED.md` in the copy names
the pinned commit and the re-vendor command), and a corpus check script in
that repo. The project's agents adopted it the same day.

**Acceptance:** met in that repo: zero errors; the one intended orphan; every
`serves:` citation in the older documents resolves; hand-verified queries.

**Support channel (settled 2026-09-12):** adopters file GitHub issues on this
repo with `gh` (templates under `.github/ISSUE_TEMPLATE/`, filing guide in
README.md, pinned issue #1 as the landing spot); this side watches the issue
list and replies on the issue. Titles carry the project name in brackets;
project internals stay in the project's repo.

## Phase 3 — Drift detection and the full first-project transcription _(in progress, started 2026-09-12)_

Reprioritised 2026-09-12 by the user: drift between layers is what has been
holding the first project back, so landing its whole design in the format,
with drift detection, comes before nesting.

Drift detection (ARCHITECTURE.md section 12): fingerprints, `accepted-links.txt`,
`accept` and `drift`, suspect and untracked reports, fingerprints in exports,
index-snapshot staleness. **Landed 2026-09-12** with tests.

Full transcription: **landed 2026-09-12** in the first project's repo: 945
items, zero errors, every row pointing at its body, five families drafted in
parallel from four read-only inventories, duplicates merged, cross-family links
resolved through `aka:`, drift baseline accepted (579 links). Awaiting the
project's agents' area-by-area review and the owner's decisions (recorded in
that repo's `spec/owner-questions.md`). Scope, restated: every standing design artifact of the first project
(numbered laws, never-list, charters, doctrines, surfaces, rulings, systems,
requirements, architecture decisions, packages, guards) as registry rows in
its `spec/`, rows pointing at bodies, statuses as the documents state them,
purposes recorded where the documents record them and reported as missing
where they do not. Inventoried by four parallel surveys, assembled by hand,
reviewed by the project's agents area by area through their issue tracker.

**Acceptance:** the project's spec checks with zero errors; every artifact its
agents cite by number or name has a row; the corpus check still passes;
`accept --all` bootstrapped so the next wording change anywhere in L0 or L1
is reported as suspect links; the project's agents have reviewed their areas.

## Phase 3b — Nesting _(deferred)_

The public example is a nested pair, `examples/aircraft` and `examples/cas`,
exercising `serves: parent:ID`, `discharged-by`, derived child goals, the
parent citing a child item, index-snapshot staleness, and (2026-09-13) the
parent's `allocations` view. Remaining: a real nested pair (the first
project's business proposition as its parent, which is also the first
non-software profile), when the user has time to author it.

**Acceptance:** `allocations` on `examples/aircraft` lists the child's items
per parent element; a real nested pair links both ways.

## Phase 4 — Review flow, profiles, handover _(not started)_

`status` handling and an `explain review` walk per level (landed); `adopted-through` in
the manifest; the `business` profile and `init` scaffold (landed 2026-09-13,
for the user's business-and-product pair, a separate private project); the
`leveson` reference profile. Handover in the first project: its agents write
L2 and L3 rows as they touch them; its earlier index tool retired once
`explain` answers everything it did; its earlier L0/L1 files retired in favour
of `spec/` on the owner's word.

**Acceptance:** a level-by-level review of a real spec run with the user using
the tool; the first project's agents use only the new tool.

## Phase 4b — Code as the last child _(landed 2026-09-24)_

The first project's audit found a third of its source files named by some
row's `refs` and no source file naming a row. Landed: `covers PATH[:LINE]`
(which rows govern a file, with their chain up), a documented citation form a
source file may carry (`spec: S49, D30`, `spec-guard: S1`, each id optionally
`@fingerprint`), `scan DIR` turning citations into a child index that the
existing cross-spec drift then watches, `scan FILE --accept`, and
`orphans --suggested` as the promotable list of unrecorded parents.

**Acceptance:** met by `tests/test_covers.py`: a citation without a
fingerprint is untracked; with one it goes suspect when the row's design
body changes and `covers` says so on the line.

## Phase 5 — Dogfood _(complete 2026-09-13)_

explain's own spec under `spec/`: mission and goals at L0, the format's
principles at L1, the tool's components (with interfaces and `hides:`) and the
format's doctrines at L2, every settled decision at L3 with its date and
reason, modules and test files at L4. ARCHITECTURE.md stays as the body and
names itself the body; the spec is the index.

**Acceptance:** met. `tests/test_dogfood.py` asserts zero errors, no orphans,
no suspect links, no boundary crossings, every ARCHITECTURE.md section cited
by a row, and every test file a guard. Writing it surfaced five unnamed L2
doctrines (the item grammar, the id scheme, the report taxonomy, the
command-line conventions, questions and conditions) that the skip-level
report asked for.

## Later

Candidates surfaced by the first full transcription (see the project's
`spec/TRANSCRIPTION.md` once landed): `built:` landed 2026-09-13 with the
unrealized/unguarded split and the isolated count; the `Q` kind with
`questions` and the `until:` field landed 2026-09-13 (section 14); still
open: a `due:` field for time-bound obligations (probably the tracker's job);
a first-class provenance field. HTML render.
