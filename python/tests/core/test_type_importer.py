from __future__ import annotations

from pathlib import Path

import pytest
from hhat_lang.core.data.core import CompositeSymbol
from hhat_lang.core.imports import TypeImporter


def create_project(tmp_path: Path, files: dict[str, str]) -> TypeImporter:
    for rel, content in files.items():
        file_path = tmp_path / "src" / "hat_types" / rel
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
    return TypeImporter(tmp_path)


def test_single_type(tmp_path: Path) -> None:
    importer = create_project(tmp_path, {"point.hat": "type point {}"})
    res = importer.import_types([CompositeSymbol(("point",))])
    assert CompositeSymbol(("point",)) in res


def test_folder_file_type(tmp_path: Path) -> None:
    importer = create_project(
        tmp_path,
        {"geometry/euclidian.hat": "type space {}"},
    )
    sym = CompositeSymbol(("geometry", "euclidian", "space"))
    res = importer.import_types([sym])
    assert sym in res


def test_multiple_from_same_file(tmp_path: Path) -> None:
    importer = create_project(
        tmp_path,
        {"cartesian.hat": "type point {}\ntype point3d {}"},
    )
    syms = [
        CompositeSymbol(("cartesian", "point")),
        CompositeSymbol(("cartesian", "point3d")),
    ]
    res = importer.import_types(syms)
    for s in syms:
        assert s in res


def test_multiple_from_different_files(tmp_path: Path) -> None:
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
    res = importer.import_types(syms)
    for s in syms:
        assert s in res


def test_invalid_type(tmp_path: Path) -> None:
    importer = create_project(tmp_path, {"cartesian.hat": "type point {}"})
    with pytest.raises(ValueError):
        importer.import_types([CompositeSymbol(("cartesian", "missing"))])


def test_circular_import_success(tmp_path: Path) -> None:
    files = {
        "a.hat": "use(type:b.b)\ntype a {}",
        "b.hat": "use(type:a.a)\ntype b {}",
    }
    importer = create_project(tmp_path, files)
    res = importer.import_types([CompositeSymbol(("a", "a"))])
    assert CompositeSymbol(("b", "b")) in res


def test_circular_import_missing(tmp_path: Path) -> None:
    files = {
        "a.hat": "use(type:b.c)\ntype a {}",
        "b.hat": "use(type:a.a)\ntype b {}",
    }
    importer = create_project(tmp_path, files)
    with pytest.raises(ValueError):
        importer.import_types([CompositeSymbol(("a", "a"))])


def test_grouped_import_same_file(tmp_path: Path) -> None:
    files = {
        "cartesian.hat": "type point {}\ntype point3d {}",
        "geom.hat": "use(type:cartesian.{point point3d})\ntype shape {}",
    }
    importer = create_project(tmp_path, files)
    res = importer.import_types([CompositeSymbol(("geom", "shape"))])
    assert CompositeSymbol(("cartesian", "point")) in res
    assert CompositeSymbol(("cartesian", "point3d")) in res


def test_grouped_import_multiple_files(tmp_path: Path) -> None:
    files = {
        "cartesian.hat": "type point {}\ntype point3d {}",
        "scalar.hat": "type pos {}\ntype velocity {}\ntype acceleration {}",
        "geom.hat": (
            "use(type:[cartesian.{point point3d} scalar.{pos velocity acceleration}])\n"
            "type shape {}"
        ),
    }
    importer = create_project(tmp_path, files)
    res = importer.import_types([CompositeSymbol(("geom", "shape"))])
    for name in [
        ("cartesian", "point"),
        ("cartesian", "point3d"),
        ("scalar", "pos"),
        ("scalar", "velocity"),
        ("scalar", "acceleration"),
    ]:
        assert CompositeSymbol(name) in res


def test_grouped_import_missing(tmp_path: Path) -> None:
    files = {
        "cartesian.hat": "type point {}",
        "geom.hat": "use(type:cartesian.{point missing})\ntype shape {}",
    }
    importer = create_project(tmp_path, files)
    with pytest.raises(ValueError):
        importer.import_types([CompositeSymbol(("geom", "shape"))])


def test_missing_type_file(tmp_path: Path) -> None:
    importer = create_project(tmp_path, {})
    with pytest.raises(FileNotFoundError):
        importer.import_types([CompositeSymbol(("foo", "bar"))])


def test_indented_type_definitions(tmp_path: Path) -> None:
    files = {"cartesian.hat": "    type point {}"}
    importer = create_project(tmp_path, files)
    res = importer.import_types([CompositeSymbol(("cartesian", "point"))])
    assert CompositeSymbol(("cartesian", "point")) in res


def test_state_cleanup_after_error(tmp_path: Path) -> None:
    files = {"cartesian.hat": ""}
    importer = create_project(tmp_path, files)
    sym = CompositeSymbol(("cartesian", "point"))
    with pytest.raises(ValueError):
        importer.import_types([sym])

    # Define the missing type and retry with the same importer
    path = tmp_path / "src" / "hat_types" / "cartesian.hat"
    path.write_text("type point {}")
    res = importer.import_types([sym])
    assert sym in res
