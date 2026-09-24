# trash: an rm you can take back

A small, working command-line program with a complete explain spec behind
it. It is the walkthrough in the top-level README.

- `spec/` is the design: 45 items over five levels, from the mission (G0) to
  the source files (I1 to I6) and the tests (V1).
- `src/trash/` is the program. Each module names the rows it realizes on a
  `spec:` line; `tests/test_trash.py` names the rows each test class guards
  on a `spec-guard:` line.
- `spec/code-index.json` is those citations gathered by `explain scan`, so
  `explain drift` can tell when a row that code cites has changed.

Try it from this directory:

```
explain g1                 # what is G1
explain why s4             # why the trash keeps things for 30 days
explain how c2             # the code that keeps a file from being lost mid-move
explain covers src/trash/put.py
explain check
```

Run the program itself (it uses `$XDG_DATA_HOME/Trash`, the desktop trash):

```
PYTHONPATH=src python3 -m trash -v some-file
PYTHONPATH=src python3 -m trash --list
PYTHONPATH=src python3 -m trash --restore some-file
python3 -m unittest discover tests
```

After changing a row, re-read what cites it, then record that:

```
explain accept I4                                # a spec row that serves it
explain scan src/trash/empty.py --accept spec    # the code's citations
explain scan . -o spec/code-index.json spec      # refresh the gathered index
```
