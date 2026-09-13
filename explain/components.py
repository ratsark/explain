"""Components and boundaries (ARCHITECTURE.md section 13).

A component is any item that declares `component: true` or `hides:`, that other
items declare `part-of:`, or that has an `interface: true` sub-item. An item's component is its
own `part-of`, else its refinement parent's component (a sub-item of a
component node is inside it). Items with no component are cross-cutting.

The boundary rule: a `serves`, `depends-on` or `assumes` link from inside
component A to an item inside a different component B must target B itself
(the group node), or one of B's interface items. Reaching up into an enclosing
component is fine; reaching into a sibling's or a child's internals is a
crossing. `verifies`, `conflicts-with` and `supersedes` are exempt.
"""

from .parse import split_qid

BOUNDARY_RELATIONS = ("serves", "depends-on", "assumes")


class Components:
    def __init__(self, spec):
        self.spec = spec
        items = spec.items
        declared = set()
        for it in items.values():
            po = it.header.get("part-of")
            if po:
                declared.add(po)
            if it.header.get("hides") or it.header.get("component") is True:
                declared.add(it.id)
            if it.header.get("interface") is True and it.parent_id:
                declared.add(it.parent_id)
        self.nodes = {c for c in declared if c in items}
        self._comp = {}
        for it in items.values():
            self._comp[it.id] = self._compute(it, set())

    def _compute(self, it, seen):
        if it.id in seen:
            return None
        seen.add(it.id)
        po = it.header.get("part-of")
        if po:
            return po if po in self.spec.items else None
        if it.parent_id and it.parent_id in self.spec.items:
            parent = self.spec.items[it.parent_id]
            if parent.id in self.nodes:
                return parent.id
            return self._compute(parent, seen)
        return None

    def of(self, iid):
        """Nearest enclosing component id, or None (cross-cutting)."""
        return self._comp.get(iid)

    def src(self, iid):
        """The component a link FROM iid is attributed to: the node itself if iid is a component, else its component."""
        return iid if iid in self.nodes else self._comp.get(iid)

    def chain(self, cid):
        """[cid, its component, ...] up to the outermost."""
        out, seen = [], set()
        while cid and cid not in seen:
            out.append(cid)
            seen.add(cid)
            cid = self.of(cid)
        return out

    def is_interface(self, iid):
        it = self.spec.items.get(iid)
        return bool(it and it.header.get("interface") is True)

    def members(self, cid):
        return [i for i in self.spec.items.values() if self.of(i.id) == cid]

    def _local_target(self, link):
        q = split_qid(link.target)
        if q is None or q[0] not in (None, self.spec.name):
            return None
        return self.spec.items.get(q[1])

    def classify(self, src, link):
        """'internal' | 'up' | 'node' | 'interface' | 'outside' | 'unassigned' | 'crossing' | None (unresolvable)."""
        tgt = self._local_target(link)
        if tgt is None:
            return None
        cx, cy = self.src(src.id), self.of(tgt.id)
        if tgt.id in self.nodes and tgt.id != cx:
            return "node"
        if cy is None:
            return "outside"
        if cx is None:
            return "unassigned"   # a cross-cutting item reaching inside a component: probably belongs to it
        if cy == cx:
            return "internal"
        if cy in self.chain(cx):
            return "up"
        if self.is_interface(tgt.id):
            return "interface"
        return "crossing"

    def crossings(self):
        out = []
        for it in self.spec.items.values():
            for link in it.links:
                if link.relation in BOUNDARY_RELATIONS and self.classify(it, link) == "crossing":
                    tgt = self._local_target(link)
                    out.append((it, link, self.src(it.id), self.of(tgt.id)))
        return out

    def unassigned_inside(self):
        """Items outside every component whose links reach a component's internals: candidates for part-of."""
        out = {}
        for it in self.spec.items.values():
            if self.src(it.id) is not None:
                continue
            for link in it.links:
                if link.relation in BOUNDARY_RELATIONS and self.classify(it, link) == "unassigned":
                    out.setdefault(it.id, set()).add(self.of(self._local_target(link).id))
        return sorted(((iid, sorted(cs)) for iid, cs in out.items()), key=lambda x: x[0])

    def component_edges(self):
        """{(from_component, to_component): count} over boundary relations, nearest components, neither enclosing the other."""
        edges = {}
        for it in self.spec.items.values():
            cx = self.src(it.id)
            if cx is None:
                continue
            for link in it.links:
                if link.relation not in BOUNDARY_RELATIONS:
                    continue
                tgt = self._local_target(link)
                if tgt is None:
                    continue
                cy = tgt.id if tgt.id in self.nodes else self.of(tgt.id)
                if cy is None or cy == cx or cy in self.chain(cx) or cx in self.chain(cy):
                    continue
                edges[(cx, cy)] = edges.get((cx, cy), 0) + 1
        return edges

    def cycles(self):
        """Strongly connected components of size > 1 in the component graph, as sorted id lists."""
        edges = self.component_edges()
        adj = {}
        for a, b in edges:
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set())
        index, low, stack, on, result = {}, {}, [], set(), []
        counter = [0]

        def strong(v):
            index[v] = low[v] = counter[0]
            counter[0] += 1
            stack.append(v)
            on.add(v)
            for w in adj.get(v, ()):
                if w not in index:
                    strong(w)
                    low[v] = min(low[v], low[w])
                elif w in on:
                    low[v] = min(low[v], index[w])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                if len(comp) > 1:
                    result.append(sorted(comp))
        for v in sorted(adj):
            if v not in index:
                strong(v)
        return sorted(result)

    def stats(self):
        """Per component: members, internal, out_via (node/interface/up), out_crossing, incoming, cohesion."""
        rows = {}
        for c in self.nodes:
            rows[c] = {"members": 0, "internal": 0, "out_ok": 0, "out_crossing": 0, "in": 0}
        for it in self.spec.items.values():
            cx = self.src(it.id)
            if self.of(it.id) in rows:
                rows[self.of(it.id)]["members"] += 1
            for link in it.links:
                if link.relation not in BOUNDARY_RELATIONS:
                    continue
                kind = self.classify(it, link)
                if kind is None:
                    continue
                tgt = self._local_target(link)
                cy = self.of(tgt.id)
                if kind == "internal" and cx in rows:
                    rows[cx]["internal"] += 1
                elif kind in ("node", "interface", "up") and cx in rows:
                    rows[cx]["out_ok"] += 1
                elif kind == "crossing" and cx in rows:
                    rows[cx]["out_crossing"] += 1
                target_comp = tgt.id if tgt.id in self.nodes and kind == "node" else cy
                if kind in ("node", "interface", "crossing") and target_comp in rows and target_comp != cx:
                    rows[target_comp]["in"] += 1
        for c, r in rows.items():
            out = r["out_ok"] + r["out_crossing"]
            r["cohesion"] = (r["internal"] / (r["internal"] + out)) if (r["internal"] + out) else None
        return rows

    def cross_cutting(self):
        """Items outside every component, with the set of components that link to them (serves/depends-on/assumes)."""
        fanin = {}
        for it in self.spec.items.values():
            cx = self.src(it.id)
            if cx is None:
                continue
            for link in it.links:
                if link.relation not in BOUNDARY_RELATIONS:
                    continue
                tgt = self._local_target(link)
                if tgt is not None and self.of(tgt.id) is None and tgt.id not in self.nodes:
                    fanin.setdefault(tgt.id, set()).add(cx)
        return sorted(((tid, comps) for tid, comps in fanin.items()), key=lambda x: (-len(x[1]), x[0]))

    def overdetermined(self, threshold=3):
        """Items whose serves targets lie in at least `threshold` distinct components."""
        out = []
        for it in self.spec.items.values():
            comps = set()
            for link in it.links_of("serves"):
                tgt = self._local_target(link)
                if tgt is None:
                    continue
                c = tgt.id if tgt.id in self.nodes else self.of(tgt.id)
                if c:
                    comps.add(c)
            if len(comps) >= threshold:
                out.append((it, sorted(comps)))
        return sorted(out, key=lambda x: (-len(x[1]), x[0].id))

    def interfaces(self, cid):
        """(interface items with outside dependants, assumptions with dischargers) for a component."""
        ifaces = []
        for it in self.spec.items.values():
            if self.is_interface(it.id) and self.of(it.id) == cid:
                users = set()
                for other in self.spec.items.values():
                    if self.src(other.id) == cid or cid in self.chain(self.src(other.id)):
                        continue
                    for link in other.links:
                        if link.relation in BOUNDARY_RELATIONS:
                            tgt = self._local_target(link)
                            if tgt is not None and tgt.id == it.id:
                                users.add(other.id)
                ifaces.append((it, sorted(users)))
        assumptions = [(it, [l.target for l in it.links_of("discharged-by")])
                       for it in self.spec.items.values() if it.kind == "A" and self.of(it.id) == cid]
        return ifaces, assumptions
