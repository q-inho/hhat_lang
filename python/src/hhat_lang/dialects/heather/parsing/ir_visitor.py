"""Attempt to parse direct to IR"""

from __future__ import annotations

from itertools import chain
from pathlib import Path
from typing import Iterable

from arpeggio import visit_parse_tree, NonTerminal, PTNodeVisitor, SemanticActionResults, Terminal
from arpeggio.cleanpeg import ParserPEG

from hhat_lang.core.code.ast import AST
from hhat_lang.core.types.abstract_base import Size, BaseTypeDataStructure, QSize
from hhat_lang.core.types.builtin_types import builtins_types
from hhat_lang.core.types.core import SingleDS, StructDS
from hhat_lang.dialects.heather.grammar import WHITESPACE

from hhat_lang.core.data.core import (
    CoreLiteral,
    WorkingData,
    CompositeLiteral,
    Symbol,
    CompositeSymbol,
    CompositeWorkingData,
)
from hhat_lang.core.imports import TypeImporter
from hhat_lang.core.memory.core import MemoryManager
from hhat_lang.dialects.heather.code.simple_ir_builder.ir import (
    IR,
    IRBlock,
    IRFlag,
    IRBaseInstr,
    IRTypes,
    IRFns, IRProgram, IRCast, IRCall, IRArgs, IRArgValue,
)
from hhat_lang.dialects.heather.interpreter.classical.executor import Evaluator
from hhat_lang.dialects.heather.parsing.utils import TypesDict, FnsDict, ImportDicts


def read_grammar() -> str:
    grammar_path = Path(__file__).parent.parent / "grammar" / "grammar.peg"

    if grammar_path.exists():
        return open(grammar_path, "r").read()

    raise ValueError("No grammar found on the grammar directory.")


def parse_grammar() -> ParserPEG:
    grammar = read_grammar()
    return ParserPEG(
        language_def=grammar,
        root_rule_name="program",
        comment_rule_name="comment",
        reduce_tree=False,
        ws=WHITESPACE,
    )


def parse(raw_code: str, project_root: Path | str) -> IRProgram:
    parser = parse_grammar()
    parse_tree = parser.parse(raw_code)
    return visit_parse_tree(parse_tree, ParserIRVisitor(project_root))


def parse_file(file: str | Path, project_root: Path | str) -> IRProgram:
    with open(file, "r") as f:
        data = f.read()

    return parse(data, project_root)


class ParserIRVisitor(PTNodeVisitor):
    # TODO: use quantum device configuration number instead hardcoded one
    MAX_NUM_INDEXES = 26

    def __init__(self, project_root: Path):
        super().__init__()
        self._root = project_root
        self._mem = MemoryManager(self.MAX_NUM_INDEXES)
        self._ev = Evaluator(self._mem)

    def visit_program(
        self, node: NonTerminal, child: SemanticActionResults
    ) -> IRProgram:

        main = IR()
        types = IRTypes()
        fns = IRFns()

        for k in child:
            match k:
                case IRBlock():
                    # only main should be an IRBlock by now
                    print(f"[!] program main:\n{k}")
                    main.add_block(k)

                case ImportDicts():
                    # work on the types handler
                    for p, v in k.types.items():
                        types.add(name=p, data=v)

                    # work on the functions handler
                    for p, v in k.fns.items():
                        fns.add(fn_entry=p, data=v)

                case BaseTypeDataStructure():
                    # types definitions from type files
                    types.add(name=k.name, data=k)

                case _:
                    print(f"[?] {k} ({type(k)})")

        program = IRProgram(main=main, types=types, fns=fns)
        return program

    def visit_type_file(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return child[0]

    def visit_typesingle(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> BaseTypeDataStructure:
        # TODO: implement a better resolver to account for custom and circular imports;
        #  for now, just check if it's built-in.

        btype = builtins_types[child[1].value]
        single = SingleDS(name=child[0], size=btype.size, qsize=btype.qsize)
        return single.add_member(btype)

    def visit_typemember(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> tuple:
        # TODO: for now, consider members as built-in only
        member_type = builtins_types[child[1].value]
        member_name = child[0]
        return member_type, member_name

    def visit_typestruct(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> BaseTypeDataStructure:
        # TODO: implement a better resolver to account for custom and circular imports;
        #  for now, just check if it's built-in.

        count_size = 0
        count_qsize_min = 0
        count_qsize_max = 0

        # first, count the size and qsizes
        for member_type, member_name in child[1:]:
            count_size += member_type.size.size
            count_qsize_min += member_type.qsize.min
            count_qsize_max += member_type.qsize.max or 0

        size = Size(count_size)

        if count_qsize_min == 0 and count_qsize_max == 0:
            qsize = None

        else:
            qsize = QSize(count_qsize_min, count_qsize_max or None)

        struct = StructDS(name=child[0], size=size, qsize=qsize)

        # second, populate struct
        for t, m in child[1:]:
            struct.add_member(t, m)

        return struct

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
        print(f"[!] body: {[k for k in child]}")

        values = ()
        for k in child:
            match k:
                case IRBaseInstr():
                    print(f"IR instr: {k}")
                    values += k,
                case IRBlock():
                    print(f"IR block: {k}")
                    values += k,
                case _:
                    print(f"something else: {k}")
        block = IRBlock(*values)
        return block

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
    ) -> WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        # returning the child; there should exist only one element
        print(f"[!] expr elem: {child}" if len(child) > 1 else "", end="")
        return child[0]

    def visit_cast(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IRBaseInstr:
        print(f"[!] cast {child}")
        return IRCast(cast_data=child[0], to_type=child[1])

    def visit_call(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IRBaseInstr:
        print(f"[!] call {child}")
        if len(child) == 2:
            return IRCall(caller=child[0], args=child[1])

        # TODO: resolve this later
        for k in child:
            print(f"  -> call item: {k} ({type(k)}")
        return child

    def visit_trait_id(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        print(f"[!] trait id?")
        return ()

    def visit_args(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IRBaseInstr:
        print(f"[!] args {child}")
        return IRArgs(*child)

    def visit_callargs(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IRBaseInstr:
        return IRArgValue(arg_name=child[0], value=child[1])

    def visit_valonly(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return child[0]

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
        # Id composite value should have only one value
        return child[0]

    def visit_imports(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> ImportDicts:
        instrs = tuple(chain.from_iterable(child))
        importer = TypeImporter(self._root)
        res = importer.import_types(instrs)

        # parsing each type and function
        types = TypesDict()
        fns = FnsDict()

        for k, v in zip(instrs, res.values()):
            parsed_ir: IRProgram = parse_file(v, self._root)

            if len(parsed_ir.types) > 0:
                types[k] = parsed_ir.types.table[Symbol(k.value[-1])]

            elif len(parsed_ir.fns) > 0:
                # TODO: implement this
                raise NotImplementedError()

            else:
                raise ValueError(
                    f"[{k}:{v}] {parsed_ir.types=} types len={len(parsed_ir.types)}, {parsed_ir.fns} fns len={len(parsed_ir.fns)}"
                )

        parsed_types = ImportDicts(types=types, fns=fns)
        return parsed_types

    def visit_typeimport(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        if isinstance(child[0], tuple):
            return IRBlock(*tuple(k for k in child[0]))
        raise ValueError("type import not tuple?")

    def visit_fnimport(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        pass

    def visit_single_import(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return child[0] if isinstance(child[0], tuple) else (child[0],)

    def visit_many_import(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return tuple(chain.from_iterable(child))

    def visit_main(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        instrs = ()
        for k in child:
            match k:
                case IRBlock():
                    print(f"  -> block {k}")
                    instrs += k,
                case IRBaseInstr():
                    print(f"  => instr {k}")
                    for p, q in k.block_refs.items():
                        print(f"   -> ref: {p}={q}")
                    instrs += k,
                case tuple():
                    print(f"  -> tuple {k}")
                    instrs += k
                case _:
                    raise ValueError(f"unknown {k} ({type(k)})")

        block = IRBlock(*instrs)
        ir = IR()
        ir.add_block(block)
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
        self, node: Terminal, _: None
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
        self, node: Terminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="null")

    def visit_bool(
        self, node: Terminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="bool")

    def visit_str(
        self, node: NonTerminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="str")

    def visit_int(
        self, node: Terminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="int")

    def visit_float(
        self, node: Terminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        print(f"[!] float {node}")
        return CoreLiteral(value=node.value, lit_type="float")

    def visit_imag(
        self, node: Terminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="imag")

    def visit_q__bool(
        self, node: Terminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="@bool")

    def visit_q__int(
        self, node: Terminal, _: None
    ) -> IR | WorkingData | CompositeWorkingData | IRBlock | IRBaseInstr | tuple:
        return CoreLiteral(value=node.value, lit_type="@int")


def _resolve_data_to_str(
    data: SemanticActionResults | tuple | WorkingData | CompositeWorkingData | str
) -> tuple | tuple[str, ...]:

    match data:
        case WorkingData():
            return (data.value,)

        case CompositeWorkingData():
            return _resolve_data_to_str(data.value)

        case SemanticActionResults() | tuple():
            pure_data: tuple | tuple[str, ...] = ()

            for k in data:
                if isinstance(k, WorkingData):
                    pure_data += k.value,

                elif isinstance(k, str):
                    pure_data += k,

                elif isinstance(k, CompositeWorkingData):
                    pure_data += k.value

            return pure_data

        case str():
            return (data,)

        case _:
            raise NotImplementedError()


def _flatten_recursive_closure(
    data: SemanticActionResults | tuple[str | Symbol | CompositeSymbol | list | tuple, ...]
) -> tuple | tuple[CompositeSymbol, ...]:

    members: tuple | tuple[CompositeSymbol, ...] = ()
    parent: str | WorkingData | CompositeWorkingData | None = None
    composite_members: tuple[CompositeSymbol, ...] | tuple = ()

    for n, k in enumerate(data):
        if n == 0:
            if isinstance(k, Symbol):
                parent = k.value
                continue
            elif isinstance(k, str):
                parent = k
                continue

        if isinstance(k, SemanticActionResults | tuple):
            members += _flatten_recursive_closure(k)

        else:
            members += _resolve_data_to_str(k),

    if parent is None:
        return members

    for k in members:
        composite_members += CompositeSymbol(_resolve_data_to_str(parent) + k),

    return composite_members
