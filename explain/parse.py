"""Read a spec directory into items, links, mentions and findings.

THE MATCHERS. Every regex the tool uses is declared here and printed by
`explain --patterns`. There is no heuristic matching: if a line does not match
one of these, it is prose.
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import miniyaml
from .profile import ProfileError, load_profile

# An id: optional level prefix (only for per-level kinds), 1-3 capital letters
# that are not "L"+digit, a number, optional dotted refinement.
ID_CORE = r"(?:L(\d+)-)?(?!L\d)([A-Z]{1,3})(\d+)((?:\.\d+)*)"
# A qualified id: optional "spec-name:" namespace before the id.
QID_CORE = r"(?:([a-z][a-z0-9_-]*):)?" + ID_CORE

ID_RE = re.compile(r"^" + ID_CORE + r"$")
QID_RE = re.compile(r"^" + QID_CORE + r"$")

# A top-level entry of the spec directory that belongs to a level.
LEVEL_ENTRY_RE = re.compile(r"^L(\d+)-([A-Za-z0-9_.-]+?)(\.md)?$")

# Item headings and bullet items: id, separator (em dash, en dash, hyphen or
# colon), title. Trailing #'s on headings are stripped.
SEP = r"[ \t]*[—–:\-][ \t]*"
HEADING_ITEM_RE = re.compile(r"^(#{1,6})[ \t]+" + ID_CORE + SEP + r"(.*?)[ \t]*#*[ \t]*$")
BULLET_ITEM_RE = re.compile(r"^([ \t]*)[-*+][ \t]+" + ID_CORE + SEP + r"(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$")
BULLET_RE = re.compile(r"^([ \t]*)[-*+][ \t]+")

# A header line directly under a heading item: "key: value".
HEADER_LINE_RE = re.compile(r"^([a-z][a-z0-9-]*):[ \t]*(.*)$")

# Typed inline link [[relation ID]] and untyped mention [[ID]].
INLINE_LINK_RE = re.compile(r"\[\[[ \t]*([a-z][a-z-]*)[ \t]+(" + QID_CORE + r")[ \t]*\]\]")
MENTION_RE = re.compile(r"\[\[[ \t]*(" + QID_CORE + r")[ \t]*\]\]")

FENCE_RE = re.compile(r"^[ \t]*(```|~~~)")

RELATIONS = {
    "serves": "the ends this item exists for (means-ends, up)",
    "assumes": "assumption items this item rests on (lateral)",
    "discharged-by": "on an assumption: what guarantees it (up or lateral)",
    "verifies": "on a verification item: what it checks (any level)",
    "depends-on": "needs this other item to exist or hold (lateral)",
    "conflicts-with": "recorded tension, reconciled in the body (lateral)",
    "supersedes": "this item replaces that one (lateral)",
}
HEADER_FIELDS = {
    "status": "draft | proposed | adopted | superseded | rejected (the decision's state)",
    "built": "unbuilt | building | shipped | removed (the realization's state; separate from status)",
    "derived": "true when an item deliberately serves nothing",
    "owner": "who maintains this item",
    "was": "previous ids after a level move or renumber",
    "source": "where the body's authority comes from",
    "refs": "paths into code, tests, docs",
    "aka": "other names this item is cited by (free text, e.g. 'law 16'); unique across the spec; resolvable by show/why/serves",
    "component": "true to declare this item a component: its dotted sub-items are inside it, and other items may declare part-of it",
    "part-of": "the component this item belongs to (an item id); items without one are cross-cutting",
    "interface": "true on the items that are a component's published surface: the only things another component may link to",
    "hides": "the design decision this component encapsulates (free text, on a component node)",
}
STATUSES = ("draft", "proposed", "adopted", "superseded", "rejected")
BUILT = ("unbuilt", "building", "shipped", "removed")

# Relations whose target, when changed, affects the source. Used by `serves`
# (the downstream sweep): X is downstream of Y if X has one of these to Y.
DOWNSTREAM_RELATIONS = ("serves", "assumes", "discharged-by", "verifies", "depends-on")

DECLARED_MISSES = [
    "Anything inside a ``` or ~~~ fenced block is ignored: no items, links or mentions.",
    "A bare id in prose (G2 without [[ ]]) is text, never a reference.",
    "HTML comments are not recognised; an item heading inside <!-- --> is still an item.",
    "A header ends at the first line that is not 'key: value'; a body that starts on the line after the heading with 'word: ...' is read as a header line and reported if the key is unknown.",
    "Bullet items are only recognised with -, * or + markers; numbered lists are prose.",
    "Sections are matched by heading text against the profile's section titles, case-insensitively, at the top level of the section tree only.",
    "Cross-spec targets are resolved through a parent's 'path' or 'index'; a namespace with neither is reported as unresolvable, not checked.",
    "A fingerprint covers an item's title and body and its refinements' (dotted sub-items), not its header fields: a status change never makes dependants suspect, and a change to a linked-to item's own links does not either.",
    "Drift is only detected for links that have been accepted (accepted-links.txt); links never accepted are counted, not checked.",
    "Prose outside any item has no fingerprint: drift in it is invisible. A profile section holding prose but no items is reported so the author can make the prose an item.",
    "Boundary checks cover serves, depends-on and assumes between local items; verifies, conflicts-with, supersedes and cross-spec links are not boundary-checked.",
]


@dataclass
class Link:
    relation: str
    target: str          # as written, e.g. "G2", "biz:G3", "L4-V1"
    file: Path
    line: int
    inline: bool


@dataclass
class Mention:
    target: str
    file: Path
    line: int


@dataclass
class Finding:
    severity: str        # "error" | "report"
    code: str
    message: str
    file: Path = None
    line: int = None

    def format(self):
        loc = ""
        if self.file is not None:
            loc = f"{self.file}:{self.line}: " if self.line else f"{self.file}: "
        return f"{loc}{self.severity}: {self.message} [{self.code}]"

    def sort_key(self):
        return (str(self.file or ""), self.line or 0, self.severity, self.code)


@dataclass
class Item:
    id: str
    kind: str
    level: int           # from the path
    prefix_level: int    # from the id's L<n>- prefix, or None
    number: str          # "6.2"
    title: str
    file: Path
    line: int
    is_bullet: bool
    depth: int           # heading depth or bullet indent
    header: dict = field(default_factory=dict)
    links: list = field(default_factory=list)
    mentions: list = field(default_factory=list)
    body_lines: list = field(default_factory=list)

    @property
    def parent_id(self):
        if "." not in self.number:
            return None
        head = self.number.rsplit(".", 1)[0]
        pre = f"L{self.prefix_level}-" if self.prefix_level is not None else ""
        return f"{pre}{self.kind}{head}"

    @property
    def status(self):
        return self.header.get("status")

    @property
    def body(self):
        return "\n".join(self.body_lines).strip("\n")

    def links_of(self, relation):
        return [l for l in self.links if l.relation == relation]


@dataclass
class LevelFiles:
    n: int
    name: str
    entry: Path          # the L<n>-name entry, relative to root
    files: list          # markdown files, relative to root


@dataclass
class Spec:
    root: Path
    manifest: dict
    profile: object
    levels: dict         # n -> LevelFiles
    items: dict          # id -> Item
    findings: list       # parse-time findings
    sections: dict       # n -> [(title, file, line, depth)]
    accepted: dict = field(default_factory=dict)   # (from, relation, to) -> fingerprint
    section_flags: dict = field(default_factory=dict)  # (file, line) -> {"items": bool, "prose": bool}

    @property
    def name(self):
        return self.manifest.get("name")

    def fingerprint(self, item_id):
        """A short hash of an item's title and body, and of its refinements'.

        Header fields are not included: a status change does not make the
        items that depend on this one suspect; a wording change does.
        """
        parts = []
        stack = [item_id]
        while stack:
            iid = stack.pop()
            it = self.items.get(iid)
            if it is None:
                continue
            parts.append(iid + "\n" + _norm_text(it.title) + "\n" + _norm_text(it.body))
            stack.extend(sorted(k.id for k in self.items.values() if k.parent_id == iid))
        return hashlib.sha256("\n\n".join(sorted(parts)).encode("utf-8")).hexdigest()[:10]

    def canonical_id(self, text):
        """Normalise an id as written to its canonical form, or None."""
        m = ID_RE.match(text.strip())
        if not m:
            return None
        return make_id(m.group(1), m.group(2), m.group(3), m.group(4))


def _norm_text(s):
    return " ".join((s or "").split())


ACCEPTED_FILE = "accepted-links.txt"
ACCEPTED_LINE_RE = re.compile(r"^(\S+)[ \t]+([a-z-]+)[ \t]+(\S+)[ \t]+([0-9a-f]{6,64})[ \t]*$")


def load_accepted(root, findings):
    """spec/accepted-links.txt: one line per accepted link, 'FROM RELATION TO FINGERPRINT'."""
    path = root / ACCEPTED_FILE
    out = {}
    if not path.is_file():
        return out
    for n, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = ACCEPTED_LINE_RE.match(line)
        if not m:
            findings.append(Finding("error", "bad-accepted-line",
                                    f"{ACCEPTED_FILE}: expected 'FROM RELATION TO FINGERPRINT', got {line!r}", Path(ACCEPTED_FILE), n))
            continue
        out[(m.group(1), m.group(2), m.group(3))] = m.group(4)
    return out


def save_accepted(root, accepted):
    lines = ["# Accepted links: FROM RELATION TO FINGERPRINT-OF-TO. Machine-written by `explain accept`.",
             "# A link whose target's fingerprint has changed since acceptance is reported as suspect",
             "# by `explain check` and listed by `explain drift`. Re-read the FROM item, then accept again."]
    for (a, rel, b), fp in sorted(accepted.items()):
        lines.append(f"{a} {rel} {b} {fp}")
    (root / ACCEPTED_FILE).write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_id(prefix_level, kind, number, refinement):
    pre = f"L{int(prefix_level)}-" if prefix_level is not None else ""
    return f"{pre}{kind}{int(number)}{refinement or ''}"


def split_qid(text):
    """'biz:G6.2' -> ('biz', 'G6.2'); 'G2' -> (None, 'G2'). None if malformed."""
    m = QID_RE.match(text.strip())
    if not m:
        return None
    ns, pl, kind, num, ref = m.groups()
    return ns, make_id(pl, kind, num, ref)


def parse_manifest(root, findings):
    path = root / "spec.yaml"
    if not path.is_file():
        findings.append(Finding("error", "no-manifest", "spec.yaml not found", Path("spec.yaml")))
        return {}
    try:
        data = miniyaml.loads(path.read_text(encoding="utf-8"))
    except miniyaml.MiniYamlError as e:
        findings.append(Finding("error", "bad-manifest", f"spec.yaml: {e}", Path("spec.yaml"), e.line))
        return {}
    if not isinstance(data, dict):
        findings.append(Finding("error", "bad-manifest", "spec.yaml must be a mapping", Path("spec.yaml")))
        return {}
    known = {"name", "title", "profile", "adopted-through", "parents", "children", "refs-root"}
    for k in data:
        if k not in known:
            findings.append(Finding("error", "bad-manifest", f"spec.yaml: unknown key {k!r}", Path("spec.yaml")))
    name = data.get("name")
    if not isinstance(name, str) or not re.match(r"^[a-z][a-z0-9_-]*$", name):
        findings.append(Finding("error", "bad-manifest",
                                "spec.yaml: 'name' must be lowercase letters, digits, - or _ (used as a namespace)",
                                Path("spec.yaml")))
    parents = data.get("parents") or {}
    if not isinstance(parents, dict):
        findings.append(Finding("error", "bad-manifest", "spec.yaml: 'parents' must be a mapping of name -> {path, index}", Path("spec.yaml")))
        data["parents"] = {}
    else:
        for pname, pval in parents.items():
            if pval is None:
                parents[pname] = {}
            elif not isinstance(pval, dict):
                findings.append(Finding("error", "bad-manifest", f"spec.yaml: parent {pname!r} must be a mapping", Path("spec.yaml")))
                parents[pname] = {}
    children = data.get("children") or []
    if not isinstance(children, list):
        findings.append(Finding("error", "bad-manifest", "spec.yaml: 'children' must be a list", Path("spec.yaml")))
        data["children"] = []
    return data


def find_levels(root, profile, findings):
    levels = {}
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        m = LEVEL_ENTRY_RE.match(entry.name)
        if not m:
            continue
        if entry.is_file() and not m.group(3):
            continue  # "L0-notes.txt" is not a level
        n = int(m.group(1))
        rel = entry.relative_to(root)
        if n not in profile.levels:
            findings.append(Finding("error", "unknown-level",
                                    f"{entry.name}: level {n} is not in profile {profile.name!r} (levels {profile.level_numbers()})", rel))
            continue
        if n in levels:
            findings.append(Finding("error", "duplicate-level",
                                    f"{entry.name}: level {n} already provided by {levels[n].entry}", rel))
            continue
        if entry.is_file():
            files = [rel]
        else:
            files = sorted(p.relative_to(root) for p in entry.rglob("*.md") if p.is_file())
        levels[n] = LevelFiles(n, m.group(2), rel, files)
    return levels


class _FileParser:
    def __init__(self, spec, level, rel, findings):
        self.spec = spec
        self.level = level
        self.rel = rel
        self.findings = findings
        self.items = []            # items in this file, in order
        self.sections = []
        self.section_flags = {}    # (file, line) of a section -> {"items": bool, "prose": bool}
        self._cur_section = None
        self.current_heading = None   # heading Item owning body lines
        self.current_bullet = None    # bullet Item owning continuation lines
        self.bullet_indent = 0
        self.in_header = False

    def parse(self, text):
        in_fence = False
        for lineno, raw in enumerate(text.splitlines(), start=1):
            line = raw.rstrip("\n")
            if FENCE_RE.match(line):
                in_fence = not in_fence
                self.in_header = False
                continue
            if in_fence:
                continue
            self._line(lineno, line)
        return self.items

    def _new_item(self, m, lineno, is_bullet, depth, title):
        # Both item regexes put the id groups at 2..5 (group 1 is the heading
        # marks or the bullet indent).
        pl, kind, num, ref = m.group(2), m.group(3), m.group(4), m.group(5)
        item = Item(
            id=make_id(pl, kind, num, ref),
            kind=kind,
            level=self.level,
            prefix_level=int(pl) if pl is not None else None,
            number=f"{int(num)}{ref or ''}",
            title=title.strip(),
            file=self.rel,
            line=lineno,
            is_bullet=is_bullet,
            depth=depth,
        )
        self.items.append(item)
        return item

    def _line(self, lineno, line):
        m = HEADING_ITEM_RE.match(line)
        if m:
            item = self._new_item(m, lineno, False, len(m.group(1)), m.group(6))
            if self._cur_section is not None:
                self.section_flags[self._cur_section]["items"] = True
            self.current_heading = item
            self.current_bullet = None
            self.in_header = True
            return
        if self.in_header:
            hm = HEADER_LINE_RE.match(line)
            if hm and self.current_heading is not None:
                self._header_line(self.current_heading, hm.group(1), hm.group(2), lineno)
                return
            self.in_header = False
        m = HEADING_RE.match(line)
        if m:
            depth = len(m.group(1))
            self.sections.append((m.group(2).strip(), self.rel, lineno, depth))
            self._cur_section = (self.rel, lineno)
            self.section_flags[self._cur_section] = {"items": False, "prose": False}
            if self.current_heading is not None and depth <= self.current_heading.depth:
                self.current_heading = None
            self.current_bullet = None
            if self.current_heading is not None:
                self.current_heading.body_lines.append(line)
            return
        m = BULLET_ITEM_RE.match(line)
        if m:
            indent = len(m.group(1).expandtabs(4))
            item = self._new_item(m, lineno, True, indent, m.group(6))
            self.current_bullet = item
            self.bullet_indent = indent
            # The title line is not repeated in the body; continuation lines are.
            self._scan_links(item, m.group(6), lineno)
            return
        if not line.strip():
            self.current_bullet = None
            if self.current_heading is not None:
                self.current_heading.body_lines.append(line)
            return
        bm = BULLET_RE.match(line)
        if self.current_bullet is not None:
            indent = len(line[: len(line) - len(line.lstrip())].expandtabs(4))
            if bm is None and indent > self.bullet_indent:
                self.current_bullet.body_lines.append(line.strip())
                self._scan_links(self.current_bullet, line, lineno)
                return
            self.current_bullet = None
        if self.current_heading is not None:
            self.current_heading.body_lines.append(line)
            self._scan_links(self.current_heading, line, lineno)
        else:
            if self._cur_section is not None:
                self.section_flags[self._cur_section]["prose"] = True
            self._scan_orphan_links(line, lineno)

    def _header_line(self, item, key, value, lineno):
        if key in RELATIONS:
            try:
                parsed = miniyaml.parse_value(value, lineno)
            except miniyaml.MiniYamlError as e:
                self.findings.append(Finding("error", "bad-header", f"{item.id}: {key}: {e}", self.rel, lineno))
                return
            targets = parsed if isinstance(parsed, list) else [parsed]
            for t in targets:
                if t is None or not isinstance(t, str) or split_qid(str(t)) is None:
                    self.findings.append(Finding("error", "bad-header",
                                                 f"{item.id}: {key}: {t!r} is not an id", self.rel, lineno))
                    continue
                item.links.append(Link(key, str(t), self.rel, lineno, False))
            return
        if key in HEADER_FIELDS:
            if key in item.header:
                self.findings.append(Finding("error", "bad-header", f"{item.id}: duplicate header key {key!r}", self.rel, lineno))
                return
            try:
                parsed = miniyaml.parse_value(value, lineno)
            except miniyaml.MiniYamlError as e:
                self.findings.append(Finding("error", "bad-header", f"{item.id}: {key}: {e}", self.rel, lineno))
                return
            if key in ("was", "refs", "aka") and not isinstance(parsed, list):
                parsed = [parsed] if parsed is not None else []
            if key in ("derived", "interface", "component") and parsed is not True:
                self.findings.append(Finding("error", "bad-header", f"{item.id}: {key} must be 'true' or absent", self.rel, lineno))
                return
            if key == "part-of":
                if not isinstance(parsed, str) or split_qid(parsed) is None or split_qid(parsed)[0] not in (None,):
                    self.findings.append(Finding("error", "bad-header", f"{item.id}: part-of must be a single local id", self.rel, lineno))
                    return
                parsed = split_qid(parsed)[1]
            if key == "built" and parsed not in BUILT:
                self.findings.append(Finding("error", "bad-header",
                                             f"{item.id}: built must be one of {', '.join(BUILT)}; got {parsed!r}", self.rel, lineno))
                return
            if key == "status" and parsed not in STATUSES:
                self.findings.append(Finding("error", "bad-header",
                                             f"{item.id}: status must be one of {', '.join(STATUSES)}; got {parsed!r}", self.rel, lineno))
                return
            item.header[key] = parsed
            return
        self.findings.append(Finding("error", "unknown-key",
                                     f"{item.id}: unknown header key {key!r} (relations: {', '.join(RELATIONS)}; fields: {', '.join(HEADER_FIELDS)})",
                                     self.rel, lineno))

    def _scan_links(self, item, line, lineno):
        typed_spans = []
        for m in INLINE_LINK_RE.finditer(line):
            typed_spans.append(m.span())
            rel, target = m.group(1), m.group(2)
            if rel not in RELATIONS:
                self.findings.append(Finding("error", "unknown-relation",
                                             f"{item.id}: unknown inline relation {rel!r} (known: {', '.join(RELATIONS)})", self.rel, lineno))
                continue
            item.links.append(Link(rel, target, self.rel, lineno, True))
        for m in MENTION_RE.finditer(line):
            if any(a <= m.start() < b for a, b in typed_spans):
                continue
            item.mentions.append(Mention(m.group(1), self.rel, lineno))

    def _scan_orphan_links(self, line, lineno):
        for m in INLINE_LINK_RE.finditer(line):
            self.findings.append(Finding("error", "link-outside-item",
                                         f"typed link [[{m.group(1)} {m.group(2)}]] is not inside any item", self.rel, lineno))


def parse_spec(root, load_external=True):
    """Parse the spec at `root`. Never raises for content problems; see spec.findings."""
    root = Path(root).resolve()
    findings = []
    manifest = parse_manifest(root, findings)
    profile_name = manifest.get("profile") or "software"
    try:
        profile = load_profile(str(profile_name), root)
    except ProfileError as e:
        findings.append(Finding("error", "bad-profile", str(e), Path("spec.yaml")))
        profile = load_profile("software")
    levels = find_levels(root, profile, findings)
    items = {}
    sections = {}
    section_flags = {}
    for n, lf in sorted(levels.items()):
        sections[n] = []
        for rel in lf.files:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
            fp = _FileParser(None, n, rel, findings)
            for item in fp.parse(text):
                if item.id in items:
                    other = items[item.id]
                    findings.append(Finding("error", "duplicate-id",
                                            f"{item.id} already defined at {other.file}:{other.line}", rel, item.line))
                    continue
                items[item.id] = item
            sections[n].extend(fp.sections)
            section_flags.update(fp.section_flags)
    accepted = load_accepted(root, findings)
    return Spec(root, manifest, profile, levels, items, findings, sections, accepted, section_flags)


def patterns_text():
    out = ["PATTERNS (every regex the tool matches; nothing else is matched)", ""]
    for name, rx in [
        ("level entry (top-level file or dir)", LEVEL_ENTRY_RE),
        ("id", ID_RE),
        ("qualified id", QID_RE),
        ("heading item", HEADING_ITEM_RE),
        ("bullet item", BULLET_ITEM_RE),
        ("section heading", HEADING_RE),
        ("header line (directly under a heading item)", HEADER_LINE_RE),
        ("typed inline link", INLINE_LINK_RE),
        ("mention", MENTION_RE),
        ("fence toggle", FENCE_RE),
    ]:
        out.append(f"  {name}:\n    {rx.pattern}")
    out += ["", "RELATIONS"] + [f"  {k:15} {v}" for k, v in RELATIONS.items()]
    out += ["", "HEADER FIELDS"] + [f"  {k:15} {v}" for k, v in HEADER_FIELDS.items()]
    out += ["", "DECLARED MISSES (what this version knowingly does not see)"]
    out += [f"  - {m}" for m in DECLARED_MISSES]
    return "\n".join(out)
