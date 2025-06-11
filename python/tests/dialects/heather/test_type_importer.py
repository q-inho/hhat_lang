from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import pytest

try:  # allow running tests from repository root
    from tests.conftest import _content_to_code  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for root execution
    import sys
    from pathlib import Path as _Path

    sys.path.insert(0, str(_Path(__file__).resolve().parents[3]))
    from tests.conftest import _content_to_code  # type: ignore

from hhat_lang.core.data.core import CompositeSymbol
from hhat_lang.core.imports import types_importer
from hhat_lang.dialects.heather.code.ast import (
    CompositeId,
    CompositeIdWithClosure,
    Id,
    Imports,
    TypeDef,
    TypeImport,
)
from hhat_lang.dialects.heather.parsing.run import parse_file


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


def parse_heather_file(
    file: Path, root: Path
) -> tuple[list[TypeDef], list[TypeImport]]:
    program = parse_file(file)
    rel = file.relative_to(root).with_suffix("")
    prefix_parts = list(rel.parts)

    imports: list[TypeImport] = []
    type_defs: list[TypeDef] = []

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

    if imports_node:
        imports = list(imports_node.value[0])

    for d in defs_tuple:
        name_parts = list(_id_parts(d.value[0]))
        if (
            len(prefix_parts) == 1
            and len(name_parts) == 1
            and prefix_parts[0] == name_parts[0]
        ):
            parts = name_parts
        else:
            parts = prefix_parts + name_parts
        new_def = TypeDef(*d.value[2], type_name=_make_id(parts), type_ds=d.value[1])
        type_defs.append(new_def)

    return type_defs, imports


def test_single_type(create_project, tmp_path: Path) -> None:
    importer = create_project(
        tmp_path,
        {"point.hat": TypeDef(type_name=Id("point"), type_ds=Id("struct"))},
    )
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    expected_def = TypeDef(type_name=Id("point"), type_ds=Id("struct"))
    defs, imps = parse_heather_file(hat_root / "point.hat", hat_root)
    assert defs == [expected_def]
    assert imps == []
    res = importer.import_types([CompositeSymbol(("point",))])
    assert CompositeSymbol(("point",)) in res


def test_folder_file_type(create_project, tmp_path: Path) -> None:
    importer = create_project(
        tmp_path,
        {
            "geometry/euclidian.hat": TypeDef(
                type_name=CompositeId(Id("geometry"), Id("euclidian"), Id("space")),
                type_ds=Id("struct"),
            )
        },
    )
    sym = CompositeSymbol(("geometry", "euclidian", "space"))
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    expected_def = TypeDef(
        type_name=CompositeId(Id("geometry"), Id("euclidian"), Id("space")),
        type_ds=Id("struct"),
    )
    defs, _ = parse_heather_file(
        hat_root / "geometry" / "euclidian.hat",
        hat_root,
    )
    assert defs == [expected_def]
    res = importer.import_types([sym])
    assert sym in res


def test_multiple_from_same_file(create_project, tmp_path: Path) -> None:
    importer = create_project(
        tmp_path,
        {
            "cartesian.hat": (
                TypeDef(
                    type_name=CompositeId(Id("cartesian"), Id("point")),
                    type_ds=Id("struct"),
                ),
                TypeDef(
                    type_name=CompositeId(Id("cartesian"), Id("point3d")),
                    type_ds=Id("struct"),
                ),
            )
        },
    )
    syms = [
        CompositeSymbol(("cartesian", "point")),
        CompositeSymbol(("cartesian", "point3d")),
    ]
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    expected_defs = [
        TypeDef(
            type_name=CompositeId(Id("cartesian"), Id("point")),
            type_ds=Id("struct"),
        ),
        TypeDef(
            type_name=CompositeId(Id("cartesian"), Id("point3d")),
            type_ds=Id("struct"),
        ),
    ]
    defs, _ = parse_heather_file(hat_root / "cartesian.hat", hat_root)
    assert defs == expected_defs
    res = importer.import_types(syms)
    for s in syms:
        assert s in res


def test_multiple_from_different_files(create_project, tmp_path: Path) -> None:
    importer = create_project(
        tmp_path,
        {
            "cartesian.hat": TypeDef(
                type_name=CompositeId(Id("cartesian"), Id("point")),
                type_ds=Id("struct"),
            ),
            "geometry/euclidian.hat": TypeDef(
                type_name=CompositeId(Id("geometry"), Id("euclidian"), Id("space")),
                type_ds=Id("struct"),
            ),
        },
    )
    syms = [
        CompositeSymbol(("cartesian", "point")),
        CompositeSymbol(("geometry", "euclidian", "space")),
    ]
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    expected_cart = TypeDef(
        type_name=CompositeId(Id("cartesian"), Id("point")),
        type_ds=Id("struct"),
    )
    expected_geo = TypeDef(
        type_name=CompositeId(Id("geometry"), Id("euclidian"), Id("space")),
        type_ds=Id("struct"),
    )
    defs_cart, _ = parse_heather_file(hat_root / "cartesian.hat", hat_root)
    defs_geo, _ = parse_heather_file(
        hat_root / "geometry" / "euclidian.hat",
        hat_root,
    )
    assert defs_cart == [expected_cart]
    assert defs_geo == [expected_geo]
    res = importer.import_types(syms)
    for s in syms:
        assert s in res


def test_invalid_type(create_project, tmp_path: Path) -> None:
    importer = create_project(
        tmp_path,
        {
            "cartesian.hat": TypeDef(
                type_name=CompositeId(Id("cartesian"), Id("point")),
                type_ds=Id("struct"),
            )
        },
    )
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    expected_def = TypeDef(
        type_name=CompositeId(Id("cartesian"), Id("point")),
        type_ds=Id("struct"),
    )
    defs, _ = parse_heather_file(hat_root / "cartesian.hat", hat_root)
    assert defs == [expected_def]
    with pytest.raises(ValueError):
        importer.import_types([CompositeSymbol(("cartesian", "missing"))])


def test_circular_import_success(create_project, tmp_path: Path) -> None:
    files = {
        "a.hat": (
            TypeImport((CompositeId(Id("b"), Id("b")),)),
            TypeDef(type_name=Id("a"), type_ds=Id("struct")),
        ),
        "b.hat": (
            TypeImport((CompositeId(Id("a"), Id("a")),)),
            TypeDef(type_name=Id("b"), type_ds=Id("struct")),
        ),
    }
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    expected_a = TypeDef(type_name=Id("a"), type_ds=Id("struct"))
    expected_b = TypeDef(type_name=Id("b"), type_ds=Id("struct"))
    defs_a, imps_a = parse_heather_file(hat_root / "a.hat", hat_root)
    defs_b, imps_b = parse_heather_file(hat_root / "b.hat", hat_root)
    assert defs_a == [expected_a]
    assert defs_b == [expected_b]
    assert _token_str(imps_a[0].value[0]) == "b.b"
    assert _token_str(imps_b[0].value[0]) == "a.a"
    res = importer.import_types([CompositeSymbol(("a", "a"))])
    assert CompositeSymbol(("b", "b")) in res


def test_circular_import_missing(create_project, tmp_path: Path) -> None:
    files = {
        "a.hat": (
            TypeImport((CompositeId(Id("b"), Id("c")),)),
            TypeDef(type_name=Id("a"), type_ds=Id("struct")),
        ),
        "b.hat": (
            TypeImport((CompositeId(Id("a"), Id("a")),)),
            TypeDef(type_name=Id("b"), type_ds=Id("struct")),
        ),
    }
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    expected_a = TypeDef(type_name=Id("a"), type_ds=Id("struct"))
    defs_a, imps_a = parse_heather_file(hat_root / "a.hat", hat_root)
    assert defs_a == [expected_a]
    assert _token_str(imps_a[0].value[0]) == "b.c"
    with pytest.raises(ValueError):
        importer.import_types([CompositeSymbol(("a", "a"))])


def test_grouped_import_same_file(create_project, tmp_path: Path) -> None:
    files = {
        "cartesian.hat": (
            TypeDef(
                type_name=CompositeId(Id("cartesian"), Id("point")),
                type_ds=Id("struct"),
            ),
            TypeDef(
                type_name=CompositeId(Id("cartesian"), Id("point3d")),
                type_ds=Id("struct"),
            ),
        ),
        "geom.hat": (
            TypeImport(
                (
                    CompositeIdWithClosure(
                        Id("point"),
                        Id("point3d"),
                        name=Id("cartesian"),
                    ),
                )
            ),
            TypeDef(
                type_name=CompositeId(Id("geom"), Id("shape")),
                type_ds=Id("struct"),
            ),
        ),
    }
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    token = CompositeIdWithClosure(
        _make_id(["point"]),
        _make_id(["point3d"]),
        name=_make_id(["cartesian"]),
    )
    assert _token_str(token) == "cartesian.{point point3d}"
    res = importer.import_types([CompositeSymbol(("geom", "shape"))])
    assert CompositeSymbol(("cartesian", "point")) in res
    assert CompositeSymbol(("cartesian", "point3d")) in res


def test_grouped_import_multiple_files(create_project, tmp_path: Path) -> None:
    files = {
        "cartesian.hat": (
            TypeDef(
                type_name=CompositeId(Id("cartesian"), Id("point")),
                type_ds=Id("struct"),
            ),
            TypeDef(
                type_name=CompositeId(Id("cartesian"), Id("point3d")),
                type_ds=Id("struct"),
            ),
        ),
        "scalar.hat": (
            TypeDef(
                type_name=CompositeId(Id("scalar"), Id("pos")),
                type_ds=Id("struct"),
            ),
            TypeDef(
                type_name=CompositeId(Id("scalar"), Id("velocity")),
                type_ds=Id("struct"),
            ),
            TypeDef(
                type_name=CompositeId(Id("scalar"), Id("acceleration")),
                type_ds=Id("struct"),
            ),
        ),
        "geom.hat": (
            TypeImport(
                (
                    CompositeIdWithClosure(
                        Id("point"),
                        Id("point3d"),
                        name=Id("cartesian"),
                    ),
                    CompositeIdWithClosure(
                        Id("pos"),
                        Id("velocity"),
                        Id("acceleration"),
                        name=Id("scalar"),
                    ),
                )
            ),
            TypeDef(
                type_name=CompositeId(Id("geom"), Id("shape")),
                type_ds=Id("struct"),
            ),
        ),
    }
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    token = CompositeIdWithClosure(
        _make_id(["point"]),
        _make_id(["point3d"]),
        name=_make_id(["cartesian"]),
    )
    assert _token_str(token) == "cartesian.{point point3d}"
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
        "cartesian.hat": (
            TypeDef(
                type_name=CompositeId(Id("cartesian"), Id("point")),
                type_ds=Id("struct"),
            ),
        ),
        "geom.hat": (
            TypeImport(
                (
                    CompositeIdWithClosure(
                        Id("point"),
                        Id("missing"),
                        name=Id("cartesian"),
                    ),
                )
            ),
            TypeDef(
                type_name=CompositeId(Id("geom"), Id("shape")),
                type_ds=Id("struct"),
            ),
        ),
    }
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    token = CompositeIdWithClosure(
        _make_id(["point"]),
        _make_id(["missing"]),
        name=_make_id(["cartesian"]),
    )
    assert _token_str(token) == "cartesian.{point missing}"
    with pytest.raises(ValueError):
        importer.import_types([CompositeSymbol(("geom", "shape"))])


def test_missing_type_file(create_project, tmp_path: Path) -> None:
    importer = create_project(tmp_path, {})
    with pytest.raises(FileNotFoundError):
        importer.import_types([CompositeSymbol(("foo", "bar"))])


def test_indented_type_definitions(create_project, tmp_path: Path) -> None:
    files = {
        "cartesian.hat": (
            TypeDef(
                type_name=CompositeId(Id("cartesian"), Id("point")),
                type_ds=Id("struct"),
            ),
        )
    }
    importer = create_project(tmp_path, files)
    project_root = tmp_path / "project"
    hat_root = project_root / "src" / "hat_types"
    expected_def = TypeDef(
        type_name=CompositeId(Id("cartesian"), Id("point")),
        type_ds=Id("struct"),
    )
    defs, _ = parse_heather_file(hat_root / "cartesian.hat", hat_root)
    assert defs == [expected_def]
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

    path.write_text(
        _content_to_code(
            TypeDef(
                type_name=CompositeId(Id("cartesian"), Id("point")),
                type_ds=Id("struct"),
            )
        )
    )
    expected_def = TypeDef(
        type_name=CompositeId(Id("cartesian"), Id("point")),
        type_ds=Id("struct"),
    )
    defs, _ = parse_heather_file(path, hat_root)
    assert defs == [expected_def]
    res = importer.import_types([sym])
    assert sym in res


def test_parse_cache(
    create_project, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    files = {
        "cartesian.hat": (
            TypeDef(
                type_name=CompositeId(Id("cartesian"), Id("point")),
                type_ds=Id("struct"),
            ),
            TypeDef(
                type_name=CompositeId(Id("cartesian"), Id("point3d")),
                type_ds=Id("struct"),
            ),
        )
    }

    parse_calls: list[str] = []

    real_parse = types_importer.parse

    def counting_parse(src: str) -> Any:
        parse_calls.append(src)
        return real_parse(src)

    monkeypatch.setattr(types_importer, "parse", counting_parse)

    types_importer._PARSE_CACHE.clear()

    importer = create_project(tmp_path, files)

    importer.import_types(
        [
            CompositeSymbol(("cartesian", "point")),
            CompositeSymbol(("cartesian", "point3d")),
        ]
    )

    assert len(parse_calls) == 1
