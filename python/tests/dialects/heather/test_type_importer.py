from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pytest
from hhat_lang.core.data.core import CompositeSymbol
from hhat_lang.core.imports.types_importer import _expand_token, _tokenize_imports
from hhat_lang.dialects.heather.code.ast import (
    CompositeId,
    CompositeIdWithClosure,
    Id,
    TypeDef,
    TypeImport,
)


def _make_id(parts: Iterable[str]) -> Id | CompositeId:
    ids = [Id(p) for p in parts]
    if len(ids) == 1:
        return ids[0]
    return CompositeId(*ids)


def _id_parts(obj: Id | CompositeId) -> tuple[str, ...]:
    if isinstance(obj, Id):
        return (obj.value[0],)
    return tuple(c.value[0] for c in obj)


def _token_str(obj: Id | CompositeId | CompositeIdWithClosure) -> str:
    if isinstance(obj, CompositeIdWithClosure):
        name = ".".join(_id_parts(obj.value[0]))
        inner = " ".join(_token_str(v) for v in obj.value[1])
        return f"{name}.{{{inner}}}"
    return ".".join(_id_parts(obj))


def _token_to_ast(token: str) -> Id | CompositeId | CompositeIdWithClosure:
    if ".{" in token and token.endswith("}"):
        prefix, inner = token.split(".{", 1)
        inner = inner[:-1].strip()
        values = [_make_id(v.split(".")) for v in inner.split()]
        return CompositeIdWithClosure(*values, name=_make_id(prefix.split(".")))
    return _make_id(token.split("."))


def parse_heather_file(
    file: Path, root: Path
) -> tuple[list[TypeDef], list[TypeImport]]:
    data = file.read_text()
    rel = file.relative_to(root).with_suffix("")
    prefix_parts = list(rel.parts)

    type_defs: list[TypeDef] = []
    pattern = re.compile(r"^\s*type\s+([@]?[A-Za-z][A-Za-z0-9_-]*)", flags=re.MULTILINE)
    for name in pattern.findall(data):
        if len(prefix_parts) == 1 and prefix_parts[0] == name:
            parts = [name]
        else:
            parts = prefix_parts + [name]
        type_defs.append(TypeDef(type_name=_make_id(parts), type_ds=Id("struct")))

    imports: list[TypeImport] = []
    for m in re.finditer(r"use\s*\(\s*type:([^)]*)\)", data):
        inner = m.group(1).strip()
        if inner.startswith("[") and inner.endswith("]"):
            inner = inner[1:-1].strip()
        tokens = [t for t in _tokenize_imports(inner) if t]
        imports.append(TypeImport(tuple(_token_to_ast(t) for t in tokens)))

    return type_defs, imports


def test_single_type(create_project, tmp_path: Path) -> None:
    importer = create_project(tmp_path, {"point.hat": "type point {}"})
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    defs, imps = parse_heather_file(hat_root / "point.hat", hat_root)
    assert len(defs) == 1
    assert _token_str(defs[0].value[0]) == "point"
    assert isinstance(defs[0].value[1], Id)
    assert imps == []
    res = importer.import_types([CompositeSymbol(("point",))])
    assert CompositeSymbol(("point",)) in res


def test_folder_file_type(create_project, tmp_path: Path) -> None:
    importer = create_project(
        tmp_path,
        {"geometry/euclidian.hat": "type space {}"},
    )
    sym = CompositeSymbol(("geometry", "euclidian", "space"))
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    defs, _ = parse_heather_file(
        hat_root / "geometry" / "euclidian.hat",
        hat_root,
    )
    assert len(defs) == 1
    assert _token_str(defs[0].value[0]) == "geometry.euclidian.space"
    res = importer.import_types([sym])
    assert sym in res


def test_multiple_from_same_file(create_project, tmp_path: Path) -> None:
    importer = create_project(
        tmp_path,
        {"cartesian.hat": "type point {}\ntype point3d {}"},
    )
    syms = [
        CompositeSymbol(("cartesian", "point")),
        CompositeSymbol(("cartesian", "point3d")),
    ]
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    defs, _ = parse_heather_file(hat_root / "cartesian.hat", hat_root)
    names = [_token_str(d.value[0]) for d in defs]
    assert "cartesian.point" in names
    assert "cartesian.point3d" in names
    res = importer.import_types(syms)
    for s in syms:
        assert s in res


def test_multiple_from_different_files(create_project, tmp_path: Path) -> None:
    importer = create_project(
        tmp_path,
        {
            "cartesian.hat": "type point {}",
            "geometry/euclidian.hat": "type space {}",
        },
    )
    syms = [
        CompositeSymbol(("cartesian", "point")),
        CompositeSymbol(("geometry", "euclidian", "space")),
    ]
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    defs_cart, _ = parse_heather_file(hat_root / "cartesian.hat", hat_root)
    defs_geo, _ = parse_heather_file(
        hat_root / "geometry" / "euclidian.hat",
        hat_root,
    )
    assert _token_str(defs_cart[0].value[0]) == "cartesian.point"
    assert _token_str(defs_geo[0].value[0]) == "geometry.euclidian.space"
    res = importer.import_types(syms)
    for s in syms:
        assert s in res


def test_invalid_type(create_project, tmp_path: Path) -> None:
    importer = create_project(tmp_path, {"cartesian.hat": "type point {}"})
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    defs, _ = parse_heather_file(hat_root / "cartesian.hat", hat_root)
    assert _token_str(defs[0].value[0]) == "cartesian.point"
    with pytest.raises(ValueError):
        importer.import_types([CompositeSymbol(("cartesian", "missing"))])


def test_circular_import_success(create_project, tmp_path: Path) -> None:
    files = {
        "a.hat": "use(type:b.b)\ntype a {}",
        "b.hat": "use(type:a.a)\ntype b {}",
    }
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    defs_a, imps_a = parse_heather_file(hat_root / "a.hat", hat_root)
    defs_b, imps_b = parse_heather_file(hat_root / "b.hat", hat_root)
    assert _token_str(imps_a[0].value[0]) == "b.b"
    assert _token_str(imps_b[0].value[0]) == "a.a"
    res = importer.import_types([CompositeSymbol(("a", "a"))])
    assert CompositeSymbol(("b", "b")) in res


def test_circular_import_missing(create_project, tmp_path: Path) -> None:
    files = {
        "a.hat": "use(type:b.c)\ntype a {}",
        "b.hat": "use(type:a.a)\ntype b {}",
    }
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    _, imps_a = parse_heather_file(hat_root / "a.hat", hat_root)
    assert _token_str(imps_a[0].value[0]) == "b.c"
    with pytest.raises(ValueError):
        importer.import_types([CompositeSymbol(("a", "a"))])


def test_grouped_import_same_file(create_project, tmp_path: Path) -> None:
    files = {
        "cartesian.hat": "type point {}\ntype point3d {}",
        "geom.hat": "use(type:cartesian.{point point3d})\ntype shape {}",
    }
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    _, imps = parse_heather_file(hat_root / "geom.hat", hat_root)
    token = imps[0].value[0]
    assert isinstance(token, CompositeIdWithClosure)
    assert _token_str(token) == "cartesian.{point point3d}"
    res = importer.import_types([CompositeSymbol(("geom", "shape"))])
    assert CompositeSymbol(("cartesian", "point")) in res
    assert CompositeSymbol(("cartesian", "point3d")) in res


def test_grouped_import_multiple_files(create_project, tmp_path: Path) -> None:
    files = {
        "cartesian.hat": "type point {}\ntype point3d {}",
        "scalar.hat": "type pos {}\ntype velocity {}\ntype acceleration {}",
        "geom.hat": (
            "use(type:[cartesian.{point point3d} scalar.{pos velocity acceleration}])\n"
            "type shape {}"
        ),
    }
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    _, imps = parse_heather_file(hat_root / "geom.hat", hat_root)
    assert isinstance(imps[0].value[0], CompositeIdWithClosure)
    assert _token_str(imps[0].value[0]) == "cartesian.{point point3d}"
    res = importer.import_types([CompositeSymbol(("geom", "shape"))])
    for name in [
        ("cartesian", "point"),
        ("cartesian", "point3d"),
        ("scalar", "pos"),
        ("scalar", "velocity"),
        ("scalar", "acceleration"),
    ]:
        assert CompositeSymbol(name) in res


def test_grouped_import_missing(create_project, tmp_path: Path) -> None:
    files = {
        "cartesian.hat": "type point {}",
        "geom.hat": "use(type:cartesian.{point missing})\ntype shape {}",
    }
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    _, imps = parse_heather_file(hat_root / "geom.hat", hat_root)
    assert isinstance(imps[0].value[0], CompositeIdWithClosure)
    assert _token_str(imps[0].value[0]) == "cartesian.{point missing}"
    with pytest.raises(ValueError):
        importer.import_types([CompositeSymbol(("geom", "shape"))])


def test_missing_type_file(create_project, tmp_path: Path) -> None:
    importer = create_project(tmp_path, {})
    with pytest.raises(FileNotFoundError):
        importer.import_types([CompositeSymbol(("foo", "bar"))])


def test_indented_type_definitions(create_project, tmp_path: Path) -> None:
    files = {"cartesian.hat": "    type point {}"}
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    defs, _ = parse_heather_file(hat_root / "cartesian.hat", hat_root)
    assert len(defs) == 1
    assert _token_str(defs[0].value[0]) == "cartesian.point"
    res = importer.import_types([CompositeSymbol(("cartesian", "point"))])
    assert CompositeSymbol(("cartesian", "point")) in res


def test_state_cleanup_after_error(create_project, tmp_path: Path) -> None:
    files = {"cartesian.hat": ""}
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    sym = CompositeSymbol(("cartesian", "point"))
    with pytest.raises(ValueError):
        importer.import_types([sym])

    # Define the missing type and retry with the same importer
    path = hat_root / "cartesian.hat"
    path.write_text("type point {}")
    defs, _ = parse_heather_file(path, hat_root)
    assert _token_str(defs[0].value[0]) == "cartesian.point"
    res = importer.import_types([sym])
    assert sym in res
