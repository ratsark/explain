# L4 — Realization

The modules that realize the components, and the test files that verify the
decisions. `python3 -m unittest discover -s tests -t .` is the gate.

## Code

## I1 — explain/parse.py
status: adopted
built: shipped
serves: [S2, S3, S4, S5, S6, S10]
part-of: D1
refs: [explain/parse.py]

## I2 — explain/checks.py
status: adopted
built: shipped
serves: [S11, S12, S13, S14, S15, S16, S17]
part-of: D2
refs: [explain/checks.py]

## I3 — explain/components.py
status: adopted
built: shipped
serves: S11
part-of: D3
refs: [explain/components.py]

## I4 — explain/cli.py
status: adopted
built: shipped
serves: [S18, S13]
part-of: D4
refs: [explain/cli.py]

## I5 — explain/profile.py and the shipped profiles
status: adopted
built: shipped
serves: [S6, S5]
part-of: D5
refs: [explain/profile.py, explain/profiles/software.yaml]

## I6 — explain/miniyaml.py
status: adopted
built: shipped
serves: S11
part-of: D6
refs: [explain/miniyaml.py]

## I7 — The package runs as a directory
status: adopted
built: shipped
serves: S18
part-of: D4
refs: [explain/__main__.py]

`python3 path/to/explain check DIR` works with no install, which is how
adopters vendor it.

## Guards

## V1 — tests/test_parse.py
status: adopted
built: shipped
verifies: [D1, S2, S3, S4, S5]
part-of: D1
refs: [tests/test_parse.py]

## V2 — tests/test_miniyaml.py
status: adopted
built: shipped
verifies: D6
part-of: D6
refs: [tests/test_miniyaml.py]

## V3 — tests/test_checks.py
status: adopted
built: shipped
verifies: [S11, S12, S14, S16, S6, S7, S8, S9, D5]
part-of: D2
refs: [tests/test_checks.py]

One test per error and report code.

## V4 — tests/test_cross_spec.py
status: adopted
built: shipped
verifies: [D12, S15, D2.2]
part-of: D2
refs: [tests/test_cross_spec.py]

## V5 — tests/test_drift.py
status: adopted
built: shipped
verifies: [D10, D13, S17]
part-of: D2
refs: [tests/test_drift.py]

## V6 — tests/test_components.py
status: adopted
built: shipped
verifies: [D3, D11]
part-of: D3
refs: [tests/test_components.py]

## V7 — tests/test_cli.py
status: adopted
built: shipped
verifies: [D4, S13, S18]
part-of: D4
refs: [tests/test_cli.py]

## V8 — tests/test_example.py
status: adopted
built: shipped
verifies: D12
part-of: D2
refs: [tests/test_example.py, examples/aircraft, examples/cas]

The nested example pair reports exactly what it was written to show.

## V9 — tests/test_dogfood.py
status: adopted
built: shipped
verifies: [G1, G2, C1, C2]
part-of: D2
refs: [tests/test_dogfood.py, spec]

This spec checks with zero errors, no orphans, and no suspect links; every
ARCHITECTURE.md section is cited by at least one row.

## V10 — tests/test_covers.py
status: adopted
built: shipped
verifies: [S21, S22, S23]
part-of: D2
refs: [tests/test_covers.py]

A citation without a fingerprint is untracked; with one, it goes suspect
when the row's design body changes, and `covers` says so on the line.
