from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable, cast

from hhat_lang.core.data.core import CompositeSymbol
from hhat_lang.dialects.heather.code.ast import (
    CompositeId,
    CompositeIdWithClosure,
    Id,
    Imports,
    TypeDef,
    TypeImport,
)
from hhat_lang.dialects.heather.parsing.run import parse

_PARSE_CACHE: dict[Path, tuple[float, list[str], list[CompositeSymbol]]] = {}


def _id_parts(obj: Id | CompositeId) -> list[str]:
    if isinstance(obj, CompositeId):
        return [p.value[0] for p in obj]
    return [cast(str, obj.value[0])]


def _expand_group_closures(raw: str) -> str:
    """Rewrite grouped closures to many-import form for the parser."""

    token = r"@?[A-Za-z][A-Za-z0-9_-]*"
    prefix_re = re.compile(rf"({token}(?:\.{token})*)\.{{")

    def _split_tokens(inner: str) -> list[str]:
        tokens: list[str] = []
        buf: list[str] = []
        depth = 0
        for ch in inner.strip():
            if ch.isspace() and depth == 0:
                if buf:
                    tokens.append("".join(buf))
                    buf = []
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            buf.append(ch)
        if buf:
            tokens.append("".join(buf))
        return tokens

    result: list[str] = []
    i = 0
    depth = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "[":
            depth += 1
            result.append(ch)
            i += 1
            continue
        if ch == "]":
            depth -= 1
            result.append(ch)
            i += 1
            continue

        m = prefix_re.match(raw, i)
        if not m:
            result.append(ch)
            i += 1
            continue

        base = m.group(1)
        j = m.end()
        brace_depth = 1
        start = j
        while j < len(raw) and brace_depth:
            if raw[j] == "{":
                brace_depth += 1
            elif raw[j] == "}":
                brace_depth -= 1
            j += 1
        inner = raw[start : j - 1]
        parts = _split_tokens(inner)
        if len(parts) <= 1:
            result.append(raw[i:j])
        else:
            expanded = " ".join(f"{base}.{p}" for p in parts)
            if depth > 0:
                result.append(expanded)
            else:
                result.append(f"[{expanded}]")
        i = j

    return "".join(result)


def _parse_file(file_path: Path) -> tuple[list[str], list[CompositeSymbol]]:
    mtime = file_path.stat().st_mtime
    cached = _PARSE_CACHE.get(file_path)
    if cached and cached[0] == mtime:
        return cached[1], cached[2]

    raw_code = file_path.read_text()
    expanded = _expand_group_closures(raw_code)
    program = parse(expanded)

    imports: list[CompositeSymbol] = []
    names: list[str] = []

    values = program.value
    imports_node: Imports | None = None
    defs_tuple: tuple[TypeDef, ...] = ()

    if len(values) == 2:
        first, second = values
        if isinstance(first, Imports):
            imports_node = first
            if isinstance(second, tuple):
                defs_tuple = tuple(d for d in second if isinstance(d, TypeDef))
        else:
            if isinstance(first, tuple):
                defs_tuple = tuple(d for d in first if isinstance(d, TypeDef))
            if isinstance(second, Imports):
                imports_node = second
    elif len(values) == 1:
        item = values[0]
        if isinstance(item, Imports):
            imports_node = item
        elif isinstance(item, tuple):
            defs_tuple = tuple(d for d in item if isinstance(d, TypeDef))

    def collect(
        obj: Id | CompositeId | CompositeIdWithClosure,
        prefix: tuple[str, ...] = (),
    ) -> list[CompositeSymbol]:
        if isinstance(obj, CompositeIdWithClosure):
            name_ast, values = obj.value
            base = prefix + tuple(_id_parts(cast(Id | CompositeId, name_ast)))
            res: list[CompositeSymbol] = []
            for v in list(values):  # type: ignore[arg-type]
                res.extend(
                    collect(cast(Id | CompositeId | CompositeIdWithClosure, v), base)
                )
            return res
        if isinstance(obj, CompositeId):
            return [CompositeSymbol(prefix + tuple(_id_parts(obj)))]
        return [CompositeSymbol(prefix + (cast(str, obj.value[0]),))]

    if imports_node:
        for imp in cast(tuple[TypeImport, ...], imports_node.value[0]):
            for t in cast(
                tuple[Id | CompositeId | CompositeIdWithClosure, ...], imp.value
            ):
                imports.extend(collect(t))

    for d in defs_tuple:
        parts = _id_parts(cast(Id | CompositeId, d.value[0]))
        names.append(parts[-1])

    _PARSE_CACHE[file_path] = (mtime, names, imports)
    return names, imports


def _parse_type_names(file_path: Path) -> list[str]:
    return _parse_file(file_path)[0]


def _parse_type_imports(file_path: Path) -> list[CompositeSymbol]:
    return _parse_file(file_path)[1]


class TypeImporter:
    """Locate and load types under ``src/hat_types`` relative to a project.

    Each ``.hat`` file is scanned for ``type`` declarations and
    ``use(type:...)`` statements. Referenced types are resolved recursively.
    Circular imports are tolerated during discovery, but a missing type raises
    ``FileNotFoundError`` or ``ValueError``.
    """

    def __init__(self, project_root: Path) -> None:
        self._base = Path(project_root).resolve() / "src" / "hat_types"
        self._loaded: dict[CompositeSymbol, Path] = {}
        self._processing: set[CompositeSymbol] = set()

    @staticmethod
    def _path_parts(name: CompositeSymbol) -> tuple[list[str], str, str]:
        parts = list(name.value)
        if len(parts) == 1:
            dirs: list[str] = []
            file_name = parts[0]
            type_name = parts[0]
        else:
            dirs = parts[:-2]
            file_name = parts[-2]
            type_name = parts[-1]
        return dirs, file_name, type_name

    def _discover(self, name: CompositeSymbol) -> None:
        if name in self._loaded or name in self._processing:
            return

        self._processing.add(name)
        try:
            dirs, file_name, type_name = self._path_parts(name)
            file_path = self._base.joinpath(*dirs, file_name + ".hat")

            if not file_path.exists():
                raise FileNotFoundError(file_path)

            defined = _parse_type_names(file_path)
            if type_name not in defined:
                raise ValueError(f"Type '{type_name}' not found in {file_path}")

            self._loaded[name] = file_path

            for imp in _parse_type_imports(file_path):
                self._discover(imp)
        finally:
            self._processing.remove(name)

    def import_types(
        self, names: Iterable[CompositeSymbol]
    ) -> dict[CompositeSymbol, Path]:
        for name in names:
            self._discover(name)
        return dict(self._loaded)
