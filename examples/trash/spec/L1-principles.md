# L1 — Principles

## Principles

## P1 — Destruction lives in one place
status: adopted
serves: [G1, C1]

Every path through trash moves data except `--empty`, which is the only one
that unlinks it. One small module to audit for C1, and one command the user
has to type on purpose.

## P2 — Move by rename; when a rename is impossible, copy, flush, and only then remove
status: adopted
serves: [C2, E1]

A rename is atomic. A copy is not, so the original stays until the copy is
safely on disk, and a failed copy is cleaned up with the original untouched.

## P3 — Speak rm's grammar, and refuse what cannot be honoured
status: adopted
serves: [G2, C1]

rm's everyday flags mean what they mean in rm. An rm option trash does not
implement stops the whole command before anything moves: quietly ignoring
`--one-file-system` would do something the user did not ask for.

## P4 — The trash is plain files anyone can read
status: adopted
serves: G1

No database and no index to corrupt. A person with `ls` and `mv` can restore
by hand, and a desktop file manager shows the same entries.

## P5 — Restoring is putting in reverse: same place, same name, never over anything
status: adopted
serves: [G1, C1]

## P6 — Space is reclaimed oldest first, and only when asked
status: adopted
serves: [G3, H1]
assumes: A2

## Never-list

## P7 — Never follow a symlink
status: adopted
serves: C1

A link is trashed, restored and emptied as a link. Resolving it would move,
or destroy, a file the user never named.
