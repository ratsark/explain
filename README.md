# explain

A lightweight, modular design-document format in plain markdown, modelled on
Nancy Leveson's intent specifications, and a dependency-free tool that queries
and checks it. Every item in a spec is linked to the ends it serves and the
means that realize it, so `explain G2` tells you what G2 is, `explain why G2`
tells you what it exists for, `explain how G2` what realizes it, and
`explain serves G2` everything that would need a second look if it changed. The level set is chosen per domain, and
one system's spec can be a component of another's across repositories.

```
python3 -m explain check examples/cas      # errors fail; incompleteness is reported
python3 -m explain G2 examples/cas         # what is G2
python3 -m explain why D2 examples/cas     # the chain up to the goals, into the parent spec
python3 -m explain how G1 examples/cas     # the tree of means below it
python3 -m explain serves G1 examples/cas  # the re-evaluation sweep: everything that would need a second look
```

Python 3.9+, standard library only. Copy the `explain/` directory into any
repo's `tools/` to use it there.

**Starting a spec:** `python3 -m explain init myspec --profile software` (or
`--profile business`) scaffolds a directory with a manifest, one file per level
holding the profile's sections, and a README of the rules. Fill L0, run
`check`, and work downward. Two specs nest by naming each other in `spec.yaml`.

## Bugs, feature requests, questions

File a GitHub issue on this repo; it is watched, and replies come back on the
issue. From a shell with `gh` authenticated:

```
gh issue create -R ratsark/explain --title "check: false unknown-id on L4-V1.2" --label bug \
  --body "$(printf 'What happened: ...\nExpected: ...\nRepro: explain check spec (spec/L4-realization.md:12)\n%s' "$(explain --version)")"
gh issue list -R ratsark/explain --state open          # what is already filed
gh issue view -R ratsark/explain 12 --comments         # read the reply
gh issue comment -R ratsark/explain 12 --body "..."    # continue the thread
```

Labels: `bug` (the tool did something wrong, or the format is ambiguous),
`enhancement` (a check, query or capability you need), `question` (how to
express something, or what a report means). Include the command you ran, the
spec path, the smallest item or file that shows the problem, and the output
of `explain --version`. Templates under `.github/ISSUE_TEMPLATE/` say the same.

Status: format v0 and tool v0.1; see `ARCHITECTURE.md` for the format,
`PLAN.md` for where it is going, `examples/` for a nested pair of worked specs, and
`research/` for the background reading.
