"""To handle the `imports` part, for both types and functions"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, cast

from hhat_lang.core.code.ast import AST
from hhat_lang.core.data.core import CompositeSymbol
from hhat_lang.core.imports import TypeImporter
from hhat_lang.dialects.heather.code.ast import (
    CompositeId,
    CompositeIdWithClosure,
    Id,
    Imports,
    TypeImport,
)


def parse_types(code: Any) -> Any:
    match code:
        case CompositeId():
            return _collect_symbols_from_compositeid(code)
        case CompositeIdWithClosure():
            return _collect_symbols_from_closure(code)
        case _:
            raise ValueError(f"invalid type import: {code}")


def _id_tuple(obj: Id | CompositeId) -> tuple[str, ...]:
    if isinstance(obj, CompositeId):
        result: list[str] = []
        for node in obj:
            node_id = cast(Id, node)
            result.append(cast(str, node_id.value[0]))
        return tuple(result)
    return (cast(str, cast(Id, obj).value[0]),)


def _collect_symbols_from_compositeid(obj: CompositeId) -> list[CompositeSymbol]:
    return [CompositeSymbol(_id_tuple(obj))]


def _collect_symbols_from_closure(
    obj: CompositeIdWithClosure, prefix: Iterable[str] | None = None
) -> list[CompositeSymbol]:
    name_ast, values = cast(tuple[Any, Iterable[Any]], obj.value)
    base = tuple(prefix or ()) + _id_tuple(name_ast)
    res: list[CompositeSymbol] = []
    for v in values:  # type: ignore[attr-defined]
        if isinstance(v, CompositeIdWithClosure):
            res.extend(_collect_symbols_from_closure(v, base))
        elif isinstance(v, CompositeId):
            res.append(CompositeSymbol(base + _id_tuple(v)))
        else:  # Id
            res.append(CompositeSymbol(base + (v.value[0],)))
    return res


def parse_types_compositeid(code: CompositeId) -> Any:
    return _collect_symbols_from_compositeid(code)


def parse_types_compositeidwithclosure(code: CompositeIdWithClosure) -> Any:
    return _collect_symbols_from_closure(code)


def parse_fns(code: Any) -> Any:
    pass


def parse_imports(code: Imports) -> Any:
    type_imports, _ = cast(tuple[tuple[TypeImport, ...], tuple[Any, ...]], code.value)
    names: list[CompositeSymbol] = []
    for imp in type_imports:
        for t in cast(Iterable[Any], imp):
            names.extend(parse_types(t))
    importer = TypeImporter(Path(".").resolve())
    return importer.import_types(names)
