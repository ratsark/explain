# Mission Statement

Approved by the user 2026-09-12.

This project defines a lightweight, modular design-document format and a tool
for querying and checking it. A spec is a means-ends hierarchy in plain
markdown: purpose at the top, realization at the bottom, every item linked to
the ends it serves and the means that realize it. The level set is chosen per
domain, not fixed. One system's spec can be a component of another's, across
directories, repos, or organizations, with the contract between them explicit.

The format cannot stop a layer from drifting away from its neighbours; it makes
drift visible and keeps the list of what to re-read exact. Broken structure (a
reference to something that no longer exists, an id used twice) is an error.
Incompleteness (a goal nothing serves yet, an assumption nobody has discharged)
is a report, never a failure: a spec grows level by level and is expected to be
unfinished below the line of what has been agreed. Every pattern the tool
matches is declared, every answer it gives could be reproduced by hand from the
text, and it says what it cannot see rather than returning a confident empty
result.

Humans write the top; agents write the bottom. Success is a project whose
design review proceeds level by level from agreed goals, whose agents can
answer "why does this exist" and "what depends on this" with one command, and
whose spec is still trusted a year in.
