"""Errors (the graph is malformed) and reports (the graph is incomplete).

Errors fail `check`. Reports never do; `--strict` promotes them.
"""

import json
from pathlib import Path

from .components import Components
from .parse import DOWNSTREAM_RELATIONS, Finding, RELATIONS, parse_spec, split_qid


def norm_alias(a):
    return " ".join(str(a).lower().split())


def find_alias(spec, text):
    """The item whose aka matches text (case- and whitespace-insensitive), or None."""
    key = norm_alias(text)
    for it in spec.items.values():
        for a in it.header.get("aka", []) or []:
            if norm_alias(a) == key:
                return it
    return None


class External:
    """A parent or child spec, resolved through a path or an index file."""

    def __init__(self, name, how, ids, error=None, stale=None):
        self.name = name
        self.how = how          # "path" | "index" | None
        self.ids = ids          # {id: {"level":..,"kind":..,"title":..,"fingerprint":..}} or None
        self.error = error
        self.stale = stale      # ids whose index fingerprint differs from the live spec, when both are given


def _ids_of(other):
    return {i.id: {"level": i.level, "kind": i.kind, "title": i.title, "fingerprint": other.fingerprint(i.id)}
            for i in other.items.values()}


def _load_index(spec, name, rel):
    p = (spec.root / str(rel)).resolve()
    if not p.is_file():
        return None, f"{rel}: index file not found"
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if data.get("name") != name:
            return None, f"{rel}: that index is for {data.get('name')!r}, not {name!r}"
        return data["items"], None
    except (ValueError, KeyError) as e:
        return None, f"{rel}: not a valid index ({e})"


def resolve_external(spec, name, conf):
    conf = conf or {}
    live = None
    if conf.get("path"):
        p = (spec.root / str(conf["path"])).resolve()
        if not (p / "spec.yaml").is_file():
            return External(name, "path", None, f"{conf['path']}: no spec.yaml there")
        other = parse_spec(p)
        if other.name and other.name != name:
            return External(name, "path", None,
                            f"{conf['path']}: that spec calls itself {other.name!r}, not {name!r}")
        live = _ids_of(other)
    if conf.get("index"):
        idx, err = _load_index(spec, name, conf["index"])
        if idx is None:
            if live is not None:
                return External(name, "path", live, stale=None)
            return External(name, "index", None, err)
        if live is not None:
            stale = sorted(i for i, v in idx.items() if i in live and v.get("fingerprint") and v["fingerprint"] != live[i]["fingerprint"])
            stale += sorted(i for i in live if i not in idx)
            return External(name, "path", live, stale=stale)
        return External(name, "index", idx)
    if live is not None:
        return External(name, "path", live)
    return External(name, None, None, "declared with neither path nor index")


def link_key(item, link):
    """The identity of a link for the accepted-links store: (from, relation, to-as-canonical)."""
    q = split_qid(link.target)
    to = link.target if q is None else (f"{q[0]}:{q[1]}" if q[0] else q[1])
    return (item.id, link.relation, to)


def target_fingerprint(spec, ext, link):
    """Current fingerprint of a link's target, or None if it cannot be resolved."""
    q = split_qid(link.target)
    if q is None:
        return None
    ns, tid = q
    if ns is None or ns == spec.name:
        return spec.fingerprint(tid) if tid in spec.items else None
    e = ext.get(ns)
    if e is None or e.ids is None or tid not in e.ids:
        return None
    return e.ids[tid].get("fingerprint")


def suspects(spec, ext):
    """[(item, link, accepted_fp, current_fp)] for accepted links whose target changed."""
    out = []
    for it in spec.items.values():
        for link in it.links:
            key = link_key(it, link)
            if key not in spec.accepted:
                continue
            cur = target_fingerprint(spec, ext, link)
            if cur is not None and cur != spec.accepted[key]:
                out.append((it, link, spec.accepted[key], cur))
    return out


def accept(spec, ext, item_ids=None):
    """Record the current target fingerprint for every link from the given items (or all).

    Returns (new, updated, unchanged, unresolved) counts. Does not write; the caller saves.
    """
    new = updated = unchanged = unresolved = 0
    for it in spec.items.values():
        if item_ids is not None and it.id not in item_ids:
            continue
        for link in it.links:
            cur = target_fingerprint(spec, ext, link)
            if cur is None:
                unresolved += 1
                continue
            key = link_key(it, link)
            old = spec.accepted.get(key)
            if old is None:
                new += 1
            elif old != cur:
                updated += 1
            else:
                unchanged += 1
            spec.accepted[key] = cur
    return new, updated, unchanged, unresolved


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
                    out[child_name] = External(child_name, "path", _ids_of(other))
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
        elif e.stale:
            f.append(Finding("report", "index-stale",
                             f"spec {name!r}: the committed index snapshot differs from the live spec for {len(e.stale)} item(s) "
                             f"({', '.join(e.stale[:6])}{', ...' if len(e.stale) > 6 else ''}); re-export it", Path("spec.yaml")))

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

    # --- aliases -------------------------------------------------------------
    seen_aka = {}
    for it in items.values():
        for a in it.header.get("aka", []) or []:
            key = norm_alias(a)
            if key in seen_aka and seen_aka[key] is not it:
                f.append(Finding("error", "duplicate-alias",
                                 f"{it.id}: aka {a!r} is also an alias of {seen_aka[key].id}", it.file, it.line))
            seen_aka[key] = it
            if split_qid(str(a)) is not None and str(a).strip().upper() in items:
                f.append(Finding("error", "alias-is-an-id", f"{it.id}: aka {a!r} is an existing item id", it.file, it.line))

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

    # --- drift ---------------------------------------------------------------
    for it, link, old, cur in suspects(spec, ext):
        f.append(Finding("report", "suspect-link",
                         f"{it.id} {link.relation} {link.target}, but {link.target} changed since this link was accepted "
                         f"(was {old}, now {cur}): re-read {it.id}, then `explain accept {it.id}`", link.file, link.line))
    untracked = sum(1 for it in items.values() for l in it.links
                    if link_key(it, l) not in spec.accepted and target_fingerprint(spec, ext, l) is not None)
    if untracked:
        f.append(Finding("report", "untracked-links",
                         f"{untracked} link(s) have never been accepted, so drift in their targets is not detected; "
                         f"`explain accept --all` after reading them", Path("accepted-links.txt")))

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
        declared = {t.lower() for t in profile.levels[n].section_titles()}
        titles = {t.lower() for t, _, _, _ in spec.sections.get(n, [])}
        missing = [t for t in profile.levels[n].section_titles() if t.lower() not in titles]
        if missing:
            f.append(Finding("report", "sections-absent",
                             f"L{n} has no section yet for: {', '.join(missing)}", lf.entry))
        for title, file, line, depth in spec.sections.get(n, []):
            flags = spec.section_flags.get((file, line))
            if title.lower() in declared and flags and flags["prose"] and not flags["items"]:
                f.append(Finding("report", "section-prose-only",
                                 f"section {title!r} holds prose but no items; prose outside an item has no fingerprint, so drift in it is invisible. Make it an item if anything depends on it", file, line))

    # --- components and boundaries ----------------------------------------------
    for it in items.values():
        po = it.header.get("part-of")
        if po and po not in items:
            f.append(Finding("error", "unknown-id", f"{it.id}: part-of: {po} is not defined", it.file, it.line))
        elif po == it.id:
            f.append(Finding("error", "self-link", f"{it.id}: part-of itself", it.file, it.line))
    comps = Components(spec)
    for it in items.values():
        po = it.header.get("part-of")
        if po and po in items and po != it.id and it.id in comps.chain(po):
            f.append(Finding("error", "part-of-cycle", f"{it.id}: part-of {po} closes a cycle ({' > '.join(comps.chain(po))})", it.file, it.line))
        if it.header.get("interface") is True and comps.of(it.id) is None:
            f.append(Finding("report", "interface-without-component",
                             f"{it.id} is marked interface but belongs to no component (no part-of, and its parent is not a component)", it.file, it.line))
    for src, link, cx, cy in comps.crossings():
        f.append(Finding("report", "boundary-crossing",
                         f"{src.id} (in {cx}) {link.relation} {link.target} (inside {cy}), which is not {cy}'s interface: route it through an interface item or {cy} itself", link.file, link.line))
    for cycle in comps.cycles():
        f.append(Finding("report", "component-cycle",
                         f"components depend on each other in a cycle: {' -> '.join(cycle)} -> {cycle[0]}", Path("spec.yaml")))

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
                   "file": str(i.file), "line": i.line, "fingerprint": spec.fingerprint(i.id)}
            for i in sorted(spec.items.values(), key=lambda x: (x.level, x.file, x.line))
        },
        "links": [
            {"from": i.id, "relation": l.relation, "to": l.target}
            for i in spec.items.values() for l in i.links
        ],
    }
