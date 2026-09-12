# L0 — Purpose

An illustrative parent spec. Its collision avoidance system is a component
with a spec of its own (`../cas`), which is how nesting works: the parent's
design element D1 is the child's purpose. Content is loosely after the TCAS
example in Leveson's *Intent Specifications* (2000), simplified and invented
where convenient.

## Goals

## G1 — Carry passengers safely between airports
status: adopted

## G2 — Avoid collision with other aircraft
status: adopted

In all meteorological conditions, with or without ground control.

## Constraints

## C1 — Comply with the airspace rules of every jurisdiction flown
status: adopted
serves: G1

## Environment

### Assumptions

## A1 — Air traffic control separates aircraft in controlled airspace
status: adopted

Ground-based separation is the primary defence. It is assumed, not guaranteed,
which is why [[P1]] exists.
