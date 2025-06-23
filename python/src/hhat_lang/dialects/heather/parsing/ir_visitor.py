"""Attempt to parse direct to IR"""

from __future__ import annotations

from arpeggio import NonTerminal, PTNodeVisitor, SemanticActionResults, Terminal
from mypy.literals import literal

from hhat_lang.core.data.core import (
    CoreLiteral,
    WorkingData,
    CompositeLiteral,
    Symbol,
    CompositeSymbol,
    CompositeWorkingData,
)
from hhat_lang.core.memory.core import MemoryManager
from hhat_lang.dialects.heather.code.simple_ir_builder.ir import (
    IR,
    IRBlock,
    IRFlag,
    IRBaseInstr,
)
from hhat_lang.dialects.heather.interpreter.classical.executor import Evaluator


class ParserIRVisitor(PTNodeVisitor):
    # TODO: use quantum device configuration number instead hardcoded one
    MAX_NUM_INDEXES = 100

    def __init__(self):
        super().__init__()
        self._mem = MemoryManager(self.MAX_NUM_INDEXES)
        self._ev = Evaluator(self._mem)

    def visit_program(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_type_file(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_typesingle(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_typemember(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_typestruct(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_typeenum(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_typeunion(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_enumnumber(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_fns(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_fnargs(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_argtype(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_fn_body(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_body(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_declare(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_assign(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_declareassign(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_return(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_expr(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_cast(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_call(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_trait_id(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_args(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_callargs(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_valonly(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_option(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_callwithbody(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_callwithbodyoptions(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_callwithargsoptions(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        raise NotImplementedError()

    def visit_id_composite_value(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_imports(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_typeimport(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_fnimport(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_single_import(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_many_import(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_main(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        instrs = ()
        for k in child:
            if isinstance(k, IRBaseInstr):
                instrs += k,

            elif isinstance(k, tuple):
                print(f"[!] main: {tuple((p, type(p)) for p in k)}")
                instrs += k

            elif isinstance(k, WorkingData):
                raise ValueError(f"something went wrong on building 'main': {k}")

        block = IRBlock(*instrs)
        print(f"[!] main\n{block}")
        ir = IR()
        ir.add_new_block(block)
        return ir

    def visit_composite_id_with_closure(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return _flatten_recursive_closure(child)

    def visit_id(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        if len(child) == 1:
            return child[0]

        raise NotImplementedError("symbol with modifier not implemented yet")

    def visit_modifier(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        raise NotImplementedError("modifier not implemented yet")

    def visit_array(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        raise NotImplementedError("array not implemented yet")

    def visit_composite_id(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CompositeSymbol(value=_resolve_data_to_str(child))

    def visit_simple_id(
        self, node: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return Symbol(value=node.value)

    def visit_literal(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return child[0]

    def visit_complex(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        raise NotImplementedError("complex type not implemented yet")

    def visit_null(
        self, node: NonTerminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="null")

    def visit_bool(
        self, node: NonTerminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="bool")

    def visit_str(
        self, node: NonTerminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="str")

    def visit_int(
        self, node: NonTerminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="int")

    def visit_float(
        self, node: NonTerminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="@float")

    def visit_imag(
        self, node: NonTerminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="@imag")

    def visit_q__bool(
        self, node: NonTerminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="@bool")

    def visit_q__int(
        self, node: NonTerminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="@int")


def _resolve_data_to_str(
    data: SemanticActionResults | tuple | WorkingData | CompositeWorkingData
) -> tuple | tuple[str, ...]:

    pure_data: tuple | tuple[str]

    match data:
        case WorkingData():
            pure_data = (data.value,)

        case CompositeWorkingData():
            pure_data = _resolve_data_to_str(data.value)

        case SemanticActionResults() | tuple():
            pure_data = ()

            for k in data:
                if isinstance(k, WorkingData):
                    pure_data += k.value,

                elif isinstance(k, str):
                    pure_data += k,

                elif isinstance(k, CompositeWorkingData):
                    pure_data += k.value

        case _:
            raise NotImplementedError()

    return pure_data


def _flatten_recursive_closure(data) -> tuple | tuple[CompositeSymbol, ...]:
    members: tuple | tuple[CompositeSymbol, ...] = ()
    parent = data[0].value

    for k in data[1:]:
        if isinstance(k, SemanticActionResults | list | tuple):
            members += CompositeSymbol(_flatten_recursive_closure((parent, k))),

        else:
            members += CompositeSymbol(_resolve_data_to_str((parent, k))),

    return members
