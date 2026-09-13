# L0 — Purpose

explain's own spec: the format applied to itself. Rows point at the bodies in
MISSION_STATEMENT.md and ARCHITECTURE.md; they do not copy them.

## Mission

## G0 — The mission
status: adopted
source: MISSION_STATEMENT.md, approved by the user 2026-09-12
refs: [MISSION_STATEMENT.md]

A lightweight, modular design-document format and a tool for querying and
checking it: purpose at the top, realization at the bottom, every item linked
to the ends it serves and the means that realize it. Success is a project whose
design review proceeds level by level from agreed goals, whose agents can
answer "why does this exist" and "what depends on this" with one command, and
whose spec is still trusted a year in.

## Goals

## G1 — Every item answers why and how
status: adopted
source: MISSION_STATEMENT.md ¶1; ARCHITECTURE.md § 1

Every item links to the ends it serves and the means that realize it, so the
two questions the mission names are one command each (`why`, `serves`).

## G2 — Drift is visible and the re-read list is exact
status: adopted
source: MISSION_STATEMENT.md ¶2

The format cannot stop a layer from drifting away from its neighbours; it
makes drift visible and keeps the list of what to re-read exact.

## G3 — Humans write the top, agents write the bottom, the tool keeps both honest
status: adopted
source: MISSION_STATEMENT.md ¶3

## G4 — Lightweight: plain markdown, one directory, nothing to install
status: adopted
source: MISSION_STATEMENT.md ¶1; ARCHITECTURE.md § 2, § 9

## G5 — Modular: one system's spec can be a component of another's
status: adopted
source: MISSION_STATEMENT.md ¶1; ARCHITECTURE.md § 8

Across directories, repos, or organizations, with the contract between them
explicit.

## G6 — The level set is chosen per domain, not fixed
status: adopted
source: MISSION_STATEMENT.md ¶1; ARCHITECTURE.md § 7

## Constraints

## C1 — Incompleteness is a report, never a failure; broken structure is an error
status: adopted
serves: G3
source: MISSION_STATEMENT.md ¶2; ARCHITECTURE.md § 9

A spec grows level by level and is expected to be unfinished below the line
of what has been agreed. A goal added today is expected to have nothing under
it.

## C2 — Every pattern is declared, and the tool says what it cannot see
status: adopted
serves: G3
source: MISSION_STATEMENT.md ¶2; ARCHITECTURE.md § 9 (`--patterns`, declared misses)

Every answer the tool gives could be reproduced by hand from the text; a
confident empty result is never returned where a miss is known.

## C3 — Standard library only; the tool is copied, not installed
status: adopted
serves: G4
assumes: A2
source: ARCHITECTURE.md § 9; DEVELOPMENT.md

## C4 — Nothing specific to an adopting project lives in this public repo
status: adopted
source: DEVELOPMENT.md § Conventions; user instruction 2026-09-12

Adopters vendor the tool and keep their integration notes with them.

## Environment

### Assumptions

## A1 — Markdown is what humans and agents both read and write
status: adopted
source: user, 2026-09-12 ("it's the standard for human and agent readable text these days")

## A2 — Adopters have git and Python 3.9 or later, and nothing else can be assumed
status: adopted
source: ARCHITECTURE.md § 9
