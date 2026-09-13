"""Profiles: the level set, the kinds allowed at each level, the section tree."""

from pathlib import Path

from . import miniyaml

RESERVED_KINDS = {"L"}  # the level prefix, never a kind

PROFILE_DIR = Path(__file__).parent / "profiles"


class ProfileError(ValueError):
    pass


class Level:
    def __init__(self, n, name, kinds, sections):
        self.n = n
        self.name = name
        self.kinds = kinds          # {letter: description}
        self.sections = sections    # [(title, [subtitle, ...]), ...]

    def section_titles(self):
        return [title for title, _ in self.sections]


class Profile:
    def __init__(self, name, levels, per_level_kinds):
        self.name = name
        self.levels = {lv.n: lv for lv in levels}
        self.per_level_kinds = per_level_kinds  # {letter: description}: kinds allowed at any level (free kinds)
        self.kind_level = {}                     # fixed kinds: letter -> n
        for lv in levels:
            for k in lv.kinds:
                self.kind_level[k] = lv.n

    def level_numbers(self):
        return sorted(self.levels)

    def kind_description(self, kind):
        if kind in self.per_level_kinds:
            return self.per_level_kinds[kind]
        n = self.kind_level.get(kind)
        return self.levels[n].kinds[kind] if n is not None else None

    def all_kinds(self):
        return sorted(set(self.kind_level) | set(self.per_level_kinds))


def _sections(raw):
    out = []
    for entry in raw or []:
        if isinstance(entry, str):
            out.append((entry, []))
        elif isinstance(entry, dict) and len(entry) == 1:
            title, subs = next(iter(entry.items()))
            subs = subs or []
            if not all(isinstance(s, str) for s in subs):
                raise ProfileError(f"section {title!r}: nested sections must be plain titles")
            out.append((title, list(subs)))
        else:
            raise ProfileError(f"bad section entry {entry!r}")
    return out


def load_profile_data(data, source="<profile>"):
    if not isinstance(data, dict) or "levels" not in data:
        raise ProfileError(f"{source}: a profile needs a 'levels' list")
    name = data.get("name") or source
    per_level = data.get("free-kinds") or data.get("per-level-kinds") or {}
    if not isinstance(per_level, dict):
        raise ProfileError(f"{source}: free-kinds must be a mapping")
    seen = {}
    levels = []
    for raw in data["levels"]:
        if not isinstance(raw, dict) or "n" not in raw:
            raise ProfileError(f"{source}: each level needs 'n'")
        n = raw["n"]
        if not isinstance(n, int) or n < 0:
            raise ProfileError(f"{source}: level n must be a non-negative integer, got {n!r}")
        if n in [lv.n for lv in levels]:
            raise ProfileError(f"{source}: level {n} declared twice")
        kinds = raw.get("kinds") or {}
        if not isinstance(kinds, dict):
            raise ProfileError(f"{source}: level {n}: kinds must be a mapping")
        for k in kinds:
            _check_kind_letter(k, source)
            if k in per_level:
                raise ProfileError(f"{source}: kind {k} is both free (any level) and fixed to level {n}")
            if k in seen:
                raise ProfileError(f"{source}: kind {k} declared at levels {seen[k]} and {n}")
            seen[k] = n
        levels.append(Level(n, str(raw.get("name") or f"level{n}"), dict(kinds), _sections(raw.get("sections"))))
    for k in per_level:
        _check_kind_letter(k, source)
    if not levels:
        raise ProfileError(f"{source}: no levels")
    return Profile(str(name), levels, dict(per_level))


def _check_kind_letter(k, source):
    if not isinstance(k, str) or not (1 <= len(k) <= 3) or not k.isupper() or not k.isalpha():
        raise ProfileError(f"{source}: kind {k!r} must be 1-3 uppercase letters")
    if k in RESERVED_KINDS:
        raise ProfileError(f"{source}: kind {k!r} is reserved for level prefixes")


def load_profile(name_or_path, spec_root=None):
    """Resolve a profile: spec_root/profile.yaml overrides; else a shipped name or a path."""
    candidates = []
    if spec_root is not None:
        candidates.append(Path(spec_root) / "profile.yaml")
    p = Path(name_or_path)
    if p.suffix in (".yaml", ".yml"):
        candidates.append(p if p.is_absolute() or spec_root is None else Path(spec_root) / p)
    candidates.append(PROFILE_DIR / f"{name_or_path}.yaml")
    for c in candidates:
        if c.is_file():
            try:
                data = miniyaml.loads(c.read_text(encoding="utf-8"))
            except miniyaml.MiniYamlError as e:
                raise ProfileError(f"{c}: {e}") from None
            return load_profile_data(data, str(c))
    shipped = ", ".join(sorted(q.stem for q in PROFILE_DIR.glob("*.yaml")))
    raise ProfileError(f"profile {name_or_path!r} not found (shipped profiles: {shipped})")
