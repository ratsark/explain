# L0 — Purpose

## Mission

## G0 — Deleting from a shell can be taken back
status: adopted

`rm` is forever. One mistyped glob in a shell destroys work with no way back,
while every desktop has had a trash can for forty years. trash makes deleting
from the command line reversible until the user decides otherwise, without
asking them to change how they type.

## Goals

## G1 — A deletion made by mistake can be undone
status: adopted

The user gets back any file they trashed, with its name and contents, at the
path it came from, until they choose to destroy it.

## G2 — It fits where rm already is
status: adopted

Muscle memory, aliases and scripts that call `rm` keep working when `rm`
becomes `trash`. A safety tool people must remember to use protects nobody.
Deletions made some other way (`rm` itself, an editor, `git clean`) are
outside trash's reach; this goal is how it earns being the default.

## G3 — The space held by deleted files comes back on the user's terms
status: adopted

A trash that is never emptied is a disk that silently fills.

## Constraints

## C1 — trash never destroys data the user did not explicitly ask to destroy
status: adopted

Not the file being trashed, not whatever sits at a restore target, not the
target of a symlink, not anything already in the trash. Only an explicit
`--empty` destroys.

## C2 — At every instant a trashed file exists in exactly one place
status: adopted

Through a crash, a full disk or a kill mid-move, the file is at its original
path or in the trash: never in neither, never half in both.

## Environment

### Assumptions

## A1 — Most deletions are of files on the same filesystem as the user's home
status: adopted

True of a laptop or workstation; false of an external drive or a network
mount, where the design pays in time and home-disk space.

## A2 — People notice a mistaken deletion within days, not months
status: adopted

## Risks

### Hazards

## H1 — The trash fills the disk without anyone noticing
status: adopted

Measured as the trash's size against free space on the home filesystem.

## Evaluation criteria and priorities

## E1 — When safety and speed conflict, safety wins
status: adopted

A slower delete is acceptable; a lost file is not.
