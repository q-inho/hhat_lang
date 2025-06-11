from __future__ import annotations

from pathlib import Path

import pytest
from hhat_lang.dialects.heather.code.ast import (
    EnumTypeMember,
    Id,
    Program,
    SingleTypeMember,
    TypeDef,
    TypeMember,
)
from hhat_lang.dialects.heather.parsing.run import (
    parse_file,
    parse_grammar,
)

THIS = Path(__file__).parent

# skipping this file until the parser
# pytest.skip(allow_module_level=True)


def test_parse_grammar() -> None:
    assert parse_grammar()


@pytest.mark.parametrize(
    "hat_file,res",
    [
        (
            "ex_type01.hat",
            Program(
                types=(
                    TypeDef(
                        SingleTypeMember(Id("u64")),
                        type_name=Id("natural"),
                        type_ds=Id("single"),
                    ),
                    TypeDef(
                        TypeMember(member_name=Id("x"), member_type=Id("u32")),
                        TypeMember(member_name=Id("y"), member_type=Id("u32")),
                        type_name=Id("point"),
                        type_ds=Id("struct"),
                    ),
                )
            ),
        ),
        (
            "ex_type02.hat",
            Program(
                types=(
                    TypeDef(
                        EnumTypeMember(Id("READ")),
                        EnumTypeMember(Id("WRITE")),
                        EnumTypeMember(Id("APPEND")),
                        EnumTypeMember(Id("ALL")),
                        type_name=Id("dataflag"),
                        type_ds=Id("enum"),
                    ),
                )
            ),
        ),
    ],
)
def test_parse_type_sample_file(hat_file: str, res: Program) -> None:
    hat_file = (THIS / hat_file).resolve()
    parsed = parse_file(hat_file)
    assert parsed == res


@pytest.mark.skip()
@pytest.mark.parametrize("hat_file", ["ex_fn01.hat", "ex_fn02.hat"])
def test_parse_fn_sample_file(hat_file) -> None:
    hat_file = (THIS / hat_file).resolve()
    assert parse_file(hat_file)


@pytest.mark.skip()
@pytest.mark.parametrize("hat_file", ["ex_main01.hat", "ex_main02.hat"])
def test_parse_main_sample_file(hat_file) -> None:
    hat_file = (THIS / hat_file).resolve()
    assert parse_file(hat_file)
