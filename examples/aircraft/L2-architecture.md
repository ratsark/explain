# L2 — Architecture

## Components

## D1 — Collision avoidance system
status: adopted
serves: P1
depends-on: cas:G3

Realized by the `cas` spec. Its top-level goals `cas:G1` and `cas:G2` serve
this element. `cas:G3` (a traffic display) is a goal the child added on its
own; citing it here is how the parent acknowledges a derived child item.

## D2 — Barometric altimeter
status: adopted
serves: [P1, P2]

Supplies own altitude to D1. This is what discharges the child's assumption
about altitude accuracy (`cas:A1`).

## D3 — Mode S transponder
status: adopted
serves: P1

Replies to interrogations from other aircraft's collision avoidance systems.
