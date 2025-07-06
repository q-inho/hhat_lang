from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Iterable, cast

from hhat_lang.core.data.core import (
    Symbol,
    CompositeSymbol,
    WorkingData,
    CompositeWorkingData,
    CoreLiteral,
    CompositeLiteral,
)
from hhat_lang.core.data.fn_def import BaseFnKey
from hhat_lang.core.data.utils import VariableKind
from hhat_lang.core.data.variable import VariableTemplate, BaseDataContainer
from hhat_lang.core.error_handlers.errors import HeapInvalidKeyError
from hhat_lang.core.memory.core import Heap
from hhat_lang.core.types.abstract_base import BaseTypeDataStructure
from hhat_lang.core.types.builtin_types import builtins_types, compatible_types


###########################
# IR INSTRUCTIONS CLASSES #
###########################

class IRFlag(Enum):
    """
    Used to identify the ``IRBaseInstr`` child class purpose. Ex: a ``CallInstr``
    class is defined with its name as ``IRFlag.CALL``.
    """

    NULL = auto()
    CALL = auto()
    CAST = auto()
    ASSIGN = auto()
    DECLARE = auto()
    DECLARE_ASSIGN = auto()
    ARGS = auto()
    ARG_VALUE = auto()
    OPTION = auto()
    COND = auto()
    MATCH = auto()
    CALL_WITH_BODY = auto()
    CALL_WITH_OPTION = auto()
    RETURN = auto()


class IRInstr(ABC):
    """
    Base class for IR instructions. Custom IR instructions names must adhere to
    IRFlag enum attributes. For example::


        class DeclareInstr(IRInstr):
            def __init__(self, ...):
                ...
                super().__init__(..., name=IRFlag.DECLARE)
    """

    _name: IRFlag
    args: tuple[IRBlock | WorkingData | CompositeWorkingData, ...] | tuple

    def __init__(
        self,
        *args: IRBlock | WorkingData | CompositeWorkingData,
        name: IRFlag
    ):
        if (
            all(isinstance(k, IRBlock | WorkingData | CompositeWorkingData) for k in args)
            and isinstance(name, IRFlag)
        ):
            self._name = name
            self.args = args

        else:
            raise ValueError(
                f"IR instr {self.__class__.__name__} must received name as {type(name)},"
                f" args as {type(args)}. Check for correct types."
            )

    @property
    def name(self) -> IRFlag:
        return self._name

    @abstractmethod
    def resolve(self, *args: Any, **kwargs: Any) -> Any:
        """
        To resolve pending type imports to ``IRTypes`` and function imports to ``IRFns``,
        type checks on built-in types or custom types at ``IRTypes`` or var checks in the
        ``Heap`` memory, and so on.
        """

    def __iter__(self) -> Iterable:
        yield from self.args

    def __repr__(self) -> str:
        return f"{self.name}({', '.join(str(k) for k in self.args)})"


class CallInstr(IRInstr):
    def __init__(
        self,
        name: Symbol | CompositeSymbol,
        args: ArgsBlock | ArgsValuesBlock | WorkingData | CompositeWorkingData,
        option: OptionBlock | None = None,
        body: BodyBlock | None = None,
    ):
        if option is None and body is None:
            instr_args = (args,)
            flag = IRFlag.CALL

        elif option is not None and body is None:
            instr_args = (args, option)
            flag = IRFlag.CALL_WITH_OPTION

        elif option is None and body is not None:
            instr_args = (args, body)
            flag = IRFlag.CALL_WITH_BODY

        else:
            raise ValueError(
                f"cannot contain option ({type(option)}) and body ({type(body)}) "
                f"in the same instruction."
            )

        super().__init__(name, *instr_args, name=flag)

    def resolve(self):
        pass


class DeclareInstr(IRInstr):
    def __init__(self, var: Symbol, var_type: Symbol | CompositeSymbol):
        if isinstance(var, Symbol) and isinstance(var_type, Symbol | CompositeSymbol):
            super().__init__(var, var_type, name=IRFlag.DECLARE)

        else:
            raise ValueError(
                f"var must be symbol, got {type(var)} and var type must be symbol"
                f" or composite symbol, got {type(var_type)}"
            )

    def resolve(self, *, heap_table: Heap, types_table: IRTypes) -> Any:
        var: Symbol = cast(Symbol, self.args[0])
        variable = _get_declare_variable(var=var, heap=heap_table, types_table=types_table)
        heap_table.set(key=var, value=variable)


class AssignInstr(IRInstr):
    def __init__(self, var: Symbol, value: WorkingData | CompositeWorkingData | IRBlock):
        if (
            isinstance(var, Symbol)
            and isinstance(value, WorkingData | CompositeWorkingData | IRBlock)
        ):
            super().__init__(var, value, name=IRFlag.ASSIGN)

        else:
            raise ValueError(
                f"var must be symbol, got {type(var)} and "
                f"value must be working data or composite working data, got {type(value)}"
            )

    def resolve(self, *, heap_table: Heap, types_table: IRTypes) -> Any:
        var: Symbol = cast(Symbol, self.args[0])
        # retrieve variable from heap
        variable = heap_table.get(var)
        value = self.args[1]

        # resolve value to check and assign the correct type
        new_args = _get_assign_datatype(
            var_type=variable.type,
            value=value,
            heap=heap_table,
            types_table=types_table
        )
        # set new arguments
        self.args = (self.args[0], *new_args)
        _assign_variable(*new_args, variable=variable)


class DeclareAssignInstr(IRInstr):
    def __init__(
        self,
        var: Symbol,
        var_type: Symbol | CompositeSymbol,
        value: WorkingData | CompositeWorkingData,
    ):
        if (
            isinstance(var, Symbol)
            and isinstance(var_type, Symbol | CompositeSymbol)
            and isinstance(value, WorkingData | CompositeWorkingData)
        ):
            super().__init__(var, var_type, value, name=IRFlag.DECLARE_ASSIGN)

        else:
            raise ValueError(
                f"var must be symbol, got {type(var)}, "
                f"var type must be symbol or composite symbol, got {type(var_type)} and "
                f"value must be working data or composite working data, got {type(value)}"
            )

    def resolve(self, *, heap_table: Heap, types_table: IRTypes) -> Any:
        var: Symbol = cast(Symbol, self.args[0])
        variable = _get_declare_variable(var=var, heap=heap_table, types_table=types_table)
        heap_table.set(key=var, value=variable)

        value = self.args[1]

        # resolve value to check and assign the correct type
        new_args = _get_assign_datatype(
            var_type=variable.type,
            value=value,
            heap=heap_table,
            types_table=types_table
        )
        # set new arguments
        self.args = (self.args[0], *new_args)
        _assign_variable(*new_args, variable=variable)


####################
# IR BLOCK CLASSES #
####################

class IRBlockFlag(Enum):
    """Define all valid IR block flags for IR blocks"""

    BODY = auto()
    ARGS = auto()
    ARGS_VALUES = auto()
    OPTION = auto()


class IRBlock(ABC):
    """
    IR blocks
    """

    _name: IRBlockFlag
    args: tuple

    @property
    def name(self) -> IRBlockFlag:
        return self._name

    def __iter__(self) -> Iterable:
        yield from self.args

    def __repr__(self) -> str:
        return "\n".join(str(k) for k in self.args)


class BodyBlock(IRBlock):
    _name: IRBlockFlag.BODY

    def __init__(self, *args: IRBlock | IRInstr):
        if all(isinstance(k, IRBlock | IRInstr) for k in args):
            self.args = args

        else:
            raise ValueError(
                f"args must be block or instruction, but got {tuple(type(k) for k in args)}"
            )


class ArgsBlock(IRBlock):
    _name: IRBlockFlag.ARGS

    def __init__(self, *args: IRInstr):
        if all(isinstance(k, IRBlock | IRInstr) for k in args):
            self.args = args

        else:
            raise ValueError(
                f"args must be block or instruction, but got {tuple(type(k) for k in args)}"
            )


class ArgsValuesBlock(IRBlock):
    _name: IRBlockFlag.ARGS_VALUES

    def __init__(
        self,
        *args: tuple[Symbol, WorkingData | CompositeWorkingData | IRBlock | IRInstr]
    ):
        if all(
            isinstance(k[0], Symbol)
            and isinstance(k[1], WorkingData | CompositeWorkingData | IRBlock | IRInstr)
            for k in args
        ):
            self.args = args

        else:
            raise ValueError(
                f"args must be symbols and values must be symbol, composite symbols,"
                f" block or instruction, but got {tuple(type(k) for k in args)}"
            )


class OptionBlock(IRBlock):
    _name: IRBlockFlag.OPTION

    def __init__(
        self,
        option: WorkingData | CompositeWorkingData | IRBlock | IRInstr,
        block: IRBlock | IRInstr,
    ):
        if (
            isinstance(option, WorkingData | CompositeWorkingData | IRBlock | IRInstr)
            and isinstance(block, IRBlock | IRInstr)
        ):
            self.args = (option, block)

        else:
            raise ValueError(f"option ({type(option)}) or block ({type(block)}) is of wrong type.")


##############
# IR CLASSES #
##############

class IRTypes:
    """
    This class holds types definitions as ``BaseTypeDataStructure`` objects.

    Together with ``IRFns`` and ``IR`` it provides the base for an IR object
    picturing the full code.
    """

    table: dict[Symbol | CompositeSymbol, BaseTypeDataStructure]

    def __init__(self):
        self.table = dict()

    def add(self, name: Symbol | CompositeSymbol, data: BaseTypeDataStructure) -> None:
        if (
            isinstance(name, Symbol | CompositeSymbol)
            and isinstance(data, BaseTypeDataStructure)
        ):
            if name not in self.table:
                self.table[name] = data

        else:
            raise ValueError(
                f"type {name} must be symbol/composite symbol and its data must be "
                f"known type structure"
            )

    def get(
        self,
        name: Symbol | CompositeSymbol,
        default: Any | None = None
    ) -> BaseTypeDataStructure | Any | None:
        return self.table.get(name, default)

    def __contains__(self, item: Symbol | CompositeSymbol) -> bool:
        return item in self.table

    def __len__(self) -> int:
        return len(self.table)

    def __repr__(self) -> str:
        content = "\n      ".join(f"{v}" for v in self.table.values())
        return f"\n  types:\n      {content}\n"


class IRFns:
    """
    This class holds functions definitions as ``BaseFnKey`` for function
    entry (function name, type and arguments) and its body (content).

    Together with ``IRTypes`` and ``IR`` it provides the base for an IR object
    picturing the full code.
    """

    table: dict[BaseFnKey, IRBlock]

    def __init__(self):
        self.table = dict()

    def add(self, fn_entry: BaseFnKey, data: IRBlock) -> None:
        if (
            fn_entry not in self.table
            and isinstance(fn_entry, BaseFnKey)
            and isinstance(data, IRBlock)
        ):
            self.table[fn_entry] = data

    def __len__(self) -> int:
        return len(self.table)

    def __repr__(self) -> str:
        content = "\n      ".join(f"{k}:\n          {v}" for k, v in self.table.items())
        return f"\n  fns:\n      {content}\n"


class IR:
    """Hold all the IR content: IR blocks, IR types and IR functions"""

    main: IRBlock | None
    types: IRTypes | None
    fns: IRFns | None

    def __init__(
        self,
        *,
        main: IRBlock | None = None,
        types: IRTypes | None = None,
        fns: IRFns | None = None
    ):
        if (
            isinstance(main, IRBlock)
            or main is None
            and isinstance(types, IRTypes)
            or types is None
            and isinstance(fns, IRFns)
            or fns is None
        ):
            self.main = main
            self.types = types
            self.fns = fns

    def __repr__(self) -> str:
        return f"\n[ir/start]{self.types}{self.fns}{self.main}[ir/end]\n"


##################
# MISC FUNCTIONS #
##################

def _get_declare_variable(
    var: Symbol,
    heap: Heap,
    types_table: IRTypes
) -> BaseDataContainer:
    if var in heap:
        raise ValueError(f"{var} already in heap; cannot re-declare variable")

    vt: str | tuple[str, ...] = var.type
    type_symbol: Symbol | CompositeSymbol

    match vt:
        case str():
            type_symbol = Symbol(vt)

        case tuple():
            type_symbol = CompositeSymbol(vt)

        case _:
            raise ValueError(f"var type {vt} is not valid ({type(vt)})")

    var_type = types_table.get(type_symbol, None) or builtins_types.get(type_symbol, None)

    match var_type:
        case None:
            raise ValueError(
                f"var type {var_type} not found on available custom and built-in types"
            )

        case BaseTypeDataStructure():
            variable = VariableTemplate(
                var_name=var,
                type_name=type_symbol,
                type_ds=var_type.ds,
                # TODO: use the modifier to define variable flag and define a default
                flag=VariableKind.MUTABLE
            )

            match variable:
                case BaseDataContainer():
                    return variable

                case _:
                    raise ValueError(f"{variable}")

        case _:
            raise NotImplementedError(
                f"{var_type} ({type(var_type)}) not implemented yet for variable declaration"
            )


def _get_assign_datatype(
    var_type: Symbol | CompositeSymbol,
    value: WorkingData | CompositeWorkingData | IRInstr | IRBlock,
    heap: Heap,
    types_table: IRTypes,
) -> Symbol | CoreLiteral | IRInstr | IRBlock:
    match value:
        case Symbol():
            res_var = heap.get(value)

            match res_var:
                case HeapInvalidKeyError():
                    raise ValueError(f"variable {value} is not declared yet")

                case _:
                    if res_var.type == var_type:
                        return value

        case CompositeSymbol():
            raise NotImplementedError(
                "composite symbol on variable assignment not implemented yet"
            )

        case CoreLiteral():
            data_type = Symbol(value.type)
            data_type = compatible_types.get(data_type) or data_type

            if var_type == data_type:
                dt_ds = builtins_types.get(data_type)

                if dt_ds:
                    types_table.add(data_type, dt_ds)

                else:
                    raise ValueError(f"invalid type {data_type}")

                return CoreLiteral(value.value, data_type.value)

        case CompositeLiteral():
            raise NotImplementedError(
                "composite literal on variable assignment not implemente yet"
            )

        case IRInstr():
            new_instrs = ()

            for k in value:
                new_instrs += _get_assign_datatype(var_type, k, heap, types_table),

            return value.__class__(*new_instrs, name=value.name)

        case BodyBlock() | ArgsBlock() | ArgsValuesBlock() | OptionBlock():
            new_blocks = ()

            for k in value:
                new_blocks += _get_assign_datatype(var_type, k, heap, types_table),

            return value.__class__(*new_blocks)

        case _:
            raise NotImplementedError(
                f"{value} ({type(value)}) on variable assignment with undefined implementation"
            )

    raise ValueError(
        f"data {value} to be assigned is not compatible with target type {var_type}"
    )


def _assign_variable(*args: Any, variable: BaseDataContainer, **arg_values: Any) -> None:
    if len(args) > 0 and len(arg_values) == 0:
        variable(*args)

    elif len(args) == 0 and len(arg_values) > 0:
        variable(**arg_values)

    else:
        raise NotImplementedError(
            f"should not have arguments and argument-value together when "
            f"assigning variable {variable}"
        )
