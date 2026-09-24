"""Errors (the graph is malformed) and reports (the graph is incomplete).

Errors fail `check`. Reports never do; `--strict` promotes them.
"""

import json
from pathlib import Path

from .components import Components
from .parse import CITE_TOKEN_RE, DOWNSTREAM_RELATIONS, SOURCE_CITE_RE, SUGGESTED_PARENT_RE, Finding, RELATIONS, parse_spec, split_qid


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

    def __init__(self, name, how, ids, error=None, stale=None, links=None):
        self.name = name
        self.how = how          # "path" | "index" | None
        self.ids = ids          # {id: {"level":..,"kind":..,"title":..,"fingerprint":..}} or None
        self.error = error
        self.stale = stale      # ids whose index fingerprint differs from the live spec, when both are given
        self.links = links or []  # [{"from","relation","to","accepted"?}] — the other spec's links, for children


def _ids_of(other):
    return {i.id: {"level": i.level, "kind": i.kind, "title": i.title, "fingerprint": other.fingerprint(i.id)}
            for i in other.items.values()}


def _links_of(other):
    """A parsed spec's links in export shape, with the accepted fingerprint where it has one."""
    out = []
    for i in other.items.values():
        for l in i.links:
            entry = {"from": i.id, "relation": l.relation, "to": l.target}
            fp = other.accepted.get(link_key(i, l))
            if fp:
                entry["accepted"] = fp
            out.append(entry)
    return out


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
        if not isinstance(conf, dict):
            continue
        child_name = conf.get("name")
        if conf.get("path"):
            p = (spec.root / str(conf["path"])).resolve()
            if (p / "spec.yaml").is_file():
                other = parse_spec(p)
                child_name = other.name or child_name
                if child_name:
                    out[child_name] = External(child_name, "path", _ids_of(other), links=_links_of(other))
                    continue
            out[child_name or str(conf["path"])] = External(child_name, "path", None, f"{conf['path']}: no spec.yaml there")
        elif conf.get("index"):
            p = (spec.root / str(conf["index"])).resolve()
            if not p.is_file():
                out[child_name or str(conf["index"])] = External(child_name, "index", None, f"{conf['index']}: index file not found")
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                child_name = data.get("name") or child_name
                if not child_name:
                    raise KeyError("name")
                out[child_name] = External(child_name, "index", data["items"], links=list(data.get("links") or []))
            except (ValueError, KeyError) as e:
                out[child_name or str(conf["index"])] = External(child_name, "index", None, f"{conf['index']}: not a valid index ({e})")
    return out


def child_inbound(spec, ext, relations=DOWNSTREAM_RELATIONS):
    """this spec's id -> [(child_name, child_item_id, child_title, relation, accepted_fp)] from children's links."""
    idx = {}
    for name, e in ext.items():
        if e.ids is None:
            continue
        for l in e.links:
            if l.get("relation") not in relations:
                continue
            q = split_qid(str(l.get("to", "")))
            if q is None or q[0] != spec.name:
                continue
            title = (e.ids.get(l.get("from")) or {}).get("title", "")
            idx.setdefault(q[1], []).append((name, l.get("from"), title, l["relation"], l.get("accepted")))
    return idx


def child_suspects(spec, ext):
    """Child links (with an accepted fingerprint) whose target here changed since: [(child, from, relation, to, accepted, now)]."""
    out = []
    for name, e in ext.items():
        if e.ids is None:
            continue
        for l in e.links:
            fp = l.get("accepted")
            if not fp:
                continue
            q = split_qid(str(l.get("to", "")))
            if q is None or q[0] != spec.name or q[1] not in spec.items:
                continue
            now = spec.fingerprint(q[1])
            if now != fp:
                out.append((name, l.get("from"), l.get("relation"), q[1], fp, now))
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
            if it.prefix_level is not None and it.prefix_level != it.level:
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
                elif tgt.level == it.level and tgt.kind == it.kind and tid != str(spec.manifest.get("root") or ""):
                    # A constraint serving a goal at L0 is fine (Leveson's own
                    # layout); a goal serving a goal is probably refinement,
                    # unless the goal is the declared root (the mission).
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
    for name, frm, rel, tid, old_fp, now in child_suspects(spec, ext):
        f.append(Finding("report", "child-link-suspect",
                         f"{name}:{frm} {rel} {tid}, but {tid} changed since the child accepted it (was {old_fp}, now {now}): re-review {name}:{frm}, then accept it there",
                         items[tid].file, items[tid].line))
    untracked = sum(1 for it in items.values() for l in it.links
                    if link_key(it, l) not in spec.accepted and target_fingerprint(spec, ext, l) is not None)
    if untracked:
        f.append(Finding("report", "untracked-links",
                         f"{untracked} link(s) have never been accepted, so drift in their targets is not detected; "
                         f"`explain accept --all` after reading them", Path("accepted-links.txt")))

    # --- completeness ----------------------------------------------------------
    verified_by = set()
    for it in items.values():
        for link in it.links_of("verifies"):
            q = split_qid(link.target)
            if q and q[0] in (None, spec.name):
                verified_by.add(q[1])
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
        elif (it.level == top and has_parents and not has_serves and not derived
              and it.kind not in profile.per_level_kinds and it.kind not in ("C", "R")):
            f.append(Finding("report", "derived-from-parent",
                             f"{it.id} serves nothing in the parent spec: derived from the parent's point of view", it.file, it.line))
        if derived and has_serves:
            f.append(Finding("report", "derived-but-serves", f"{it.id} is marked derived yet serves something", it.file, it.line))
        if it.kind == "A" and not it.links_of("discharged-by"):
            f.append(Finding("report", "undischarged-assumption",
                             f"{it.id}: nothing discharges this assumption", it.file, it.line))
        if it.kind in ("G", "P", "D", "S") and it.status not in ("superseded", "rejected"):
            built = it.header.get("built")
            if it.id not in served_by:
                if built is None:
                    f.append(Finding("report", "unserved", f"{it.id} is served by nothing yet (built: unstated)", it.file, it.line))
                elif built == "shipped":
                    f.append(Finding("report", "unrealized", f"{it.id} is shipped but nothing serves it: no implementation row points at it", it.file, it.line))
            if built == "shipped" and it.id not in verified_by:
                f.append(Finding("report", "unguarded", f"{it.id} is shipped but nothing verifies it", it.file, it.line))

    # --- questions -------------------------------------------------------------
    for it in items.values():
        if it.kind == "Q" and it.status == "adopted":
            f.append(Finding("report", "question-adopted",
                             f"{it.id} is a question with status adopted; a question stays proposed until an answer item supersedes it (or it is rejected)", it.file, it.line))

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

def questions(spec):
    """(open questions, answered questions): open = kind Q not superseded/rejected; each with the items that depend on it and the answer that supersedes it."""
    idx = inbound(spec, ("depends-on",))
    sup = {}
    for it in spec.items.values():
        for l in it.links_of("supersedes"):
            q = split_qid(l.target)
            if q and q[0] in (None, spec.name):
                sup.setdefault(q[1], []).append(it.id)
    open_, answered = [], []
    for it in spec.items.values():
        if it.kind != "Q" or it.parent_id:
            continue
        blockers = sorted({o.id for o, _ in idx.get(it.id, [])})
        subs = sorted(k.id for k in spec.items.values() if k.parent_id == it.id)
        row = (it, blockers, sup.get(it.id, []), subs)
        (answered if it.status in ("superseded", "rejected") else open_).append(row)
    return open_, answered


def allocations(spec):
    """The parent's view: for each declared child (by path), the child's items that serve this spec's
    items, and the child's assumptions this spec's items discharge. Returns
    ({parent_id: [(child_name, child_item)]}, [(child_name, assumption, [parent ids])], [child names unresolved])."""
    served, obligations, unresolved = {}, [], []
    ext = externals(spec)
    parents = set(spec.manifest.get("parents") or {})
    for name, e in ext.items():
        if name in parents:
            continue
        if e.ids is None:
            unresolved.append(f"{name}: {e.error}")
            continue
        for l in e.links:
            q = split_qid(str(l.get("to", "")))
            if q is None or q[0] != spec.name:
                continue
            meta = e.ids.get(l.get("from")) or {}
            citem = ChildItem(name, l.get("from"), meta.get("title", ""), meta.get("level"), meta.get("kind"))
            if l.get("relation") == "serves":
                served.setdefault(q[1], []).append((name, citem))
            elif l.get("relation") == "discharged-by" and meta.get("kind") == "A":
                obligations.append((name, citem, q[1]))
    return served, obligations, unresolved


def _refs_root(spec):
    return (spec.root / str(spec.manifest.get("refs-root") or ".")).resolve()


def _path_matches(ref, path):
    """A refs entry names `path` if it is the path, a directory above it, or a file inside a path that is a directory."""
    ref = ref.rstrip("/")
    path = path.rstrip("/")
    return ref == path or path.startswith(ref + "/") or ref.startswith(path + "/")


def source_citations(text):
    """[(lineno, relation, [(id, fingerprint-or-None)])] for every spec:/spec-guard: line in a source text."""
    out = []
    for n, line in enumerate(text.splitlines(), start=1):
        for m in SOURCE_CITE_RE.finditer(line):
            rel = "verifies" if m.group(1) == "spec-guard" else "serves"
            ids = [(tm.group(1), tm.group(2) if tm.group(2) and tm.group(2) != "?" else None)
                   for tm in CITE_TOKEN_RE.finditer(m.group(2))]
            out.append((n, rel, ids))
    return out


def resolve_local(spec, iid):
    """The spec's id for a cited id: exact, or a free-kind id cited without its level prefix."""
    if iid in spec.items:
        return iid
    core = split_qid(iid)
    if core is None:
        return None
    _, bare = core
    if "-" in bare:                                    # cited as L4-V2, written as V2 at L4
        lvl, plain = bare.split("-", 1)
        it = spec.items.get(plain)
        return plain if it is not None and f"L{it.level}" == lvl else None
    hits = [k for k in spec.items if k.endswith("-" + bare)]   # cited as V2, written as L4-V2
    return hits[0] if len(hits) == 1 else None


def covers(spec, ext, path, line=None):
    """Rows and child items that name a source path.
    Returns (rows_by_refs: [item], child_items: [(child, id, title, relation)], citations: [(lineno, relation, id, fp)]).
    With a line, citations are narrowed to the nearest citation at or above it."""
    path = path.replace("\\", "/").rstrip("/")
    rows = [it for it in spec.items.values()
            if any(_path_matches(str(r), path) for r in (it.header.get("refs") or []))]
    child_items = []
    for name, e in ext.items():
        if e.ids is None:
            continue
        for iid, meta in e.ids.items():
            names = [iid] + [str(x) for x in (meta.get("refs") or [])] + ([str(meta["file"])] if meta.get("file") else [])
            if any(_path_matches(n, path) for n in names):
                rels = sorted({l["relation"] for l in e.links if l.get("from") == iid}) or ["-"]
                child_items.append((name, iid, meta.get("title", ""), ", ".join(rels)))
    citations = []
    f = _refs_root(spec) / path
    if f.is_file():
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        for n, rel, ids in source_citations(text):
            for iid, fp in ids:
                citations.append((n, rel, resolve_local(spec, iid) or iid, fp))
        if line is not None and citations:
            above = [c for c in citations if c[0] <= line]
            nearest = max(c[0] for c in above) if above else min(c[0] for c in citations)
            citations = [c for c in citations if c[0] == nearest]
    return rows, child_items, citations


SKIP_SCAN_DIRS = {".git", "node_modules", "dist", "build", "out", "coverage", "__pycache__", ".venv", "venv", "target", ".next", ".wrangler"}


def scan_sources(spec, directory, name="code", max_bytes=2 * 1024 * 1024):
    """Build a child index from spec:/spec-guard: citations in source files under `directory`.
    Items are keyed by path (relative to refs-root); links carry the accepted fingerprint when the
    citation has one. Returns (index dict, [(path, lineno, id) unresolved ids])."""
    base = _refs_root(spec)
    root = (base / directory).resolve() if not Path(directory).is_absolute() else Path(directory)
    items, links, unresolved = {}, [], []
    for f in sorted(root.rglob("*")):
        if not f.is_file() or any(part in SKIP_SCAN_DIRS for part in f.relative_to(root).parts):
            continue
        try:
            if f.stat().st_size > max_bytes:
                continue
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        cites = source_citations(text)
        if not cites:
            continue
        try:
            rel = str(f.relative_to(base))
        except ValueError:
            rel = str(f)
        items[rel] = {"level": None, "kind": "F", "title": rel, "file": rel}
        for n, relation, ids in cites:
            for cited, fp in ids:
                iid = resolve_local(spec, cited)
                if iid is None:
                    unresolved.append((rel, n, cited))
                    continue
                entry = {"from": rel, "relation": relation, "to": f"{spec.name}:{iid}", "line": n}
                if fp:
                    entry["accepted"] = fp
                links.append(entry)
    return {"name": name, "title": f"source citations under {directory}", "items": items, "links": links}, unresolved


def accept_in_source(spec, path):
    """Rewrite every cited id in a source file to carry the row's current fingerprint, keeping the
    line's own separators and prefixes. Returns the count rewritten."""
    f = _refs_root(spec) / path
    text = f.read_text(encoding="utf-8")
    count = [0]

    def fix_token(tm):
        iid = resolve_local(spec, tm.group(1))
        if iid is None:
            return tm.group(0)
        new = f"{tm.group(1)}@{spec.fingerprint(iid)}"
        if new != tm.group(0):
            count[0] += 1
        return new

    def fix_line(m):
        return m.group(0)[:m.start(2) - m.start(0)] + CITE_TOKEN_RE.sub(fix_token, m.group(2))
    new_text = SOURCE_CITE_RE.sub(fix_line, text)
    if new_text != text:
        f.write_text(new_text, encoding="utf-8")
    return count[0]


def suggested_parents(spec):
    """[(item, [ids])] for rows whose body carries 'Suggested parent (unrecorded in source): X, Y'."""
    out = []
    for it in spec.items.values():
        m = SUGGESTED_PARENT_RE.search(it.body)
        if m:
            out.append((it, [x.strip() for x in m.group(1).split(",")]))
    return sorted(out, key=lambda r: (r[0].level, str(r[0].file), r[0].line))


def connectivity(spec):
    """(isolated items, built-state counts). Isolated: no link in either direction and no refinement
    parent or child; mentions do not count. Cross-spec links count as outgoing."""
    linked = set()
    for it in spec.items.values():
        if it.links:
            linked.add(it.id)
        for link in it.links:
            q = split_qid(link.target)
            if q and q[0] in (None, spec.name):
                linked.add(q[1])
        if it.parent_id:
            linked.add(it.id)
            linked.add(it.parent_id)
    isolated = [it for it in spec.items.values() if it.id not in linked]
    built = {}
    for it in spec.items.values():
        built[it.header.get("built") or "unstated"] = built.get(it.header.get("built") or "unstated", 0) + 1
    return isolated, built

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


class ChildItem:
    """A leaf from a child spec, as seen from the parent's sweep."""

    def __init__(self, child, iid, title, level=None, kind=None):
        self.child, self.id, self.title, self.level, self.kind = child, iid, title, level, kind
        self.parent_id = None

    @property
    def qualified(self):
        return f"{self.child}:{self.id}"


def downstream(spec, start_id, ext=None):
    """Everything that would need re-evaluation if start_id changed: [(item, relation, via, depth)].
    With ext (from externals()), child items linking into this spec appear as leaves (ChildItem)."""
    idx = inbound(spec)
    cidx = child_inbound(spec, ext) if ext else {}
    seen = {start_id}
    out = []
    frontier = [(start_id, 0)]
    while frontier:
        cur, depth = frontier.pop(0)
        for name, frm, title, rel, _ in cidx.get(cur, []):
            key = f"{name}:{frm}"
            if key in seen:
                continue
            seen.add(key)
            meta = (ext[name].ids or {}).get(frm) or {}
            out.append((ChildItem(name, frm, title, meta.get("level"), meta.get("kind")), rel, cur, depth + 1))
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


def downward_tree(spec, start_id, max_depth=6):
    """The 'how' tree: items that serve start_id, recursively (serves links only, refinements shown as parts)."""
    idx = inbound(spec, ("serves",))

    def node(iid, depth, seen):
        it = spec.items.get(iid)
        title = it.title if it else "(unknown)"
        kids = []
        if depth < max_depth:
            for k in sorted((k for k in spec.items.values() if k.parent_id == iid), key=lambda k: k.id):
                kids.append((k.id, k.title + "  (part)", []))
            for other, _ in sorted(idx.get(iid, []), key=lambda x: (x[0].level, x[0].id)):
                if other.id in seen:
                    kids.append((other.id, "(cycle)", []))
                    continue
                kids.append(node(other.id, depth + 1, seen | {other.id}))
        return (iid, title, kids)
    return node(start_id, 0, {start_id})


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
        "links": _links_of(spec),
    }
