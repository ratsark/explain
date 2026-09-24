# L2 — Architecture

## Components

## D1 — The can
status: adopted
serves: P4
assumes: A3
hides: the on-disk layout and the record format
refs: [src/trash/can.py]

`files/NAME` holds what was trashed; `info/NAME.trashinfo` records its
original path and when it was trashed. Nothing else is stored anywhere.

### D1.1 — reserve: a NAME no other trash process can hold, its origin already recorded
interface: true

### D1.2 — entries: every well-formed record, oldest first
interface: true

## D2 — Put
status: adopted
serves: [P1, P7]
depends-on: [D1.1, D6]
component: true
refs: [src/trash/put.py]

Checks the path, reserves a name, moves the file in. A failed move gives the
name back.

## D3 — Restore and list
status: adopted
serves: P5
depends-on: [D1.2, D6]
component: true
refs: [src/trash/restore.py]

## D4 — Empty
status: adopted
serves: [P1, P6]
depends-on: D1.2
component: true
refs: [src/trash/empty.py]

The only code that destroys data.

## D5 — The command line
status: adopted
serves: P3
depends-on: [D2, D3, D4]
component: true
refs: [src/trash/cli.py]

rm's grammar for deleting; options, never bare words, for everything else.

## D6 — The move
status: adopted
serves: P2
hides: how a move across filesystems is made safe
refs: [src/trash/move.py]

## Environment models

## A3 — Desktop file managers read the freedesktop.org trash layout
status: adopted
source: https://specifications.freedesktop.org/trash-spec/latest/

## X1 — Files on other filesystems go to the home trash, not a trash on their own volume
status: adopted
assumes: A1

The freedesktop layout allows a per-volume trash, which would keep a rename
possible. trash copies instead: slower, and it spends home-disk space, which
is acceptable while A1 holds.
