from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from hhat_lang.core.imports import TypeImporter
from hhat_lang.toolchain.project.new import create_new_project


@pytest.fixture
def MAX_ATOL_STATES_GATE() -> float:
    return 0.08


@pytest.fixture
def create_project() -> Callable[[Path, dict[str, str]], TypeImporter]:
    def _create(tmp_path: Path, files: dict[str, str]) -> TypeImporter:
        project_root = tmp_path / "project"
        create_new_project(project_root)
        for rel, content in files.items():
            file_path = project_root / "src" / "hat_types" / rel
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        return TypeImporter(project_root)

    return _create
