#!/usr/bin/env python3
"""A small YAML reader for the files this project owns — no dependency needed.

Covers exactly what card files, the source register and skill frontmatter use:
nested mappings, sequences of mappings or scalars, quoted and plain scalars,
block scalars (`|`, `>`, with `-` or `+`), comments, and `---` document markers.

It is deliberately not a general YAML implementation. Anything it does not
understand raises YamlError with a line number rather than guessing, so a
malformed card file is reported instead of silently misread.

    from minyaml import load, YamlError
    data = load(path.read_text(encoding="utf-8"))
"""

import re

__all__ = ["YamlError", "load"]

TRUE = {"true", "yes", "on"}
FALSE = {"false", "no", "off"}
NULL = {"", "~", "null"}
INT = re.compile(r"[+-]?\d+$")
FLOAT = re.compile(r"[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?$")
# key: value, where the key is unquoted and the value optional
KEY = re.compile(r"([^:#]+?)\s*:(?:\s+(.*))?$")
ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/", "0": "\0"}


class YamlError(ValueError):
    """The input is not something this reader is willing to interpret."""


def _strip_comment(text):
    """Removes a trailing # comment that is not inside quotes."""
    quote = None
    for i, ch in enumerate(text):
        if quote:
            if ch == "\\" and quote == '"':
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or text[i - 1] in " \t"):
            return text[:i]
    return text


def _unquote(text, line_no):
    if text.startswith('"'):
        if not text.endswith('"') or len(text) < 2:
            raise YamlError(f"line {line_no}: unterminated double-quoted string")
        out, body, i = [], text[1:-1], 0
        while i < len(body):
            if body[i] == "\\" and i + 1 < len(body):
                key = body[i + 1]
                if key not in ESCAPES:
                    raise YamlError(f"line {line_no}: unsupported escape \\{key}")
                out.append(ESCAPES[key])
                i += 2
            else:
                out.append(body[i])
                i += 1
        return "".join(out)
    if text.startswith("'"):
        if not text.endswith("'") or len(text) < 2:
            raise YamlError(f"line {line_no}: unterminated single-quoted string")
        return text[1:-1].replace("''", "'")
    return None


def _scalar(text, line_no):
    """A single value: quoted string, number, bool, null, or plain string."""
    text = text.strip()
    quoted = _unquote(text, line_no)
    if quoted is not None:
        return quoted
    if text.lower() in NULL:
        return None
    if text.lower() in TRUE:
        return True
    if text.lower() in FALSE:
        return False
    if INT.match(text):
        return int(text)
    if FLOAT.match(text):
        return float(text)
    if text.startswith(("[", "{")):
        raise YamlError(f"line {line_no}: inline collections are not supported — use block style")
    return text


class _Reader:
    def __init__(self, text):
        self.raw = text.splitlines()
        self.i = 0

    def _peek(self):
        """Next meaningful line as (indent, content, line number), or None."""
        while self.i < len(self.raw):
            raw = self.raw[self.i]
            if raw.strip() in ("---", "..."):  # document markers
                self.i += 1
                continue
            content = _strip_comment(raw).rstrip()
            if not content.strip():
                self.i += 1
                continue
            return len(content) - len(content.lstrip(" ")), content.strip(), self.i + 1
        return None

    def _block_scalar(self, header, indent, line_no):
        """`|`, `>`, `|-`, `>+` … — the lines indented under the key."""
        if not re.fullmatch(r"[|>][-+]?", header):
            raise YamlError(f"line {line_no}: cannot read block scalar header {header!r}")
        folded, chomp = header[0] == ">", header[1:] or "clip"
        lines, body_indent = [], None
        while self.i < len(self.raw):
            raw = self.raw[self.i]
            if raw.strip():
                current = len(raw) - len(raw.lstrip(" "))
                if current <= indent:
                    break
                body_indent = current if body_indent is None else min(body_indent, current)
            lines.append(raw)
            self.i += 1
        while lines and not lines[-1].strip():
            lines.pop()
        body = [line[body_indent:] if line.strip() else "" for line in lines]

        if folded:
            out, chunk = [], []
            for line in body:
                if line:
                    chunk.append(line)
                else:
                    out.append(" ".join(chunk))
                    chunk = []
            out.append(" ".join(chunk))
            text = "\n".join(out)
        else:
            text = "\n".join(body)
        return text if chomp == "+" else text.rstrip("\n") + ("\n" if chomp == "clip" else "")

    def parse(self, min_indent):
        """A mapping or a sequence, indented at least `min_indent`."""
        head = self._peek()
        if head is None or head[0] < min_indent:
            return None
        indent, content = head[0], head[1]
        if content == "-" or content.startswith("- "):
            return self._sequence(indent)
        return self._mapping(indent)

    def _sequence(self, indent):
        items = []
        while True:
            head = self._peek()
            if head is None or head[0] < indent:
                return items
            depth, content, line_no = head
            if depth > indent:
                raise YamlError(f"line {line_no}: unexpected indentation in a list")
            if not (content.startswith("- ") or content == "-"):
                return items
            rest = content[2:].strip()
            self.i += 1
            if not rest:
                items.append(self.parse(indent + 1))
                continue
            match = KEY.match(rest)
            if match and not rest.startswith(("'", '"')):
                # `- key: value` starts a mapping whose keys line up after the dash
                self.i -= 1
                self.raw[self.i] = " " * (indent + 2) + rest
                items.append(self._mapping(indent + 2))
            else:
                items.append(_scalar(rest, line_no))

    def _mapping(self, indent):
        mapping = {}
        while True:
            head = self._peek()
            if head is None or head[0] < indent:
                return mapping
            depth, content, line_no = head
            if depth > indent:
                raise YamlError(f"line {line_no}: unexpected indentation")
            if content.startswith("- "):
                return mapping
            match = KEY.match(content)
            if not match:
                raise YamlError(f"line {line_no}: expected 'key: value', got {content!r}")
            key, value = match.group(1).strip(), (match.group(2) or "").strip()
            key = _unquote(key, line_no) or key
            if key in mapping:
                raise YamlError(f"line {line_no}: duplicate key {key!r}")
            self.i += 1
            if value.startswith(("|", ">")):
                mapping[key] = self._block_scalar(value, depth, line_no)
            elif value:
                mapping[key] = _scalar(value, line_no)
            else:
                nested = self._peek()
                if nested and nested[0] > depth:
                    mapping[key] = self.parse(depth + 1)
                elif nested and nested[0] == depth and nested[1].startswith(("- ", "-")):
                    # a list may sit at the same indentation as its key
                    mapping[key] = self._sequence(depth)
                else:
                    mapping[key] = None


def load(text):
    """Parses a YAML document into dicts, lists and scalars."""
    reader = _Reader(text)
    data = reader.parse(0)
    leftover = reader._peek()
    if leftover:
        raise YamlError(f"line {leftover[2]}: could not read {leftover[1]!r}")
    return data
