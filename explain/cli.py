"""Command line: check, show, serves, why, orphans, outline, export, assumptions."""

import argparse
import json
import re
import sys
from pathlib import Path

from . import __version__
from .checks import accept, connectivity, downstream, export_index, externals, find_alias, inbound, run_checks, suspects, upstream
from .components import Components
from .parse import ACCEPTED_FILE, DOWNSTREAM_RELATIONS, RELATIONS, parse_spec, patterns_text, save_accepted, split_qid


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
        it = find_alias(spec, raw)
        if it is not None:
            return it, f"note: {raw!r} is an alias of {it.id}"
        return None, f"{raw!r} is not an id or a known alias (aka:)"
    ns, iid = q
    if ns not in (None, spec.name):
        return None, f"{raw}: use 'show' inside spec {ns!r}"
    it = spec.items.get(iid)
    if it is None:
        by_alias = find_alias(spec, raw)
        if by_alias is not None:
            return by_alias, f"note: {raw!r} is an alias of {by_alias.id}"
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
    isolated, built = connectivity(spec)
    print(f"\n{spec.name or '(unnamed)'}: {n_items} items in {len(spec.levels)} levels; "
          f"{len(errors)} errors, {len(reports)} reports"
          + (" (reports promoted to errors by --strict)" if args.strict and reports else ""))
    if n_items:
        pct = 100 * len(isolated) // n_items
        built_line = ", ".join(f"{k} {v}" for k, v in sorted(built.items(), key=lambda kv: (kv[0] == "unstated", kv[0])))
        print(f"isolated (no link either way): {len(isolated)} of {n_items} ({pct}%); built: {built_line}")
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
    print(f"  {desc} at L{it.level} ({spec.levels[it.level].name}); {it.file}:{it.line}; fingerprint {spec.fingerprint(it.id)}")
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
    outgoing = {(l.relation, split_qid(l.target)[1] if split_qid(l.target) else l.target) for l in it.links}
    for other, rel in idx.get(it.id, []):
        if rel == "conflicts-with" and (rel, other.id) in outgoing:
            continue   # symmetric and already shown as outgoing
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


def cmd_isolated(args):
    spec = _spec(args.path)
    if spec is None:
        return 2
    isolated, _ = connectivity(spec)
    if not isolated:
        print("no isolated items: every item has at least one link or refinement edge")
        return 1
    by_level = {}
    for it in isolated:
        by_level.setdefault(it.level, []).append(it)
    for n in sorted(by_level):
        rows = sorted(by_level[n], key=lambda i: (str(i.file), i.line))
        print(f"L{n} ({spec.levels[n].name}): {len(rows)}")
        for it in rows:
            print(f"  {it.id:10} {it.title[:70]}  ({it.file}:{it.line})")
    print(f"{len(isolated)} isolated of {len(spec.items)} ({100 * len(isolated) // len(spec.items)}%). "
          "This count only falls as items are linked; it cannot be moved by trading one report for another.")
    return 0


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


def _split_targets_and_path(targets):
    """For commands taking ids then an optional path: the last token is the path if it is a directory."""
    targets = list(targets)
    if targets and Path(targets[-1]).is_dir():
        return targets[:-1], targets[-1]
    return targets, "."


def cmd_accept(args):
    ids, path = _split_targets_and_path(args.targets)
    spec = _spec(path)
    if spec is None:
        return 2
    if not ids and not args.all:
        print("error: give item ids to accept, or --all", file=sys.stderr)
        return 2
    wanted = None
    if ids:
        wanted = set()
        for raw in ids:
            it, note = _find(spec, raw)
            if it is None:
                print(f"error: {note}", file=sys.stderr)
                return 1
            wanted.add(it.id)
    ext = externals(spec)
    new, updated, unchanged, unresolved = accept(spec, ext, wanted)
    save_accepted(spec.root, spec.accepted)
    print(f"accepted {new + updated + unchanged} link(s): {new} new, {updated} re-accepted after a change, {unchanged} unchanged"
          + (f"; {unresolved} skipped (target unresolvable)" if unresolved else "")
          + f"\nwrote {ACCEPTED_FILE}")
    return 0


def cmd_drift(args):
    spec = _spec(args.path)
    if spec is None:
        return 2
    ext = externals(spec)
    rows = suspects(spec, ext)
    tracked = len(spec.accepted)
    if not rows:
        print(f"no drift: {tracked} accepted link(s) all point at unchanged targets"
              + ("" if tracked else f" (nothing is tracked yet; `explain accept --all` to start)"))
        return 1
    by_target = {}
    for it, link, old, cur in rows:
        by_target.setdefault((link.target, old, cur), []).append((it, link))
    for (target, old, cur), deps in sorted(by_target.items()):
        title = ""
        q = split_qid(target)
        if q and q[0] in (None, spec.name) and q[1] in spec.items:
            title = " — " + spec.items[q[1]].title
        print(f"{target}{title} changed (accepted {old}, now {cur}). Re-read:")
        for it, link in sorted(deps, key=lambda d: _idkey(d[0].id)):
            print(f"    {it.id:10} {it.title}  ({link.relation}; {link.file}:{link.line})")
        print(f"  then: explain accept {' '.join(sorted({it.id for it, _ in deps}, key=_idkey))}")
    print(f"{len(rows)} suspect link(s) across {len(by_target)} changed target(s); {tracked} accepted in total")
    return 0


def cmd_review(args):
    """Walk a level item by item: what the owner or a chair reads to sign a level off."""
    if args.level and Path(args.level).is_dir() and args.path == ".":
        args.path, args.level = args.level, None     # `review PATH` with no level
    spec = _spec(args.path)
    if spec is None:
        return 2
    findings = run_checks(spec)
    by_item = {}
    for x in findings:
        if x.code in ("orphan", "unserved", "unrealized", "unguarded", "undischarged-assumption", "skip-level", "suspect-link", "derived-from-parent"):
            by_item.setdefault(x.message.split()[0].rstrip(":,"), []).append(x.code)
    levels = spec.profile.level_numbers()
    if args.level:
        m = re.match(r"^L?(\d+)$", args.level.strip(), re.IGNORECASE)
        if not m or int(m.group(1)) not in levels:
            print(f"error: level must be one of {', '.join('L%d' % n for n in levels)}", file=sys.stderr)
            return 2
        levels = [int(m.group(1))]
    adopted_through = str(spec.manifest.get("adopted-through") or "")
    for n in levels:
        lv = spec.profile.levels[n]
        items = sorted((i for i in spec.items.values() if i.level == n and i.parent_id is None), key=lambda i: (str(i.file), i.line))
        statuses = {}
        for i in items:
            statuses[i.status or "(none)"] = statuses.get(i.status or "(none)", 0) + 1
        signed = f"; signed off through {adopted_through}" if adopted_through else ""
        print(f"L{n} {lv.name}: {len(items)} items — " + ", ".join(f"{k} {v}" for k, v in sorted(statuses.items())) + signed)
        if not args.level:
            continue
        for i in items:
            flags = by_item.get(i.id, [])
            tag = ", ".join(x for x in (i.status, i.header.get("built")) if x)
            print(f"\n{i.id} — {i.title}" + (f"  [{tag}]" if tag else "") + (f"  ⚑ {', '.join(flags)}" if flags else ""))
            for rel in ("serves", "assumes", "verifies", "depends-on", "conflicts-with", "supersedes", "discharged-by"):
                targets = [l.target for l in i.links_of(rel)]
                if targets:
                    named = []
                    for t in targets:
                        q = split_qid(t)
                        tt = spec.items.get(q[1]).title if q and q[0] in (None, spec.name) and q[1] in spec.items else ""
                        named.append(f"{t} ({tt})" if tt else t)
                    print(f"  {rel}: {', '.join(named)}")
            kids = [k for k in spec.items.values() if k.parent_id == i.id]
            if kids:
                print(f"  refined by: {', '.join(k.id for k in sorted(kids, key=lambda k: _idkey(k.id)))}")
            for key in ("owner", "source", "refs", "was"):
                if key in i.header:
                    print(f"  {key}: {_fmt(i.header[key])}")
            body = i.body.strip()
            if body:
                lines = body.splitlines()
                shown = lines if args.full else lines[:args.lines]
                for line in shown:
                    print(f"    {line}")
                if len(lines) > len(shown):
                    print(f"    ... ({len(lines) - len(shown)} more lines; --full to show)")
    return 0


def cmd_coupling(args):
    spec = _spec(args.path)
    if spec is None:
        return 2
    comps = Components(spec)
    if not comps.nodes:
        print("no components: nothing declares part-of, hides, or an interface sub-item")
        return 1
    rows = comps.stats()
    print(f"{len(rows)} components ({len(spec.items)} items; {sum(r['members'] for r in rows.values())} inside a component, "
          f"{len(spec.items) - sum(r['members'] for r in rows.values())} cross-cutting)\n")
    print(f"{'component':10} {'members':>7} {'internal':>8} {'out ok':>6} {'crossing':>8} {'in':>4} {'cohesion':>8}  title")
    for c, r in sorted(rows.items(), key=lambda kv: (kv[1]['cohesion'] if kv[1]['cohesion'] is not None else 2, kv[0])):
        coh = "-" if r["cohesion"] is None else f"{r['cohesion']:.2f}"
        print(f"{c:10} {r['members']:7} {r['internal']:8} {r['out_ok']:6} {r['out_crossing']:8} {r['in']:4} {coh:>8}  {spec.items[c].title[:50]}")
    edges = comps.component_edges()
    if edges:
        print("\ncomponent-to-component links (from -> to: count):")
        for (a, b), n in sorted(edges.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {a} -> {b}: {n}")
    cycles = comps.cycles()
    print(f"\ncycles: {len(cycles)}" + ("".join(f"\n  {' -> '.join(cy)} -> {cy[0]}" for cy in cycles)))
    crossings = comps.crossings()
    print(f"boundary crossings: {len(crossings)}" + ("".join(f"\n  {s.id} {l.relation} {l.target}  ({cx} -> inside {cy})" for s, l, cx, cy in crossings[:20]))
          + ("\n  ..." if len(crossings) > 20 else ""))
    ua = comps.unassigned_inside()
    print(f"\nitems outside every component that link into a component's internals (candidates for part-of): {len(ua)}")
    for iid, cs in ua[:20]:
        print(f"  {iid:8} -> inside {', '.join(cs)}  {spec.items[iid].title[:50]}")
    if len(ua) > 20:
        print("  ...")
    cc = comps.cross_cutting()
    print(f"\ncross-cutting items (outside every component) linked from more than one component: {sum(1 for _, s in cc if len(s) > 1)}")
    for tid, s in cc[:15]:
        if len(s) > 1:
            print(f"  {tid:8} <- {len(s)} components: {', '.join(sorted(s))}  {spec.items[tid].title[:50]}")
    od = comps.overdetermined()
    print(f"\noverdetermined items (serves targets in 3+ components): {len(od)}")
    for it, cs in od[:15]:
        print(f"  {it.id:8} -> {', '.join(cs)}  {it.title[:50]}")
    return 0


def cmd_interfaces(args):
    ids, path = _split_targets_and_path(args.targets)
    spec = _spec(path)
    if spec is None:
        return 2
    comps = Components(spec)
    wanted = sorted(comps.nodes, key=_idkey)
    if ids:
        wanted = []
        for raw in ids:
            it, note = _find(spec, raw)
            if it is None:
                print(f"error: {note}", file=sys.stderr)
                return 1
            wanted.append(it.id)
    if not wanted:
        print("no components declared")
        return 1
    for cid in wanted:
        it = spec.items[cid]
        ifaces, assumptions = comps.interfaces(cid)
        members = comps.members(cid)
        print(f"{cid} — {it.title}  ({len(members)} members" + (f"; hides: {it.header['hides']}" if it.header.get("hides") else "") + ")")
        print(f"  guarantees ({len(ifaces)} interface items):")
        for iface, users in ifaces:
            print(f"    {iface.id:10} {iface.title[:60]}" + (f"  <- {', '.join(users)}" if users else "  (no outside dependants yet)"))
        if not ifaces:
            print("    (none declared: nothing outside may link inside except to the component itself)")
        print(f"  requires ({len(assumptions)} assumptions):")
        for a, d in assumptions:
            print(f"    {a.id:10} {a.title[:60]}  " + (f"discharged-by {', '.join(d)}" if d else "UNDISCHARGED"))
        print()
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
    add("isolated", cmd_isolated, "items with no link in either direction, by level: the settlement measure that only falls")
    add("outline", cmd_outline, "levels, files, items, and profile sections not yet present")
    s = add("export", cmd_export, "the spec's index JSON for other specs to cite")
    s.add_argument("-o", "--output", help="write to this file instead of stdout")
    add("assumptions", cmd_assumptions, "every assumption, what discharges it, who assumes it")
    s = sub.add_parser("accept", help="record that the links from ID... (or --all) were read against their targets as they are now")
    s.add_argument("targets", nargs="*", help="item ids, optionally followed by the spec directory")
    s.add_argument("--all", action="store_true", help="every link in the spec")
    s.set_defaults(fn=cmd_accept)
    add("drift", cmd_drift, "accepted links whose targets changed since: what to re-read")
    add("coupling", cmd_coupling, "components: cohesion, links between them, cycles, boundary crossings, cross-cutting and overdetermined items")
    s = sub.add_parser("interfaces", help="a component's guarantees (interface items and who depends on them) and requirements (assumptions and what discharges them)")
    s.add_argument("targets", nargs="*", help="component ids, optionally followed by the spec directory")
    s.set_defaults(fn=cmd_interfaces)
    s = sub.add_parser("review", help="walk a level item by item (status, links with target titles, body); no level: status counts per level")
    s.add_argument("level", nargs="?", help="L0, L1, ... (omit for the per-level summary)")
    s.add_argument("path", nargs="?", default=".", help="spec directory (default: .)")
    s.add_argument("--lines", type=int, default=6, help="body lines to show per item (default 6)")
    s.add_argument("--full", action="store_true", help="show whole bodies")
    s.set_defaults(fn=cmd_review)
    return p


COMMANDS = ("check", "show", "serves", "why", "orphans", "isolated", "outline", "export", "assumptions", "accept", "drift", "review", "coupling", "interfaces")


def main(argv=None):
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    # `explain G2` (or `explain "law 16"`) is `explain show ...`: anything that is not a
    # command or an option in first position selects show, which resolves ids and aliases.
    if argv and argv[0] not in COMMANDS and not argv[0].startswith("-"):
        argv.insert(0, "show")
    args = parser.parse_args(argv)
    if args.patterns:
        print(patterns_text())
        return 0
    if not args.cmd:
        parser.print_help()
        return 2
    return args.fn(args)
