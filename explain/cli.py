"""Command line: check, show, serves, why, orphans, outline, export, assumptions."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .checks import downstream, export_index, externals, inbound, run_checks, upstream
from .parse import DOWNSTREAM_RELATIONS, RELATIONS, parse_spec, patterns_text, split_qid


def _spec(path):
    root = Path(path)
    if not root.is_dir():
        print(f"error: {path} is not a directory", file=sys.stderr)
        return None
    return parse_spec(root)


def _find(spec, raw):
    """Resolve an id as typed (G2, g2, L4-V1, 6.2 no) to an item, or None."""
    q = split_qid(raw.strip().upper() if ":" not in raw else raw.strip())
    if q is None:
        q = split_qid(raw.strip())
    if q is None:
        return None, f"{raw!r} is not an id"
    ns, iid = q
    if ns not in (None, spec.name):
        return None, f"{raw}: use 'show' inside spec {ns!r}"
    it = spec.items.get(iid)
    if it is None:
        # maybe an old id
        for cand in spec.items.values():
            if iid in (cand.header.get("was") or []):
                return cand, f"note: {iid} was re-homed as {cand.id}"
        return None, f"{iid} is not defined in spec {spec.name!r}"
    return it, None


def cmd_check(args):
    spec = _spec(args.path)
    if spec is None:
        return 2
    findings = run_checks(spec)
    errors = [x for x in findings if x.severity == "error"]
    reports = [x for x in findings if x.severity == "report"]
    for x in findings:
        if args.quiet and x.severity == "report":
            continue
        print(x.format())
    n_items = len(spec.items)
    print(f"\n{spec.name or '(unnamed)'}: {n_items} items in {len(spec.levels)} levels; "
          f"{len(errors)} errors, {len(reports)} reports"
          + (" (reports promoted to errors by --strict)" if args.strict and reports else ""))
    if not spec.levels:
        print("note: no L<n>- entries found; nothing was checked beyond the manifest")
    if errors or (args.strict and reports):
        return 1
    return 0


def cmd_show(args):
    spec = _spec(args.path)
    if spec is None:
        return 2
    it, note = _find(spec, args.id)
    if it is None:
        print(f"error: {note}", file=sys.stderr)
        return 1
    if note:
        print(note)
    desc = spec.profile.kind_description(it.kind) or "?"
    print(f"{it.id} — {it.title}")
    print(f"  {desc} at L{it.level} ({spec.levels[it.level].name}); {it.file}:{it.line}")
    if it.parent_id:
        print(f"  refines: {it.parent_id}")
    for k, v in it.header.items():
        print(f"  {k}: {_fmt(v)}")
    by_rel = {}
    for l in it.links:
        by_rel.setdefault(l.relation, []).append(l.target + (" (inline)" if l.inline else ""))
    for rel, targets in by_rel.items():
        print(f"  {rel}: {', '.join(targets)}")
    idx = inbound(spec, tuple(RELATIONS))
    inv = {}
    for other, rel in idx.get(it.id, []):
        inv.setdefault(rel, []).append(other.id)
    kids = [i.id for i in spec.items.values() if i.parent_id == it.id]
    if kids:
        print(f"  refined-by: {', '.join(kids)}")
    for rel, ids in inv.items():
        print(f"  {_inverse(rel)}: {', '.join(sorted(ids, key=_idkey))}")
    body = it.body
    if body:
        print()
        for line in body.splitlines():
            print(f"  {line}")
    return 0


def _inverse(rel):
    return {
        "serves": "served-by", "assumes": "assumed-by", "discharged-by": "discharges",
        "verifies": "verified-by", "depends-on": "depended-on-by",
        "conflicts-with": "conflicts-with", "supersedes": "superseded-by",
    }[rel]


def _fmt(v):
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v) + "]"
    return str(v)


def _idkey(iid):
    q = split_qid(iid)
    if not q:
        return (9, iid)
    import re
    m = re.match(r"^(?:L(\d+)-)?([A-Z]+)(\d+)((?:\.\d+)*)$", q[1])
    nums = [int(m.group(3))] + [int(x) for x in m.group(4).split(".") if x]
    return (int(m.group(1) or -1), m.group(2), nums)


def cmd_serves(args):
    spec = _spec(args.path)
    if spec is None:
        return 2
    it, note = _find(spec, args.id)
    if it is None:
        print(f"error: {note}", file=sys.stderr)
        return 1
    if note:
        print(note)
    rows = downstream(spec, it.id)
    print(f"downstream of {it.id} — {it.title} (via {', '.join(DOWNSTREAM_RELATIONS)} and refinement):")
    if not rows:
        print("  nothing. Nothing serves, assumes, verifies or depends on it yet.")
        return 1
    by_level = {}
    for item, rel, via, depth in rows:
        by_level.setdefault(item.level, []).append((item, rel, via, depth))
    for n in sorted(by_level):
        print(f"  L{n} ({spec.levels[n].name}):")
        for item, rel, via, depth in sorted(by_level[n], key=lambda r: _idkey(r[0].id)):
            print(f"    {item.id:10} {item.title}  ({rel} {via}, depth {depth})")
    print(f"  {len(rows)} items")
    return 0


def cmd_why(args):
    spec = _spec(args.path)
    if spec is None:
        return 2
    it, note = _find(spec, args.id)
    if it is None:
        print(f"error: {note}", file=sys.stderr)
        return 1
    if note:
        print(note)
    tree = upstream(spec, it.id, externals(spec))

    def walk(node, indent):
        iid, title, kids = node
        print(f"{'  ' * indent}{iid} — {title}")
        for k in kids:
            walk(k, indent + 1)
    walk(tree, 0)
    if not tree[2]:
        print("  (serves nothing: it is a top-level item, an orphan, or derived)")
    return 0


def cmd_orphans(args):
    spec = _spec(args.path)
    if spec is None:
        return 2
    rows = [x for x in run_checks(spec) if x.code in ("orphan", "derived-from-parent")]
    for x in rows:
        print(x.format())
    print(f"{len(rows)} orphans")
    return 0 if rows else 1


def cmd_outline(args):
    spec = _spec(args.path)
    if spec is None:
        return 2
    print(f"{spec.name or '(unnamed)'}: {spec.manifest.get('title') or ''}  [profile {spec.profile.name}"
          + (f", adopted through {spec.manifest.get('adopted-through')}" if spec.manifest.get("adopted-through") else "") + "]")
    for n in spec.profile.level_numbers():
        lv = spec.profile.levels[n]
        lf = spec.levels.get(n)
        if lf is None:
            print(f"L{n} {lv.name}: (absent)")
            continue
        items = [i for i in spec.items.values() if i.level == n]
        print(f"L{n} {lv.name}: {lf.entry} — {len(items)} items in {len(lf.files)} file(s)")
        for rel in lf.files:
            print(f"  {rel}")
            for i in sorted((i for i in items if i.file == rel), key=lambda i: i.line):
                ind = "    " + ("  " * i.number.count("."))
                st = f" [{i.status}]" if i.status else ""
                print(f"{ind}{i.id} — {i.title}{st}")
        present = {t.lower() for t, _, _, _ in spec.sections.get(n, [])}
        missing = [t for t in lv.section_titles() if t.lower() not in present]
        if missing:
            print(f"  sections not yet present: {', '.join(missing)}")
    return 0


def cmd_export(args):
    spec = _spec(args.path)
    if spec is None:
        return 2
    data = export_index(spec)
    text = json.dumps(data, indent=2, sort_keys=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.output}: {len(data['items'])} items, {len(data['links'])} links")
    else:
        print(text)
    return 0


def cmd_assumptions(args):
    spec = _spec(args.path)
    if spec is None:
        return 2
    idx = inbound(spec, ("assumes",))
    rows = [i for i in spec.items.values() if i.kind == "A"]
    for it in sorted(rows, key=lambda i: _idkey(i.id)):
        d = [l.target for l in it.links_of("discharged-by")]
        users = sorted({o.id for o, _ in idx.get(it.id, [])}, key=_idkey)
        print(f"{it.id} — {it.title}")
        print(f"  discharged-by: {', '.join(d) if d else '(nothing)'}")
        print(f"  assumed-by: {', '.join(users) if users else '(nothing)'}")
    print(f"{len(rows)} assumptions, {sum(1 for i in rows if not i.links_of('discharged-by'))} undischarged")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="explain", description="Query and check a means-ends design spec.")
    p.add_argument("--version", action="version", version=f"explain {__version__}")
    p.add_argument("--patterns", action="store_true", help="print every pattern the tool matches and every declared miss, then exit")
    sub = p.add_subparsers(dest="cmd")

    def add(name, fn, help_, id_arg=False):
        s = sub.add_parser(name, help=help_)
        if id_arg:
            s.add_argument("id")
        s.add_argument("path", nargs="?", default=".", help="spec directory (default: .)")
        s.set_defaults(fn=fn)
        return s

    s = add("check", cmd_check, "errors and reports for a spec; exit 1 on errors")
    s.add_argument("--strict", action="store_true", help="treat reports as errors")
    s.add_argument("--quiet", action="store_true", help="print errors only")
    add("show", cmd_show, "what is ID: header, links, computed inverses, body", id_arg=True)
    add("serves", cmd_serves, "everything downstream of ID, transitively (the re-evaluation sweep)", id_arg=True)
    add("why", cmd_why, "the upward chain from ID to the top", id_arg=True)
    add("orphans", cmd_orphans, "items that serve nothing and are not marked derived")
    add("outline", cmd_outline, "levels, files, items, and profile sections not yet present")
    s = add("export", cmd_export, "the spec's index JSON for other specs to cite")
    s.add_argument("-o", "--output", help="write to this file instead of stdout")
    add("assumptions", cmd_assumptions, "every assumption, what discharges it, who assumes it")
    return p


COMMANDS = ("check", "show", "serves", "why", "orphans", "outline", "export", "assumptions")


def main(argv=None):
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    # `explain G2` is `explain show G2`: an id in first position selects show.
    if argv and argv[0] not in COMMANDS and not argv[0].startswith("-") and split_qid(argv[0].upper()):
        argv.insert(0, "show")
    args = parser.parse_args(argv)
    if args.patterns:
        print(patterns_text())
        return 0
    if not args.cmd:
        parser.print_help()
        return 2
    return args.fn(args)
