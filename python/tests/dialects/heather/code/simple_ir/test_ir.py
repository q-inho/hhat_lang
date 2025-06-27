from __future__ import annotations

from hhat_lang.core.data.core import Symbol, CoreLiteral
from hhat_lang.dialects.heather.code.simple_ir_builder.ir import (
    IR,
    IRBlock,
    IRDeclare,
    IRAssign,
    IRArgs,
    IRCall, IRFlag,
)


def test_dac1() -> None:
    qq = Symbol("@q")
    q1 = CoreLiteral("@1", lit_type="@int")
    qu3 = Symbol("@u3")
    qredim = Symbol("@redim")

    i1 = IRDeclare(var=qq, var_type=qu3)
    assert i1.instr == IRFlag.DECLARE
    assert i1.args == (qq, qu3)

    i2 = IRAssign(var=qq, value=q1)
    assert i2.instr == IRFlag.ASSIGN
    assert i2.args == (qq, q1)

    i3 = IRCall(caller=qredim, args=IRArgs(qq))
    i3_args_block_name = IRBlock(IRArgs(qq)).name
    assert i3.instr == IRFlag.CALL
    assert i3.args == (qredim, i3_args_block_name)

    block1 = IRBlock(i1, i2, i3)
    assert block1.instrs == (i1, i2, i3)

    ir1 = IR()
    ir1.add_block(block1)
    assert block1.name in ir1.table
    assert ir1.table[block1.name] == block1

    print()
    print(ir1)
