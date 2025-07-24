"""Attempt to parse direct to IR"""

from __future__ import annotations

from itertools import chain
from pathlib import Path
from typing import Any

from arpeggio import visit_parse_tree, NonTerminal, PTNodeVisitor, SemanticActionResults, Terminal
from arpeggio.cleanpeg import ParserPEG

from hhat_lang.core.data.fn_def import FnDef, BaseFnCheck
from hhat_lang.core.imports.importer import FnImporter
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
from hhat_lang.core.code.symbol_table import TypeTable, FnTable
from hhat_lang.dialects.heather.code.simple_ir_builder.new_ir import (
    IR,
    IRBlock,
    IRInstr,
    CallInstr,
    CastInstr,
    AssignInstr,
    DeclareInstr,
    ArgsBlock,
    ArgsValuesBlock,
    ModifierBlock,
    ModifierArgsBlock,
    BodyBlock,
    OptionBlock,
    ReturnBlock,
    DeclareAssignInstr,
)
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


def parse(raw_code: str, project_root: Path | str) -> IR:
    parser = parse_grammar()
    parse_tree = parser.parse(raw_code)
    return visit_parse_tree(parse_tree, ParserIRVisitor(project_root))


def parse_file(file: str | Path, project_root: Path | str) -> IR:
    with open(file, "r") as f:
        data = f.read()

    return parse(data, project_root)


class ParserIRVisitor(PTNodeVisitor):
    """Visitor for parsing using IR code logic instead of AST's"""

    def __init__(self, project_root: Path):
        super().__init__()
        self._root = project_root
        # self._mem = MemoryManager(self.MAX_NUM_INDEXES)

    def visit_program(
        self, node: NonTerminal, child: SemanticActionResults
    ) -> IR:

        main = BodyBlock()
        types = TypeTable()
        fns = FnTable()

        for k in child:
            match k:
                case IRBlock():
                    # only main should be an IRBlock by now
                    if isinstance(k, BodyBlock):
                        main = k

                    else:
                        main.add(k)

                case ImportDicts():
                    # work on the types handler
                    for p, v in k.types.items():
                        types.add(name=p, data=v)

                    # work on the functions handler
                    for p, v in k.fns.items():
                        for q, r in v.items():
                            fns.add(fn_entry=q, data=r)

                case BaseTypeDataStructure():
                    # types definitions from type files
                    types.add(name=k.name, data=k)

                case FnDef():
                    fns.add(fn_entry=k.get_fn_check(), data=k)

                case _:
                    print(f"[?] {k} ({type(k)})")

        program = IR(main=main, types=types, fns=fns)
        return program

    def visit_type_file(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> BaseTypeDataStructure:
        return child[0]

    def visit_typesingle(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> BaseTypeDataStructure:
        # TODO: implement a better resolver to account for custom and circular imports;
        #  for now, just check if it's built-in.

        btype = builtins_types[child[1]]
        single = SingleDS(name=child[0], size=btype.size, qsize=btype.qsize)
        return single.add_member(btype)

    def visit_typemember(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> tuple:
        # TODO: for now, consider members as built-in only
        member_type = builtins_types[child[1]]
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
    ) -> Any:
        raise NotImplementedError()

    def visit_typeunion(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> Any:
        raise NotImplementedError()

    def visit_enumnumber(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> Any:
        raise NotImplementedError()

    def visit_fns(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> FnDef:
        if len(child) == 4:
            return FnDef(
                fn_name=child[0],
                fn_args=child[1],
                fn_type=child[2],
                fn_body=child[3]
            )

        return FnDef(
            fn_name=child[0],
            fn_args=child[1],
            fn_type=None,
            fn_body=child[2]
        )

    def visit_fnargs(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> ArgsBlock:
        return ArgsBlock(*child)

    def visit_argtype(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> ArgsValuesBlock:
        return ArgsValuesBlock((child[0], child[1]))

    def visit_fn_body(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> BodyBlock:
        return BodyBlock(*child)

    def visit_body(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> BodyBlock:
        values = ()
        for k in child:
            match k:
                case IRInstr():
                    values += k,

                case IRBlock():
                    values += k,

                case _:
                    print(f"    -> something else: {k} ({type(k)})")

        return BodyBlock(*values)

    def visit_declare(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> DeclareInstr:
        if len(child) == 2:
            return DeclareInstr(var=child[0], var_type=child[1])

        if len(child) == 3:
            return DeclareInstr(var=ModifierBlock(obj=child[0], args=child[1]), var_type=child[2])

        raise ValueError("declaring variable must have only variable and its type")

    def visit_assign(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> AssignInstr:
        return AssignInstr(var=child[0], value=child[1])

    def visit_assign_ds(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> AssignInstr:
        return AssignInstr(var=child[0], value=ArgsBlock(*child[1:]))

    def visit_declareassign(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> DeclareAssignInstr:
        if len(child) == 3:
            return DeclareAssignInstr(var=child[0], var_type=child[1], value=child[2])

        if len(child) == 4:
            return DeclareAssignInstr(
                var=ModifierBlock(
                    obj=child[0],
                    args=child[1]
                ),
                var_type=child[2],
                value=child[3]
            )

        raise ValueError("declaring and assigning cannot contain more than 4 elements")

    def visit_declareassign_ds(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> Any:
        if len(child) == 3:
            return DeclareAssignInstr(var=child[0], var_type=child[1], value=ArgsBlock(*child[2:]))

        if len(child) == 4:
            return DeclareAssignInstr(
                var=ModifierBlock(
                    obj=child[0],
                    args=child[1]
                ),
                var_type=child[2],
                value=child[3]
            )

        raise ValueError("declaring and assigning cannot contain more than 4 elements")

    def visit_return(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> ReturnBlock:
        return ReturnBlock(*child)

    def visit_expr(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IRBlock | IRInstr | Symbol | CompositeSymbol:
        # returning the child; there should exist only one element
        return child[0]

    def visit_cast(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> CastInstr:
        return CastInstr(data=child[0], to_type=child[1])

    def visit_call(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> CallInstr | ModifierBlock:
        if len(child) == 1:
            # only the caller is present
            return CallInstr(name=child[0])

        if len(child) == 2:
            # possible cases: trait_id, args, or modifier
            match child[1]:
                # args option
                case ArgsBlock() | ArgsValuesBlock():
                    return CallInstr(name=child[0], args=child[1])

                # modifier option
                case ModifierArgsBlock():
                    return ModifierBlock(obj=CallInstr(name=child[0]), args=child[1])

                # trait_id option
                case Symbol() | CompositeSymbol() | ModifierBlock():
                    raise NotImplementedError("trait not implemented yet")

                case _:
                    raise NotImplementedError("unkown case")

        if len(child) == 3:
            # possible cases: trait_id and args, trait_id and modifier, args and modifier
            match (child[1], child[2]):
                # args and modifier
                case (ArgsBlock() | ArgsValuesBlock(), ModifierArgsBlock()):
                    return ModifierBlock(CallInstr(name=child[0], args=child[1]), args=child[2])

                # trait and something
                case _:
                    raise NotImplementedError()

        if len(child) == 4:
            # everything together :)
            raise NotImplementedError()

        raise ValueError("call cannot have len 0 or > 4")

    def visit_trait_id(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> Any:
        raise NotImplementedError()

    def visit_args(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> ArgsBlock | ArgsValuesBlock:
        argsvalues = ()
        args = ()

        for k in child:
            match k:
                case ArgsValuesBlock():
                    argsvalues += k,

                case IRInstr() | ModifierBlock():
                    args += k,

                case WorkingData() | CompositeWorkingData():
                    args += k,

                case _:
                    raise ValueError(f"unexpected value from args ({k}, {type(k)})")

        if len(argsvalues) != 0 and len(args) != 0:
            raise ValueError(
                "arguments in functino call cannot mix key-value pairs with value only"
            )

        if args:
            return ArgsBlock(*args)

        return ArgsValuesBlock(*argsvalues)

    def visit_assignargs(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> ArgsValuesBlock:
        if len(child) == 2:
            return ArgsValuesBlock((child[0], child[1]))

        raise ValueError("assigning arg with value cannot have more than an argument and a value")

    def visit_callargs(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> ArgsValuesBlock:
        return ArgsValuesBlock((child[0], child[1]))

    def visit_valonly(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> WorkingData | CompositeWorkingData:
        return child[0]

    def visit_option(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> OptionBlock:
        return OptionBlock(*child[1:], block=child[0])

    def visit_callwithbody(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> CallInstr:
        raise NotImplementedError()

    def visit_callwithbodyoptions(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> CallInstr:

        args: tuple = ()
        body: BodyBlock | None = None

        for k in child[1:]:
            match k:
                case ArgsBlock() | ArgsValuesBlock():
                    args += k,
                case BodyBlock():
                    body = k
                case _:
                    raise ValueError(f"unexpected value on call with body options {k} ({type(k)})")

        return CallInstr(name=child[0], args=args or None, body=body)

    def visit_callwithargsoptions(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> CallInstr:
        return CallInstr(name=child[0], option=child[1])

    def visit_id_composite_value(
        self, node: NonTerminal, child: SemanticActionResults
    ) -> CompositeSymbol | tuple:
        # Id composite value should have only one value
        return child[0]

    def visit_imports(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> ImportDicts:
        types = TypesDict()
        fns = FnsDict()

        for k in child:
            match k:
                case TypesDict():
                    types.update({p: q for p, q in k.items()})

                case FnsDict():
                    fns.update({p: q for p, q in k.items()})

        parsed_imports = ImportDicts(types=types, fns=fns)
        return parsed_imports

    def visit_typeimport(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> TypesDict:
        if isinstance(child[0], tuple):
            types = TypesDict()
            importer = TypeImporter(self._root, parse)
            res = importer.import_types(child[0])

            for k, v in zip(child[0], res.values()):
                types[k] = v

            return types

        raise ValueError("type import not tuple?")

    def visit_fnimport(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> FnsDict:
        if isinstance(child[0], tuple):
            fns = FnsDict()
            importer = FnImporter(self._root, parse)
            res = importer.import_fns(child[0])

            for vals in res.values():
                for p, q in vals.items():
                    if isinstance(p, BaseFnCheck):
                        names = tuple(k.arg for k in q.args)
                        fns[p.transform(fn_type=q.type, args_names=names)] = q

            return fns

        raise ValueError("fn import no tuple?")

    def visit_single_import(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> tuple[Symbol | CompositeSymbol] | tuple:
        if len(child) > 1:
            raise ValueError("single import cannot contain more than one import")

        return child[0] if isinstance(child[0], tuple) else (child[0],)

    def visit_many_import(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> tuple:
        return tuple(chain.from_iterable(child))

    def visit_main(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> IRBlock | tuple:
        if len(child) == 0:
            return ()

        return BodyBlock(*child)

    def visit_composite_id_with_closure(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> tuple[CompositeSymbol, ...] | tuple:
        return _flatten_recursive_closure(child)

    def visit_id(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> Symbol | CompositeSymbol | ModifierBlock:
        if len(child) == 1:
            return child[0]

        if len(child) == 2:
            return ModifierBlock(obj=child[0], args=child[1])

        raise NotImplementedError("symbol with modifier not implemented yet")

    def visit_modifier(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> ModifierArgsBlock:
        return ModifierArgsBlock(tuple(k for k in child))

    def visit_array(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> CompositeWorkingData:
        raise NotImplementedError("array not implemented yet")

    def visit_composite_id(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> CompositeSymbol:
        return CompositeSymbol(value=_resolve_data_to_str(child))

    def visit_simple_id(
        self, node: Terminal, _: None
    ) -> Symbol:
        return Symbol(value=node.value)

    def visit_literal(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> CoreLiteral | CompositeLiteral:
        return child[0]

    def visit_complex(
        self, _: NonTerminal, child: SemanticActionResults
    ) -> CompositeLiteral:
        raise NotImplementedError("complex type not implemented yet")

    def visit_null(
        self, node: Terminal, _: None
    ) -> CoreLiteral:
        return CoreLiteral(value=node.value, lit_type="null")

    def visit_bool(
        self, node: Terminal, _: None
    ) -> CoreLiteral:
        return CoreLiteral(value=node.value, lit_type="bool")

    def visit_str(
        self, node: NonTerminal, _: None
    ) -> CoreLiteral:
        return CoreLiteral(value=node.value, lit_type="str")

    def visit_int(
        self, node: Terminal, _: None
    ) -> CoreLiteral:
        return CoreLiteral(value=node.value, lit_type="int")

    def visit_float(
        self, node: Terminal, _: None
    ) -> CoreLiteral:
        return CoreLiteral(value=node.value, lit_type="float")

    def visit_imag(
        self, node: Terminal, _: None
    ) -> CoreLiteral:
        return CoreLiteral(value=node.value, lit_type="imag")

    def visit_q__bool(
        self, node: Terminal, _: None
    ) -> CoreLiteral:
        return CoreLiteral(value=node.value, lit_type="@bool")

    def visit_q__int(
        self, node: Terminal, _: None
    ) -> CoreLiteral:
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
