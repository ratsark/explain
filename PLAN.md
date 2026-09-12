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

## Phase 3 — Nesting _(in progress, started 2026-09-12)_

The public example is now a nested pair, `examples/aircraft` (parent) and
`examples/cas` (child), exercising `serves: parent:ID`, `discharged-by`,
derived child goals, and the parent citing a child item. Remaining: the
parent's `allocations` view; index-snapshot staleness reporting; a second
real spec nested under the first project's (its business proposition as a
parent, or its mobile app as a child) in that project's repo.

**Acceptance:** tests for every cross-spec check; `allocations` on
`examples/aircraft` lists the child's items per parent element; a real nested
pair links both ways in the first project's repo.

## Phase 4 — Review flow, profiles, handover _(not started)_

`status` handling and an `explain review` walk per level; `adopted-through` in
the manifest; a second profile for a business-proposition domain; the
`leveson` reference profile. Handover in the first project: its agents write
L2 and L3 rows as they touch them; its earlier index tool retired once
`explain` answers everything it did; its earlier L0/L1 files retired in favour
of `spec/` on the owner's word.

**Acceptance:** a level-by-level review of a real spec run with the user using
the tool; the first project's agents use only the new tool.

## Phase 5 — Dogfood _(not started)_

Rewrite this project's own ARCHITECTURE.md as a spec: goals such as "dumb and
greppable" and "incompleteness is a report" at L0, format rules at L1, the
tool's design at L2, with ARCHITECTURE.md reduced to a pointer.

**Acceptance:** `explain check` on this repo's own spec is clean apart from
declared reports; every claim in the old ARCHITECTURE.md has an item id.

## Later

Content fingerprints on links (suspect-link detection after upstream edits).
HTML render.
