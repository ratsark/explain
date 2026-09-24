# L3 — Specs

## Specs

## S1 — The record is written and flushed before the file moves
status: adopted
serves: D2

A crash between the two steps leaves a record with no file, which `--empty`
clears. The other order could leave a file in the trash that nothing traces
back to where it came from.

## S2 — Name collisions become NAME.2, NAME.3, and so on, claimed by exclusive create
status: adopted
serves: D1.1
part-of: D1

The exclusive create of the record is the lock: two trash processes can
never claim the same name.

## S9 — A record is a freedesktop .trashinfo file: the original path percent-encoded, the deletion time in local time
status: adopted
serves: D1
part-of: D1

A record that fails to parse is skipped by every command and never deleted:
it may be another program's.

## S3 — A directory needs -r, as with rm
status: adopted
serves: D2

## S4 — `--empty` with no argument destroys entries trashed more than 30 days ago
status: adopted
serves: D4
assumes: A2

`--older-than DAYS` changes the window; `--all` empties everything.

## S5 — Restore never overwrites: a taken path is an error that names --to
status: adopted
serves: D3

Restoring over an existing file would destroy it, which C1 forbids.

## S6 — Exit status follows rm: 0 when every file was trashed, 1 when any was not, 2 for a usage error with nothing moved
status: adopted
serves: D5

## S7 — A symlink is moved as a link, across filesystems too
status: adopted
serves: [D2, D6]

## S10 — Across filesystems: copy, flush every copied file and directory, then remove the original
status: adopted
serves: D6
part-of: D6

If the copy fails, or the disk fills, the partial copy is removed and the
original is untouched. Only a copy that is on disk replaces the original.

## S8 — Management actions are options, never words
status: adopted
serves: D5

`trash list` trashes a file named `list`, exactly as `rm list` would remove
it. Listing is `trash --list`.

## Open questions

## Q1 — Should trash warn when the can grows past some share of free space?
status: proposed
serves: D4

H1 is controlled today only by the retention default. A warning would make
the growth visible; what share, and printed by which command?
