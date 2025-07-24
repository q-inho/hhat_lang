from __future__ import annotations

import pytest

from hhat_lang.core.code.symbol_table import SymbolTable
from hhat_lang.core.data.fn_def import BaseFnKey, BaseFnCheck
from hhat_lang.core.data.core import Symbol
from hhat_lang.dialects.heather.code.simple_ir_builder.ir import (
    IRBlock,
    IRCall,
    IRArgs,
)


@pytest.mark.parametrize(
    "fn_key, block, fn_check,",
    [
        (
            # fn sum (a:u64 b:u64) u64 { add(a b) }
            BaseFnKey(
                fn_name=Symbol("sum"),
                fn_type=Symbol("u64"),
                args_names=(
                    Symbol("a"),
                    Symbol("b"),
                ),
                args_types=(
                    Symbol("u64"),
                    Symbol("u64"),
                ),
            ),
            IRBlock(
                IRCall(
                    caller=Symbol("add"),
                    args=IRArgs(Symbol("a"), Symbol("b")),
                )
            ),
            BaseFnCheck(
                fn_name=Symbol("sum"),
                fn_type=Symbol("u64"),
                args_types=(
                    Symbol("u64"),
                    Symbol("u64"),
                ),
            ),
        ),
    ],
)
def test_symboltable_fn(
    fn_key: BaseFnKey, block: IRBlock, fn_check: BaseFnCheck
) -> None:
    st = SymbolTable()
    st.add_fn(fn_key, block)

    assert st.get_fn(fn_check)
