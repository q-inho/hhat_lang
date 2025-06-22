from __future__ import annotations

from itertools import product

import pytest
from hhat_lang.core.code.ir import TypeIR
from hhat_lang.core.data.core import CoreLiteral, Symbol
from hhat_lang.core.memory.core import MemoryManager, SymbolTable
from hhat_lang.dialects.heather.code.simple_ir_builder.ir import (
    FnIR,
    IRArgs,
    IRBlock,
    IRCall,
)
from hhat_lang.dialects.heather.interpreter.classical.executor import Evaluator
from hhat_lang.dialects.heather.interpreter.quantum.program import Program
from hhat_lang.low_level.quantum_lang.openqasm.v2.qlang import LowLeveQLang


# FIXME: skipping whole file until LowLeveLQLang is fixed with the new IR
pytest.skip(
    "skipping whole file until LowLeveLQLang is fixed with the new IR",
    allow_module_level=True
)


def test_simple_empty_redim_program(MAX_ATOL_STATES_GATE: float) -> None:
    qv = Symbol("@v")

    mem = MemoryManager(5)
    mem.idx.add(qv, 1)
    mem.idx.request(qv)

    ex = Evaluator(mem, TypeIR(), FnIR())

    block = IRBlock(IRCall(Symbol("@redim"), IRArgs()))

    program = Program(
        qdata=qv, idx=mem.idx, block=block, qlang=LowLeveQLang, executor=ex, symboltable=SymbolTable()
    )

    res = program.run(debug=False)
    assert (abs(res["1"] - res["0"]) / (res["1"] + res["0"])) < MAX_ATOL_STATES_GATE


@pytest.mark.parametrize("ql", [CoreLiteral("@0", "@u2"), CoreLiteral("@2", "@u2")])
def test_simple_literal_redim_program(
    ql: CoreLiteral, MAX_ATOL_STATES_GATE: float
) -> None:
    mem = MemoryManager(5)
    mem.idx.add(ql, 2)
    mem.idx.request(ql)

    ex = Evaluator(mem, TypeIR(), FnIR())

    block = IRBlock(IRCall(caller=Symbol("@redim"), args=IRArgs(ql)))

    table = SymbolTable()

    program = Program(
        qdata=ql, idx=mem.idx, block=block, qlang=LowLeveQLang, executor=ex, symboltable=table
    )

    res = program.run(debug=False)

    assert {"".join(k) for k in product("01", repeat=2)} == set(res.keys())
    assert all(
        abs(1 / 4 - k / sum(res.values())) < MAX_ATOL_STATES_GATE for k in res.values()
    )
