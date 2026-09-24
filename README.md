# explain

**Design docs that know why every piece exists.**

A year into a project, the design doc says what was built, but not why a line
of code is there, what a changed requirement will break, or which decisions
quietly rested on an assumption that stopped being true. That knowledge lived
in someone's head, and the doc drifted away from the code the week it was
written.

`explain` is a small format for design docs (plain markdown, in your repo) and
a command-line tool that answers those questions from it:

```
explain why S4              what does this decision exist for?
explain how G1              what, all the way down to code, achieves this goal?
explain serves A2           if this changes, what needs a second look?
explain covers src/put.py   which parts of the design govern this file?
explain drift               what changed, and which code and tests must be re-read?
```

## The idea

The format comes from Nancy Leveson's *intent specifications*, used for
safety-critical systems. A spec is a stack of levels. Each level describes the
whole system in a different language, from purpose down to code:

| Level | Holds | Asks |
|---|---|---|
| L0 purpose | goals, constraints, assumptions, hazards | what must be true? |
| L1 principles | the rules the design follows | what do we believe? |
| L2 architecture | components, interfaces, behaviors | what are the parts? |
| L3 specs | detailed decisions | what exactly? |
| L4 realization | code and tests | where is it? |

Every item names the item above it that it **serves**. Reading up a chain
answers *why*; reading down answers *how*. Here is one chain from the example
in this repo, a safe replacement for `rm`:

```
G1  A deletion made by mistake can be undone                  L0 purpose
 └ P5  Restoring is putting in reverse: never over anything   L1 principles
    └ D3  Restore and list                                    L2 architecture
       └ S5  Restore never overwrites a file                  L3 specs
          └ I3  src/trash/restore.py                          L4 realization
```

An item is a markdown heading with an id, a few `key: value` lines, and prose:

```markdown
## S5 — Restore never overwrites: a taken path is an error that names --to
status: adopted
serves: D3

Restoring over an existing file would destroy it, which C1 forbids.
```

That is nearly the whole format. The letter in an id says what kind of item
it is (**G**oal, **C**onstraint, **P**rinciple, **D**esign element, **S**pec,
**A**ssumption, **H**azard, **V**erification, open **Q**uestion, ...), and
ids are unique across the spec, so `S5` alone finds it, from any file or
commit message. Links are typed (`serves`, `assumes`,
`depends-on`, `verifies`, ...) and the tool computes every inverse, so nobody
maintains a link in two places.

## A tour

The repo includes [`examples/trash`](examples/trash): a small working program,
a drop-in for `rm` that moves files to a trash can, with a complete spec
behind it. Forty-five items span five levels, down to its six source files
and its tests.

```
git clone https://github.com/ratsark/explain
pip install ./explain            # or pipx; see "Install" below
cd explain/examples/trash
```

Like git, `explain` finds the spec on its own: it looks for `spec.yaml` or
`spec/spec.yaml` in the current directory and then in each parent. Ids are
case-insensitive.

**What is this?**

```
$ explain g1
G1 — A deletion made by mistake can be undone
  goal at L0 (purpose); L0-purpose.md:15; fingerprint 522e594d1a
  status: adopted
  serves: G0 (implied root)
  served-by: P4, P5

  The user gets back any file they trashed, with its name and contents, at the
  path it came from, until they choose to destroy it.
```

**Why does this exist?** The 30-day default for emptying the trash looks
arbitrary. It is not:

```
$ explain why s4
S4 — `--empty` with no argument destroys entries trashed more than 30 days ago
  D4 — Empty
    P1 — Destruction lives in one place
      G1 — A deletion made by mistake can be undone
        G0 — Deleting from a shell can be taken back
      C1 — trash never destroys data the user did not explicitly ask to destroy
    P6 — Space is reclaimed oldest first, and only when asked
      G3 — The space held by deleted files comes back on the user's terms
        G0 — Deleting from a shell can be taken back
      H1 — The trash fills the disk without anyone noticing
```

Anyone changing that number now knows what it balances: recovering mistakes,
reclaiming space, and a named hazard.

**How is this promise kept?** Follow a constraint down to the code that
enforces it:

```
$ explain how c2
C2 — At every instant a trashed file exists in exactly one place
  P2 — Move by rename; when a rename is impossible, copy, flush, and only then remove
    D6 — The move
      S10 — Across filesystems: copy, flush every copied file and directory, then remove the original
        I6 — src/trash/move.py
      S7 — A symlink is moved as a link, across filesystems too
        I2 — src/trash/put.py
        I6 — src/trash/move.py
```

A thin tree is a finding in itself. Writing this example, `how c2` first came
back with no spec for the cross-filesystem copy at all. Looking closer found
a real bug: copied directories were not flushed to disk before the original
was deleted. S10 and its fix came out of that.

**What if this changes?** Suppose you learn that people notice a mistaken
deletion after months, not days. Everything resting on that assumption,
transitively, through code and tests:

```
$ explain serves a2
downstream of A2 — People notice a mistaken deletion within days, not months (via serves, assumes, discharged-by, verifies, depends-on and refinement):
  L1 (principles):
    P6         Space is reclaimed oldest first, and only when asked  (assumes A2, depth 1)
  L2 (architecture):
    D4         Empty  (serves P6, depth 2)
    D5         The command line  (depends-on D4, depth 3)
  L3 (specs):
    Q1         Should trash warn when the can grows past some share of free space?  (serves D4, depth 3)
    S4         `--empty` with no argument destroys entries trashed more than 30 days ago  (assumes A2, depth 1)
    ...
  in children:
    code:src/trash/empty.py  src/trash/empty.py  (serves S4, depth 2)
    code:tests/test_trash.py tests/test_trash.py  (verifies S4, depth 2)
    ...
  12 items (3 in children)
```

**What governs this code?** Source files cite the rows they realize with a
comment such as `# spec: S4`. From a file and line, get the rows and their
reasons in one call:

```
$ explain covers src/trash/empty.py:20
rows whose refs name src/trash/empty.py:
  D4         L2  Empty
  I4         L4  src/trash/empty.py
citations in src/trash/empty.py nearest line 20:
  :10 serves S4         `--empty` with no argument destroys entries trashed more tha  (fingerprint current)

up-chain to the top:
  I4 — src/trash/empty.py
    S4 — `--empty` with no argument destroys entries trashed more than 30 days ago
      D4 — Empty
      ...
```

**What drifted?** Every item has a fingerprint of its wording. When someone
edits S4 from 30 days to 7, everything that was written against the old
wording is flagged, including the code and the test that cite it:

```
$ explain drift
S4 — `--empty` with no argument destroys entries trashed more than 7 days ago changed (accepted 54a885a968, now cea5ab8da9). Re-read:
    I4         src/trash/empty.py  (serves; L4-realization.md:29)
  then: explain accept I4
1 suspect link(s) across 1 changed target(s); 60 accepted in total

in children (2 link(s) whose target here moved since the child accepted it; re-review in the child, then accept there):
  code:src/trash/empty.py serves S4 — `--empty` with no argument destroys ...
  code:tests/test_trash.py verifies S4 — `--empty` with no argument destroys ...
```

**Is the design complete?** `explain check` has two classes of finding.
Errors mean the graph is broken, such as a link to an id that does not exist.
Everything else is a report, because an unfinished design is a normal state,
not a failure:

```
$ explain check
L0-purpose.md:53: report: A1: nothing discharges this assumption [undischarged-assumption]
L0-purpose.md:59: report: A2: nothing discharges this assumption [undischarged-assumption]
...
trash: 45 items in 5 levels; 0 errors, 8 reports
```

Those two reports are honest: trash's retention policy rests on a belief
about users that nothing measures. Other reports flag an item that serves
nothing, a spec no code realizes, a level skipped in a chain, or a component
reaching into another's internals.

## Why this works

- **Reasons are recorded where decisions are.** Every item states what it
  serves, so revisiting a decision starts from its purpose, not from
  archaeology.
- **Impact is computed, not remembered.** `serves` and `drift` replace the
  hand-run sweep of "what else did this touch?"
- **It lives with the code.** Plain markdown in the repo, reviewed in the same
  pull requests, greppable, readable without the tool.
- **The tool never guesses.** No inferred links and no fuzzy matching. What is
  missing is reported for a person to decide.
- **Levels fit the domain.** A profile names the levels and their kinds.
  `software` and `business` ship with the tool, and you can write your own.
- **Specs nest.** A subsystem's spec can serve an item in its parent system's
  spec, in another repository, and drift crosses that boundary too.

## Install

`explain` is one Python package with no dependencies. It needs Python 3.9 or
later.

```
pipx install git+https://github.com/ratsark/explain    # or: pip install git+https://...
```

Without installing, run the package directory directly:

```
alias explain='python3 /path/to/explain/explain'
```

Or copy the `explain/` directory into a repo's `tools/` and run
`python3 tools/explain` there, so the version is pinned with the project.

## Start a spec

```
explain init myproject spec --profile software
```

This creates `spec/` with a manifest, one file per level holding that level's
suggested sections, and a short README of the rules. Write L0 first: the
goals, the constraints that are never traded away, and the assumptions. Run
`explain check` as you work downward. Sections that do not apply yet can stay
empty until they come up.

## Commands

| Command | Answers |
|---|---|
| `explain ID` | What is this item: its header, links in both directions, and body. |
| `explain why ID` / `how ID` | The chain up to the purpose / the tree down to the code. |
| `explain serves ID` | Everything downstream, transitively: what a change would touch. |
| `explain covers FILE[:LINE]` | Which rows govern a source file, and why. |
| `explain check` | Errors (a broken graph) and reports (incompleteness). |
| `explain drift` / `accept ID` | Links whose target's wording changed / mark them re-read. |
| `explain scan DIR -o FILE` | Gather `spec:` and `spec-guard:` citations from source into an index. |
| `explain questions` / `assumptions` | Open questions and what waits on them / assumptions and what discharges them. |
| `explain coupling` / `interfaces ID` | Component cohesion and boundary crossings / a component's contract. |
| `explain review L1` | Walk one level item by item, for a design review. |
| `explain orphans` / `isolated` / `outline` / `export` / `allocations` | The rest; `explain -h` lists them all. |

## Learn more

- [ARCHITECTURE.md](ARCHITECTURE.md) is the full format: ids, links, levels,
  profiles, nesting, drift, and components.
- [examples/trash](examples/trash) is the tour's spec and program.
  [examples/aircraft](examples/aircraft) and [examples/cas](examples/cas) are a
  nested pair: a collision-avoidance system's spec serving an aircraft's.
- [spec/](spec) is explain's own design, written in its own format.
- [research/](research) is the background reading behind the format.

## Bugs, feature requests, questions

File a GitHub issue on this repo. Include the command you ran, the smallest
spec that shows the problem, and the output of `explain --version`.

```
gh issue create -R ratsark/explain --title "check: false unknown-id on L4-V1.2" --label bug
```

Status: format v0, tool v0.1. It is in use on one production project.
