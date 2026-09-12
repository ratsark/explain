"""Errors (the graph is malformed) and reports (the graph is incomplete).

Errors fail `check`. Reports never do; `--strict` promotes them.
"""

import json
from pathlib import Path

from .parse import DOWNSTREAM_RELATIONS, Finding, RELATIONS, parse_spec, split_qid


class External:
    """A parent or child spec, resolved through a path or an index file."""

    def __init__(self, name, how, ids, error=None):
        self.name = name
        self.how = how          # "path" | "index" | None
        self.ids = ids          # {id: {"level":..,"kind":..,"title":..}} or None
        self.error = error


def resolve_external(spec, name, conf):
    conf = conf or {}
    if conf.get("path"):
        p = (spec.root / str(conf["path"])).resolve()
        if not (p / "spec.yaml").is_file():
            return External(name, "path", None, f"{conf['path']}: no spec.yaml there")
        other = parse_spec(p)
        if other.name and other.name != name:
            return External(name, "path", None,
                            f"{conf['path']}: that spec calls itself {other.name!r}, not {name!r}")
        ids = {i.id: {"level": i.level, "kind": i.kind, "title": i.title} for i in other.items.values()}
        return External(name, "path", ids)
    if conf.get("index"):
        p = (spec.root / str(conf["index"])).resolve()
        if not p.is_file():
            return External(name, "index", None, f"{conf['index']}: index file not found")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("name") != name:
                return External(name, "index", None,
                                f"{conf['index']}: that index is for {data.get('name')!r}, not {name!r}")
            return External(name, "index", data["items"])
        except (ValueError, KeyError) as e:
            return External(name, "index", None, f"{conf['index']}: not a valid index ({e})")
    return External(name, None, None, "declared with neither path nor index")


def externals(spec):
    out = {}
    for name, conf in (spec.manifest.get("parents") or {}).items():
        out[name] = resolve_external(spec, name, conf)
    for conf in spec.manifest.get("children") or []:
        if isinstance(conf, dict) and conf.get("path"):
            p = (spec.root / str(conf["path"])).resolve()
            child_name = conf.get("name")
            if (p / "spec.yaml").is_file():
                other = parse_spec(p)
                child_name = other.name or child_name
                if child_name:
                    out[child_name] = External(child_name, "path",
                                               {i.id: {"level": i.level, "kind": i.kind, "title": i.title}
                                                for i in other.items.values()})
                    continue
            out[child_name or str(conf["path"])] = External(child_name, "path", None, f"{conf['path']}: no spec.yaml there")
    return out


def run_checks(spec, ext=None):
    """Return spec.findings plus graph findings, sorted."""
    ext = externals(spec) if ext is None else ext
    f = list(spec.findings)
    profile = spec.profile
    items = spec.items

    for name, e in ext.items():
        if e.error:
            f.append(Finding("report", "unresolvable-namespace",
                             f"spec {name!r}: {e.error}; its ids cannot be checked", Path("spec.yaml")))

    # --- ids and kinds ------------------------------------------------------
    for it in items.values():
        if it.kind in profile.per_level_kinds:
            if it.prefix_level is None:
                f.append(Finding("error", "missing-level-prefix",
                                 f"{it.id}: kind {it.kind} is per-level; write it as L{it.level}-{it.id}", it.file, it.line))
            elif it.prefix_level != it.level:
                f.append(Finding("error", "wrong-level-prefix",
                                 f"{it.id}: prefix says L{it.prefix_level} but the file is at L{it.level}", it.file, it.line))
        else:
            if it.prefix_level is not None:
                f.append(Finding("error", "unexpected-level-prefix",
                                 f"{it.id}: kind {it.kind} is fixed to one level and takes no L{it.prefix_level}- prefix", it.file, it.line))
            home = profile.kind_level.get(it.kind)
            if home is None:
                f.append(Finding("error", "unknown-kind",
                                 f"{it.id}: kind {it.kind} is not in profile {profile.name!r} (kinds: {', '.join(profile.all_kinds())})", it.file, it.line))
            elif home != it.level:
                f.append(Finding("error", "kind-at-wrong-level",
                                 f"{it.id}: kind {it.kind} belongs at L{home}, but the file is at L{it.level}", it.file, it.line))
        pid = it.parent_id
        if pid is not None and pid not in items:
            f.append(Finding("error", "refinement-of-unknown",
                             f"{it.id} refines {pid}, which is not defined", it.file, it.line))
        for key in ("was",):
            for old in it.header.get(key, []) or []:
                if not isinstance(old, str) or split_qid(old) is None:
                    f.append(Finding("error", "bad-header", f"{it.id}: was: {old!r} is not an id", it.file, it.line))

    # --- links ---------------------------------------------------------------
    served_by = {}     # target id -> [item]
    for it in items.values():
        for link in it.links:
            q = split_qid(link.target)
            if q is None:
                f.append(Finding("error", "bad-id", f"{it.id}: {link.relation}: {link.target!r} is not an id", link.file, link.line))
                continue
            ns, tid = q
            if ns is not None:
                if ns == spec.name:
                    ns = None
                elif ns not in ext:
                    f.append(Finding("error", "unknown-namespace",
                                     f"{it.id}: {link.relation}: {link.target}: spec {ns!r} is not declared under parents or children in spec.yaml", link.file, link.line))
                    continue
                else:
                    e = ext[ns]
                    if e.ids is None:
                        continue  # already reported as unresolvable
                    if tid not in e.ids:
                        f.append(Finding("error", "unknown-id",
                                         f"{it.id}: {link.relation}: {link.target}: no such item in spec {ns!r}", link.file, link.line))
                    elif link.relation == "serves" and it.level != min(profile.level_numbers()):
                        f.append(Finding("report", "cross-spec-serves-below-top",
                                         f"{it.id} (L{it.level}) serves {link.target} in another spec; usually only top-level items serve a parent", link.file, link.line))
                    continue
            if tid not in items:
                f.append(Finding("error", "unknown-id",
                                 f"{it.id}: {link.relation}: {tid} is not defined", link.file, link.line))
                continue
            tgt = items[tid]
            if tid == it.id:
                f.append(Finding("error", "self-link", f"{it.id}: {link.relation} itself", link.file, link.line))
                continue
            rel = link.relation
            if rel == "serves":
                served_by.setdefault(tid, []).append(it)
                if tgt.level > it.level:
                    f.append(Finding("error", "serves-downward",
                                     f"{it.id} (L{it.level}) serves {tid} (L{tgt.level}): means-ends links point upward", link.file, link.line))
                elif tgt.level == it.level and tgt.kind == it.kind:
                    # A constraint serving a goal at L0 is fine (Leveson's own
                    # layout); a goal serving a goal is probably refinement.
                    f.append(Finding("report", "serves-same-level",
                                     f"{it.id} serves {tid}, same level and kind; refinement (dotted ids) or depends-on may be meant", link.file, link.line))
                elif it.level - tgt.level > 1:
                    f.append(Finding("report", "skip-level",
                                     f"{it.id} (L{it.level}) serves {tid} (L{tgt.level}) skipping L{it.level - 1}: a middle item may be waiting to be named", link.file, link.line))
            elif rel == "assumes" and tgt.kind != "A":
                f.append(Finding("error", "assumes-non-assumption",
                                 f"{it.id} assumes {tid}, which is a {profile.kind_description(tgt.kind)}, not an assumption (kind A)", link.file, link.line))
            elif rel == "discharged-by" and it.kind != "A":
                f.append(Finding("error", "discharge-on-non-assumption",
                                 f"{it.id} is a {profile.kind_description(it.kind)}; discharged-by belongs on assumptions (kind A)", link.file, link.line))
            elif rel == "verifies" and it.kind not in profile.per_level_kinds and it.kind != "V":
                f.append(Finding("report", "verifies-from-non-verification",
                                 f"{it.id} verifies {tid} but is a {profile.kind_description(it.kind)}, not a verification item", link.file, link.line))
            elif rel == "supersedes" and tgt.status != "superseded":
                f.append(Finding("report", "supersedes-unmarked",
                                 f"{it.id} supersedes {tid}, which is not marked status: superseded", link.file, link.line))
        for m in it.mentions:
            q = split_qid(m.target)
            if q is None:
                continue
            ns, tid = q
            if ns is not None and ns != spec.name:
                if ns not in ext:
                    f.append(Finding("report", "unresolved-mention", f"[[{m.target}]]: spec {ns!r} is not declared", m.file, m.line))
                elif ext[ns].ids is not None and tid not in ext[ns].ids:
                    f.append(Finding("report", "unresolved-mention", f"[[{m.target}]] does not resolve", m.file, m.line))
                continue
            if tid not in items:
                f.append(Finding("report", "unresolved-mention", f"[[{m.target}]] does not resolve", m.file, m.line))
        refs_root = spec.root / str(spec.manifest.get("refs-root") or ".")
        for ref in it.header.get("refs", []) or []:
            if not (refs_root / str(ref)).exists():
                f.append(Finding("report", "missing-ref", f"{it.id}: refs: {ref} does not exist under {refs_root}", it.file, it.line))

    # --- completeness ----------------------------------------------------------
    top = min(profile.level_numbers())
    has_parents = bool(spec.manifest.get("parents"))
    for it in items.values():
        if it.parent_id is not None:
            continue  # refinements inherit their parent's purpose
        has_serves = bool(it.links_of("serves"))
        derived = it.header.get("derived") is True
        if it.level > top and it.kind not in profile.per_level_kinds:
            if not has_serves and not derived:
                f.append(Finding("report", "orphan",
                                 f"{it.id} serves nothing and is not marked derived", it.file, it.line))
        elif it.level == top and has_parents and not has_serves and not derived and it.kind not in ("A", "X", "E", "R", "C"):
            f.append(Finding("report", "derived-from-parent",
                             f"{it.id} serves nothing in the parent spec: derived from the parent's point of view", it.file, it.line))
        if derived and has_serves:
            f.append(Finding("report", "derived-but-serves", f"{it.id} is marked derived yet serves something", it.file, it.line))
        if it.kind == "A" and not it.links_of("discharged-by"):
            f.append(Finding("report", "undischarged-assumption",
                             f"{it.id}: nothing discharges this assumption", it.file, it.line))
        if it.kind in ("G", "P", "D", "S") and it.id not in served_by and it.status not in ("superseded", "rejected"):
            f.append(Finding("report", "unserved", f"{it.id} is served by nothing yet", it.file, it.line))

    # --- sections ------------------------------------------------------------
    for n, lf in spec.levels.items():
        titles = {t.lower() for t, _, _, _ in spec.sections.get(n, [])}
        missing = [t for t in profile.levels[n].section_titles() if t.lower() not in titles]
        if missing:
            f.append(Finding("report", "sections-absent",
                             f"L{n} has no section yet for: {', '.join(missing)}", lf.entry))

    f.sort(key=lambda x: x.sort_key())
    return f


# --- queries -----------------------------------------------------------------

def inbound(spec, relations=DOWNSTREAM_RELATIONS):
    """target id -> [(item, relation)] over local links."""
    idx = {}
    for it in spec.items.values():
        for link in it.links:
            if link.relation not in relations:
                continue
            q = split_qid(link.target)
            if q is None or (q[0] not in (None, spec.name)):
                continue
            idx.setdefault(q[1], []).append((it, link.relation))
    return idx


def downstream(spec, start_id):
    """Everything that would need re-evaluation if start_id changed: [(item, relation, via, depth)]."""
    idx = inbound(spec)
    seen = {start_id}
    out = []
    frontier = [(start_id, 0)]
    while frontier:
        cur, depth = frontier.pop(0)
        # refinements of cur are downstream too
        kids = [i for i in spec.items.values() if i.parent_id == cur]
        for k in kids:
            if k.id not in seen:
                seen.add(k.id)
                out.append((k, "refines", cur, depth + 1))
                frontier.append((k.id, depth + 1))
        for it, rel in idx.get(cur, []):
            if it.id in seen:
                continue
            seen.add(it.id)
            out.append((it, rel, cur, depth + 1))
            frontier.append((it.id, depth + 1))
    return out


def upstream(spec, start_id, ext):
    """The 'why' chain: tree of serves links upward, as nested lists."""
    def node(iid, seen):
        it = spec.items.get(iid)
        kids = []
        if it is not None:
            targets = [l.target for l in it.links_of("serves")]
            if it.parent_id is not None:
                targets.insert(0, it.parent_id)
            for t in targets:
                if t in seen:
                    kids.append((t, "(cycle)", []))
                    continue
                q = split_qid(t)
                if q and q[0] not in (None, spec.name):
                    ns, tid = q
                    e = ext.get(ns)
                    title = e.ids[tid]["title"] if e and e.ids and tid in e.ids else "(unresolved)"
                    kids.append((t, title, []))
                    continue
                tid = q[1] if q else t
                kids.append(node(tid, seen | {tid}))
        title = it.title if it else "(unknown)"
        return (iid, title, kids)
    return node(start_id, {start_id})


def export_index(spec):
    return {
        "name": spec.name,
        "title": spec.manifest.get("title"),
        "profile": spec.profile.name,
        "items": {
            i.id: {"level": i.level, "kind": i.kind, "title": i.title, "status": i.status,
                   "file": str(i.file), "line": i.line}
            for i in sorted(spec.items.values(), key=lambda x: (x.level, x.file, x.line))
        },
        "links": [
            {"from": i.id, "relation": l.relation, "to": l.target}
            for i in spec.items.values() for l in i.links
        ],
    }
