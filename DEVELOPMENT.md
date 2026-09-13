# Development

Managed by Claude. Python 3.9+ standard library only; no install step.

## Layout

```
ARCHITECTURE.md       the format and tool design (the spec of the spec)
PLAN.md               phases and acceptance criteria
MISSION_STATEMENT.md  approved 2026-09-12
research/             background reports and synthesis
examples/aircraft/    illustrative parent spec
examples/cas/         illustrative child spec (collision avoidance), nested under aircraft
explain/              the tool
  miniyaml.py           strict YAML subset (no PyYAML)
  profile.py            level sets, kinds, section trees
  profiles/software.yaml
  parse.py              directory layout, items, headers, links; every regex
  checks.py             errors, reports, queries, export
  cli.py                commands
tests/                unittest suite; specs are built in temp dirs per test
```

## Test

```
python3 -m unittest discover -s tests -t .
```

This is the gate. Every error and report code in ARCHITECTURE.md section 9 has
a test that triggers it and asserts the severity and count.
`tests/test_example.py` is a golden test on the example pair. Adopting
projects keep their own corpus checks in their own repos.

## Run

```
python3 -m explain check examples/cas             # errors and reports; exit 1 on errors
python3 -m explain check --strict --quiet PATH    # release-gate mode: reports fail; errors only printed
python3 -m explain show G2 examples/cas           # what is G2 (case-insensitive; old ids via was:)
python3 -m explain G2 examples/cas                # same: a bare id means show
python3 -m explain serves G1 examples/cas         # everything downstream, transitively
python3 -m explain why D2 examples/cas            # the upward chain, into the parent spec
python3 -m explain orphans examples/cas
python3 -m explain isolated examples/cas         # items with no link either way, by level
python3 -m explain questions examples/cas        # open questions (kind Q), what each blocks
python3 -m explain outline examples/cas           # levels, files, items, sections not yet present
python3 -m explain export -o cas.index.json examples/cas
python3 -m explain assumptions examples/cas
python3 -m explain accept --all examples/cas      # start tracking drift: record every link's target fingerprint
python3 -m explain accept P2 examples/cas         # after re-reading P2 against its changed targets
python3 -m explain drift examples/cas             # accepted links whose targets changed; what to re-read
python3 -m explain review examples/cas            # status counts per level
python3 -m explain review L1 examples/cas         # walk L1 item by item (the design-review flow)
python3 -m explain coupling examples/cas          # components: cohesion, cycles, boundary crossings, cross-cutting items
python3 -m explain interfaces D1 examples/cas     # a component's guarantees and requirements
python3 -m explain --patterns                     # every regex and every declared miss
```

The package directory also runs directly, from anywhere, with no install:

```
python3 /path/to/explain/explain check /path/to/some/spec
```

Exit codes: 0 found or clean; 1 errors, or a query that found nothing; 2 usage.

## Conventions

- Every pattern the tool matches lives at the top of `parse.py` and is printed
  by `--patterns`. A new blind spot goes in `DECLARED_MISSES` there.
- A new check needs a test in `tests/test_checks.py` that triggers it.
- This repo is public. Nothing specific to an adopting project goes here:
  no quoted goals, no internal paths, no incident details. Adopters vendor the
  tool by copying the `explain/` directory into their `tools/` and run it with
  `python3 tools/explain`; their integration notes live with them.
