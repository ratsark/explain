# L1 — Principles

The rules of the format that hold across every profile. Bodies live in
ARCHITECTURE.md; each row names its section.

## Principles

## P1 — Each level is a complete model of the same system in a different language
status: adopted
serves: [G1, G6]
source: research/00-SYNTHESIS.md § 1 (Leveson, Rasmussen); ARCHITECTURE.md § 1

Adjacent levels answer why upward and how downward. Refinement and
decomposition happen within a level, never between levels.

## P2 — Links are typed wherever they appear, and placement carries no meaning
status: adopted
serves: [G1, G3]
assumes: A1
source: ARCHITECTURE.md § 4, § 5; user decision 2026-09-12 (the hybrid)

`serves: G2` in a header and `[[serves G2]]` in a sentence are the same edge.
An untyped mention is not an edge. A bare id in prose is text.

## P3 — A kind implies its level, so an id never needs a level in front of it
status: adopted
serves: [G1, G4]
source: ARCHITECTURE.md § 4 (Ids); user decision 2026-09-12 (globally unique prefixes)

Free kinds are the exception that proves it: their level comes from the path,
and a written prefix is checked, not required.

## P4 — Inverses are computed, never written
status: adopted
serves: G2
source: ARCHITECTURE.md § 5; research/00-SYNTHESIS.md § 3

Hand-written bidirectional links are where every surveyed format started
drifting.

## P5 — The tool never infers a link
status: adopted
serves: [G2, G3]
source: ARCHITECTURE.md § 9 (design stance), § 10 (the lessons the first deployment recorded)

No heuristics, no fuzzy matching, no purpose guessed from prose. A missing
purpose is reported, with the suggestion left to a human.

## P6 — Errors mean the graph is malformed; everything else is a report
status: adopted
serves: [C1, G3]
source: ARCHITECTURE.md § 9

Two classes and no third. `--strict` exists for anyone who wants a gate.

## P7 — A means-ends link is valid only under stated conditions
status: adopted
serves: [G2, G1]
source: ARCHITECTURE.md § 12, § 14; Leveson's assumptions under each item

Fingerprints catch a change in the target's wording; `until:` names the
condition in the world; assumptions with `discharged-by` name who guarantees
them.

## P8 — The parent's design element is the child's purpose
status: adopted
serves: G5
source: ARCHITECTURE.md § 8; research/04-recursive-multilevel-design.md

A child spec's top-level items serve the parent's design element; the child's
assumptions flow back up as obligations; derived child items are acknowledged
by the parent. The contract is the exported index, the `serves` links into it,
and the assumptions with their dischargers. No third document.

## P9 — Environment and verification exist at every level
status: adopted
serves: [G6, G1]
source: ARCHITECTURE.md § 4 (free kinds), § 7; Leveson's columns; the first deployment's re-homing 2026-09-13

Assumptions, limitations, hazards, evaluation criteria, questions and guards
belong at the level whose items rely on them, not at the top.

## P10 — Modularity is a separate property from traceability, and is measured, not assumed
status: adopted
serves: [G1, G5]
source: ARCHITECTURE.md § 13; user question 2026-09-12 (componentization)

A traceable spec can still describe an overdetermined system. Components,
interfaces and the boundary rule make the second property visible; enforcement
is a project's policy, not the tool's.
