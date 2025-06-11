from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

import pytest
from hhat_lang.core.imports import TypeImporter
from hhat_lang.dialects.heather.code.ast import (
    AST,
    CompositeId,
    CompositeIdWithClosure,
    Id,
    TypeDef,
    TypeImport,
)
from hhat_lang.toolchain.project.new import create_new_project


@pytest.fixture
def MAX_ATOL_STATES_GATE() -> float:
    return 0.08


def _token_str(obj: Id | CompositeId | CompositeIdWithClosure) -> str:
    if isinstance(obj, Id):
        return obj.value[0]
    if isinstance(obj, CompositeIdWithClosure):
        name, inner = obj.value
        inner_str = " ".join(_token_str(v) for v in inner)
        return f"{_token_str(name)}.{{{inner_str}}}"
    return ".".join(_token_str(part) for part in obj)


def _ast_to_code(node: AST) -> str:
    if isinstance(node, (Id, CompositeId, CompositeIdWithClosure)):
        return _token_str(node)
    if isinstance(node, TypeDef):
        name_node = node.value[0]
        if isinstance(name_node, (CompositeId, CompositeIdWithClosure)):
            # Use only the last identifier for file contents
            name_node = list(name_node)[-1]
        name = _token_str(name_node)
        # Current tests only define empty struct types
        return f"type {name} {{}}"
    if isinstance(node, TypeImport):
        tokens = node.value
        if len(tokens) == 1:
            tokens_str = _token_str(tokens[0])
        else:
            tokens_str = "[" + " ".join(_token_str(t) for t in tokens) + "]"
        return f"use(type:{tokens_str})"
    raise TypeError(f"Unsupported AST node: {type(node)!r}")


def _content_to_code(content: str | AST | Iterable[AST]) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, AST):
        return _ast_to_code(content)
    return "\n".join(_ast_to_code(item) for item in content)


@pytest.fixture
def create_project() -> (
    Callable[[Path, dict[str, str | AST | Iterable[AST]]], TypeImporter]
):
    def _create(
        tmp_path: Path, files: dict[str, str | AST | Iterable[AST]]
    ) -> TypeImporter:
        project_root = tmp_path / "project"
        create_new_project(project_root)
        for rel, content in files.items():
            file_path = project_root / "src" / "hat_types" / rel
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(_content_to_code(content))
        return TypeImporter(project_root)

    return _create
