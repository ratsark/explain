"""A strict, small YAML subset, so the tool needs no third-party parser.

Supported:
  - block mappings      key: value
  - block lists         - value
  - list items that open a mapping   - key: value  (following keys indented to
                                       the column after "- ")
  - nested blocks by indentation (any consistent indent; a nested block must be
    indented more than its parent key or dash)
  - flow lists of scalars            [a, b, "c d"]
  - scalars: "double" and 'single' quoted strings, true/false, null/~, integers,
    everything else as a plain string
  - comments: a line starting with #, or " #" after a value outside quotes

Not supported, by design: anchors, multi-line scalars, flow mappings, nested
flow lists, tabs for indentation. Anything outside the subset raises
MiniYamlError with a line number.
"""

import re

__all__ = ["loads", "parse_value", "MiniYamlError"]


class MiniYamlError(ValueError):
    def __init__(self, message, line=None):
        self.line = line
        super().__init__(f"line {line}: {message}" if line else message)


KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.-]*):(?:[ \t]+(.*))?$")
DASH_RE = re.compile(r"^-(?:[ \t]+(.*))?$")
INT_RE = re.compile(r"^-?\d+$")


def _strip_comment(text):
    """Remove a trailing comment that is outside quotes."""
    out = []
    quote = None
    for i, ch in enumerate(text):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            continue
        if ch == "#" and (i == 0 or text[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _lines(text):
    """(lineno, indent, content) for every non-blank, non-comment line."""
    result = []
    for n, raw in enumerate(text.splitlines(), start=1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise MiniYamlError("tabs are not allowed for indentation", n)
        content = _strip_comment(raw)
        if not content.strip():
            continue
        indent = len(content) - len(content.lstrip(" "))
        result.append((n, indent, content.strip()))
    return result


def parse_value(text, line=None):
    """Parse a scalar or a flow list."""
    text = text.strip()
    if text == "":
        return None
    if text.startswith("["):
        if not text.endswith("]"):
            raise MiniYamlError("unterminated flow list", line)
        inner = text[1:-1].strip()
        if inner == "":
            return []
        items = []
        for part in _split_flow(inner, line):
            part = part.strip()
            if part.startswith("["):
                raise MiniYamlError("nested flow lists are not supported", line)
            items.append(_scalar(part, line))
        return items
    if text.startswith("{"):
        raise MiniYamlError("flow mappings are not supported", line)
    return _scalar(text, line)


def _split_flow(inner, line):
    parts, buf, quote = [], [], None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if quote:
        raise MiniYamlError("unterminated quoted string", line)
    parts.append("".join(buf))
    return parts


def _scalar(text, line):
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    if text[0] in ("'", '"'):
        raise MiniYamlError("unterminated quoted string", line)
    low = text.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    if INT_RE.match(text):
        return int(text)
    return text


def loads(text):
    lines = _lines(text)
    if not lines:
        return {}
    value, i = _block(lines, 0, lines[0][1])
    if i != len(lines):
        raise MiniYamlError("unexpected indentation", lines[i][0])
    return value


def _block(lines, i, indent):
    n, ind, content = lines[i]
    if ind != indent:
        raise MiniYamlError("unexpected indentation", n)
    if DASH_RE.match(content):
        return _list(lines, i, indent)
    return _mapping(lines, i, indent)


def _mapping(lines, i, indent):
    result = {}
    while i < len(lines):
        n, ind, content = lines[i]
        if ind < indent:
            break
        if ind > indent:
            raise MiniYamlError("unexpected indentation", n)
        m = KEY_RE.match(content)
        if not m:
            raise MiniYamlError(f"expected 'key: value', got {content!r}", n)
        key, rest = m.group(1), (m.group(2) or "").strip()
        if key in result:
            raise MiniYamlError(f"duplicate key {key!r}", n)
        i += 1
        if rest:
            result[key] = parse_value(rest, n)
        elif i < len(lines) and lines[i][1] > indent:
            result[key], i = _block(lines, i, lines[i][1])
        else:
            result[key] = None
    return result, i


def _list(lines, i, indent):
    result = []
    while i < len(lines):
        n, ind, content = lines[i]
        if ind < indent:
            break
        if ind > indent:
            raise MiniYamlError("unexpected indentation", n)
        m = DASH_RE.match(content)
        if not m:
            raise MiniYamlError(f"expected '- item', got {content!r}", n)
        text = (m.group(1) or "").strip()
        i += 1
        if text == "":
            if i < len(lines) and lines[i][1] > indent:
                value, i = _block(lines, i, lines[i][1])
            else:
                value = None
            result.append(value)
        elif KEY_RE.match(text):
            # "- key: value" opens a mapping whose further keys sit at the
            # column just after "- ".
            inner_indent = indent + 2
            lines[i - 1] = (n, inner_indent, text)
            value, i = _mapping(lines, i - 1, inner_indent)
            result.append(value)
        else:
            result.append(parse_value(text, n))
    return result, i
