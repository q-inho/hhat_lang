"""When using `hat new` on terminal, should call this file"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from hhat_lang.toolchain.project.utils import str_to_path


def _is_project_scope(project_name: str | Path, some_path: Path) -> bool:
    project_name = str_to_path(project_name)

    if some_path.is_relative_to(project_name):
        return True

    return False


######################
# CREATE NEW PROJECT #
######################


def create_new_project(project_name: str | Path) -> Any:
    project_name = str_to_path(project_name)

    _create_template_folders(project_name)
    _create_template_files(project_name)


def _create_template_folders(project_name: Path) -> Any:
    # create root folder 'project_name' name
    os.mkdir(project_name)

    # create project template structure
    os.mkdir(project_name / "src")
    os.mkdir(project_name / "src" / "hat_types")
    os.mkdir(project_name / "src" / "hat_docs")
    os.mkdir(project_name / "src" / "hat_docs" / "hat_types")
    os.mkdir(project_name / "tests")
    # os.mkdir(project_name / "proofs")  # TODO: once proofs are incorporated, include them


def _create_template_files(project_name: Path) -> Any:
    open(project_name / "src" / "main.hat", "w").close()
    open(project_name / "src" / "hat_docs" / "main.hat.md", "w").close()


###################
# CREATE NEW FILE #
###################


def create_new_file(project_name: str | Path, file_name: str | Path) -> Any:
    project_name = str_to_path(project_name)
    file_name = str_to_path(file_name)
    doc_file = file_name.parent / "hat_docs" / (file_name.name + ".md")

    open(project_name / file_name, "w").close()
    open(project_name / doc_file, "w").close()


def create_new_type_file(project_name: str | Path, file_name: str | Path) -> Any:
    project_name = str_to_path(project_name)
    file_name = file_name + ".hat"
    doc_file = file_name + ".md"

    file_path = project_name / "src" / "hat_types" / file_name
    if file_path.parent != Path("."):
        file_path.parent.mkdir(parents=True, exist_ok=True)

    doc_path = project_name / "src" / "hat_docs" / "hat_types" / doc_file
    if doc_path.parent != Path("."):
        doc_path.parent.mkdir(parents=True, exist_ok=True)

    open(file_path, "w").close()
    open(doc_path, "w").close()

    return file_path
