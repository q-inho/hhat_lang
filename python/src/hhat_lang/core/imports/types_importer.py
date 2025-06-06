from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from hhat_lang.core.data.core import CompositeSymbol


def _parse_type_names(data: str) -> list[str]:
    """Extract type names from ``data`` allowing leading indentation."""

    pattern = re.compile(r"^\s*type\s+([@]?[A-Za-z][A-Za-z0-9_-]*)", flags=re.MULTILINE)
    return pattern.findall(data)


def _expand_token(token: str) -> list[str]:
    m = re.match(r"([\w@.-]+)\.\{([^}]+)\}", token)
    if m:
        prefix, inner = m.groups()
        items = re.split(r"\s+", inner.strip())
        return [f"{prefix}.{item}" for item in items]
    return [token]


def _tokenize_imports(inner: str) -> list[str]:
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


def _parse_type_imports(data: str) -> list[str]:
    imports: list[str] = []
    for m in re.finditer(r"use\s*\(\s*type:([^)]*)\)", data):
        inner = m.group(1).strip()
        if inner.startswith("[") and inner.endswith("]"):
            inner = inner[1:-1].strip()
        for raw in _tokenize_imports(inner):
            if not raw:
                continue
            imports.extend(_expand_token(raw))
    return imports


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

            data = file_path.read_text()
            defined = _parse_type_names(data)
            if type_name not in defined:
                raise ValueError(f"Type '{type_name}' not found in {file_path}")

            self._loaded[name] = file_path

            for imp in _parse_type_imports(data):
                self._discover(CompositeSymbol(tuple(imp.split("."))))
        finally:
            self._processing.remove(name)

    def import_types(
        self, names: Iterable[CompositeSymbol]
    ) -> dict[CompositeSymbol, Path]:
        for name in names:
            self._discover(name)
        return dict(self._loaded)
