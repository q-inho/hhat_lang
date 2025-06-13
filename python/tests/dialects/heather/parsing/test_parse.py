from __future__ import annotations

from pathlib import Path

import pytest
from hhat_lang.dialects.heather.code.ast import (
    ArgTypePair,
    Body,
    Call,
    CallArgs,
    CompositeId,
    CompositeIdWithClosure,
    EnumTypeMember,
    Expr,
    FnArgs,
    FnDef,
    FnImport,
    Id,
    Imports,
    Literal,
    Main,
    OnlyValue,
    Program,
    Return,
    SingleTypeMember,
    TypeDef,
    TypeImport,
    TypeMember,
)
from hhat_lang.dialects.heather.parsing.run import (
    parse_file,
    parse_grammar,
)

THIS = Path(__file__).parent


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


@pytest.mark.parametrize(
    "hat_file,res",
    [
        (
            "ex_fn01.hat",
            Program(
                fns=(
                    FnDef(
                        fn_name=Id("sum"),
                        fn_type=Id("u64"),
                        args=FnArgs(
                            ArgTypePair(arg_name=Id("a"), arg_type=Id("u64")),
                            ArgTypePair(arg_name=Id("b"), arg_type=Id("u64")),
                        ),
                        body=Body(
                            Return(
                                Expr(
                                    Call(
                                        caller=Id("add"),
                                        args=CallArgs(
                                            OnlyValue(value=Id("a")),
                                            OnlyValue(value=Id("b")),
                                        ),
                                    )
                                )
                            )
                        ),
                    ),
                )
            ),
        ),
        (
            "ex_fn02.hat",
            Program(
                fns=(
                    FnDef(
                        fn_name=Id("@sum"),
                        fn_type=Id("@u3"),
                        args=FnArgs(
                            ArgTypePair(arg_name=Id("@a"), arg_type=Id("@u3")),
                            ArgTypePair(arg_name=Id("@b"), arg_type=Id("@u3")),
                        ),
                        body=Body(
                            Return(
                                Expr(
                                    Call(
                                        caller=Id("@add"),
                                        args=CallArgs(
                                            OnlyValue(value=Id("@a")),
                                            OnlyValue(value=Id("@b")),
                                        ),
                                    )
                                )
                            )
                        ),
                    ),
                )
            ),
        ),
    ],
)
def test_parse_fn_sample_file(hat_file: str, res: Program) -> None:
    hat_file = (THIS / hat_file).resolve()
    parsed = parse_file(hat_file)
    assert parsed == res


@pytest.mark.parametrize(
    "hat_file, res",
    [
        ("ex_main01.hat", Program(main=Main(Body()))),
        (
            "ex_main02.hat",
            Program(
                main=Main(
                    Body(
                        Expr(
                            Call(
                                caller=Id("print"),
                                args=CallArgs(
                                    Call(
                                        caller=Id("add"),
                                        args=CallArgs(
                                            OnlyValue(
                                                value=Literal(
                                                    value="1", value_type="int"
                                                )
                                            ),
                                            OnlyValue(
                                                value=Literal(
                                                    value="2", value_type="int"
                                                )
                                            ),
                                        ),
                                    )
                                ),
                            )
                        )
                    )
                )
            ),
        ),
        (
            "ex_main03.hat",
            Program(
                imports=Imports(
                    type_import=(
                        TypeImport(
                            type_list=(
                                CompositeId(
                                    Id("geometry"), Id("euclidian"), Id("space")
                                ),
                            )
                        ),
                    ),
                    fn_import=(),
                ),
                main=Main(),
            ),
        ),
        (
            "ex_main04.hat",
            Program(
                imports=Imports(
                    type_import=(
                        TypeImport(
                            type_list=(
                                CompositeIdWithClosure(
                                    CompositeId(Id("euclidian"), Id("space")),
                                    CompositeId(Id("differential"), Id("form")),
                                    name=Id("geometry"),
                                ),
                            ),
                        ),
                    ),
                    fn_import=(),
                ),
                main=Main(),
            ),
        ),
        (
            "ex_main05.hat",
            Program(
                imports=Imports(
                    type_import=(
                        TypeImport(
                            type_list=(
                                CompositeIdWithClosure(
                                    CompositeId(Id("euclidian"), Id("space")),
                                    CompositeId(Id("differential"), Id("form")),
                                    name=Id("geometry"),
                                ),
                                CompositeId(Id("std"), Id("io"), Id("socket")),
                            ),
                        ),
                    ),
                    fn_import=(
                        FnImport(
                            fn_list=(
                                CompositeIdWithClosure(
                                    Id("sin"),
                                    Id("cos"),
                                    Id("tan"),
                                    name=Id("math"),
                                ),
                            )
                        ),
                    ),
                ),
                main=Main(),
            ),
        ),
    ],
)
def test_parse_main_sample_file(hat_file: str, res: Program) -> None:
    # TODO: add the Program object for each of the files to test
    hat_file = (THIS / hat_file).resolve()
    parsed = parse_file(hat_file)
    assert parsed == res


@pytest.mark.skip()
def test_parse_main_types_files() -> None:
    # TODO: write main and type files to test parsing throughout files
    pass


@pytest.mark.skip()
def test_parse_main_fns_files() -> None:
    # TODO: write main and fns files to test parsing throughout files
    pass


@pytest.mark.skip()
def test_parse_full_examples() -> None:
    # TODO: write code with main, types and fns files, with calling on
    #   different ones, circular import, etc
    pass
