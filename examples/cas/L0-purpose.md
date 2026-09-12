# L0 — Purpose

The child spec. Top-level goals serve the parent's design element
`aircraft:D1`. Environment assumptions say what this system needs from the
aircraft and from the world, and `discharged-by:` says who guarantees each.

## Goals

## G1 — Detect potential mid-air collisions
status: adopted
serves: aircraft:D1

For any two aircraft closing at up to 1,200 knots horizontally and 10,000
feet per minute vertically.

## G2 — Resolve detected threats with advisories to the crew
status: adopted
serves: aircraft:D1

## G3 — Display nearby traffic to the crew
status: proposed

Not asked for by the parent: a derived goal. The checker reports it as
"derived from the parent's point of view" until the parent cites it, which
`aircraft:D1` now does with `depends-on: cas:G3`.

## Constraints

## C1 — Never issue an advisory that reduces separation
status: adopted
serves: G2

## Environment

### Assumptions

## A1 — Own altitude is accurate to within 100 feet
status: adopted
discharged-by: aircraft:D2

## A2 — A threat aircraft will not manoeuvre abruptly against the escape manoeuvre
status: adopted

Nothing discharges this; it is an accepted risk that the checker keeps
visible.

## Limitations

## X1 — No protection against aircraft without an operating transponder
status: adopted
