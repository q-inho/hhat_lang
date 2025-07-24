from __future__ import annotations

from collections import OrderedDict

from hhat_lang.core.data.core import CoreLiteral, Symbol, CompositeSymbol
from hhat_lang.core.error_handlers.errors import (
    TypeAndMemberNoMatchError,
    TypeQuantumOnClassicalError,
    VariableWrongMemberError,
)
from hhat_lang.core.types.builtin_types import QU3, U32
from hhat_lang.core.types.core import SingleDS, StructDS, EnumDS
from hhat_lang.core.types.utils import BaseTypeEnum


# TODO: refactor the types to use `BuiltinSingleDS` or respective data
#  types so properties can be compared and addressed properly.


def test_single_ds() -> None:
    lit_108 = CoreLiteral("108", "u32")

    user_type1 = SingleDS(name=Symbol("user_type1"))
    user_type1.add_member(U32)
    var1 = user_type1(var_name=Symbol("var1"))
    var1.assign(lit_108)

    assert var1.name == Symbol("var1")
    assert var1.type == Symbol("user_type1")
    assert var1.data == OrderedDict({U32.name: lit_108})
    assert var1.get() == lit_108
    assert var1.is_quantum is False

    assert isinstance(var1.get(Symbol("x")), VariableWrongMemberError)


def test_single_ds_quantum() -> None:
    lit_q2 = CoreLiteral("@2", "@u3")

    qtype1 = SingleDS(name=Symbol("@type1"))
    qtype1.add_member(QU3)
    qvar1 = qtype1(var_name=Symbol("@var1"))
    qvar1.assign(lit_q2)

    assert qvar1.name == Symbol("@var1")
    assert qvar1.type == Symbol("@type1")
    assert qvar1.is_quantum
    assert qvar1.data == OrderedDict({QU3.name: [lit_q2]})
    assert qvar1.get() == [lit_q2]
    assert qvar1.is_quantum is True

    assert isinstance(qvar1.get(Symbol("x")), VariableWrongMemberError)


def test_single_ds_quantum_wrong() -> None:
    type1 = SingleDS(name=Symbol("type1"))
    assert isinstance(type1.add_member(QU3), TypeQuantumOnClassicalError)


def test_struct_ds() -> None:
    lit_25 = CoreLiteral("25", "u32")
    lit_17 = CoreLiteral("17", "u32")

    point = StructDS(name=Symbol("point"))
    point.add_member(U32, Symbol("x")).add_member(U32, Symbol("y"))
    p = point(var_name=Symbol("p"))
    p.assign(x=lit_25, y=lit_17)

    assert p.name == Symbol("p")
    assert p.type == Symbol("point")
    assert p.data == OrderedDict({Symbol("x"): lit_25, Symbol("y"): lit_17})
    assert p.get(Symbol("x")) == lit_25 and p.get(Symbol("y")) == lit_17
    assert p.is_quantum is False

    assert isinstance(p.get("z"), VariableWrongMemberError)


def test_struct_ds_quantum() -> None:
    lit_8 = CoreLiteral("8", "u32")
    lit_q2 = CoreLiteral("@2", "@u3")

    qsample = StructDS(name=Symbol("@sample"))
    qsample.add_member(U32, Symbol("counts")).add_member(QU3, Symbol("@d"))

    qvar = qsample(var_name=Symbol("@var"))
    qvar.assign(lit_8, lit_q2)

    assert qvar.name == Symbol("@var")
    assert qvar.type == Symbol("@sample")
    assert qvar._ds_type == BaseTypeEnum.STRUCT
    assert qvar.is_quantum is True
    assert qvar.data == OrderedDict({Symbol("counts"): lit_8, Symbol("@d"): [lit_q2]})
    assert qvar.get(Symbol("counts")) == lit_8 and qvar.get(Symbol("@d")) == [lit_q2]

    qvar2 = qsample(var_name=Symbol("@var2"))
    qvar2.assign(counts=lit_8, q__d=lit_q2)

    assert qvar2.name == Symbol("@var2")
    assert qvar2.type == Symbol("@sample")
    assert qvar2.is_quantum is True
    assert qvar2.data == OrderedDict({Symbol("counts"): lit_8, Symbol("@d"): [lit_q2]})
    assert qvar2.get(Symbol("counts")) == lit_8 and qvar2.get(Symbol("@d")) == [lit_q2]


def test_struct_ds_quantum_wrong() -> None:
    qtype = StructDS(name=Symbol("@type"))
    assert isinstance(qtype.add_member(QU3, Symbol("data")), TypeAndMemberNoMatchError)


def test_enum_ds() -> None:
    connect_enum = CompositeSymbol(("command", "CONNECT"))
    _connect = Symbol("CONNECT")
    _join = Symbol("JOIN")
    _quit = Symbol("QUIT")

    command = EnumDS(name=Symbol("command"))
    command.add_member(_connect).add_member(_join).add_member(_quit)

    opt = command(var_name=Symbol("opt"))
    opt.assign(connect_enum)

    assert opt.name == Symbol("opt")
    assert opt.type == Symbol("command")
    assert opt._ds_type is BaseTypeEnum.ENUM
    assert opt.data == OrderedDict({0: _connect})
    assert opt.get() == _connect
    assert opt.get("z") == _connect
    assert opt.is_quantum is False
