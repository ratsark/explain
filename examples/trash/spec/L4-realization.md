# L4 — Realization

## Code

## I1 — src/trash/can.py
status: adopted
built: shipped
serves: [S2, S9]
part-of: D1
refs: [src/trash/can.py]

## I2 — src/trash/put.py
status: adopted
built: shipped
serves: [S1, S3, S7]
part-of: D2
refs: [src/trash/put.py]

## I3 — src/trash/restore.py
status: adopted
built: shipped
serves: S5
part-of: D3
refs: [src/trash/restore.py]

## I4 — src/trash/empty.py
status: adopted
built: shipped
serves: S4
part-of: D4
refs: [src/trash/empty.py]

## I5 — src/trash/cli.py
status: adopted
built: shipped
serves: [S6, S8]
part-of: D5
refs: [src/trash/cli.py]

## I6 — src/trash/move.py
status: adopted
built: shipped
serves: [S7, S10]
part-of: D6
refs: [src/trash/move.py]

## Guards

## V1 — tests/test_trash.py
status: adopted
built: shipped
verifies: [C1, C2]
refs: [tests/test_trash.py]

The safety case in one file. Each test class names the rows it guards on a
`spec-guard:` line, which `explain scan tests` turns into links that
`explain serves` and `explain drift` follow.
