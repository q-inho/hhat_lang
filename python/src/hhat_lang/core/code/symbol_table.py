from __future__ import annotations

from collections import OrderedDict
from typing import Any, Iterable

from hhat_lang.core.code.ir_graph import IRKey
from hhat_lang.core.data.core import Symbol, CompositeSymbol
from hhat_lang.core.data.fn_def import BaseFnKey, BaseFnCheck, FnDef
from hhat_lang.core.types.abstract_base import BaseTypeDataStructure


class TypeTable:
    _table: OrderedDict[Symbol | CompositeSymbol, BaseTypeDataStructure]

    def __init__(self):
        self._table = OrderedDict()

    @property
    def table(self) -> OrderedDict[Symbol | CompositeSymbol, BaseTypeDataStructure]:
        return self._table

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

    def __hash__(self) -> int:
        return hash(self.table)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TypeTable):
            return hash(self) == hash(other)

        return False

    def __contains__(self, item: Symbol | CompositeSymbol) -> bool:
        return item in self.table

    def __len__(self) -> int:
        return len(self.table)

    def __iter__(self) -> Iterable:
        yield from self.table.items()

    def __repr__(self) -> str:
        content = "\n      ".join(f"{v}" for v in self.table.values())
        return f"\n  types:\n      {content}\n"


class FnTable:
    """
        This class holds functions definitions as ``BaseFnKey`` for function
        entry (function name, type and arguments) and its body (content).

        Together with ``IRTypes`` and ``IR`` it provides the base for an IR object
        picturing the full code.
        """

    _table: OrderedDict[Symbol | CompositeSymbol, dict[BaseFnKey | BaseFnCheck, FnDef]]

    def __init__(self):
        self._table = OrderedDict()

    @property
    def table(self) -> OrderedDict[Symbol | CompositeSymbol, dict[BaseFnKey | BaseFnCheck, FnDef]]:
        return self._table

    def add(self, fn_entry: BaseFnCheck, data: FnDef) -> None:
        if isinstance(data, FnDef):
            if isinstance(fn_entry, BaseFnCheck):
                if fn_entry.name in self.table:
                    self.table[fn_entry.name].update({fn_entry: data})

                else:
                    self.table[fn_entry.name] = {fn_entry: data}

            elif isinstance(fn_entry, BaseFnKey):
                new_fn_entry = BaseFnCheck(fn_name=fn_entry.name, args_types=fn_entry.args_types)
                if fn_entry.name in self.table:
                    self.table[fn_entry.name].update({new_fn_entry: data})

                else:
                    self.table[fn_entry.name] = {new_fn_entry: data}

            else:
                raise ValueError(f"fn_entry is of wrong type ({type(fn_entry)})")

    def get(
        self,
        fn_entry: Symbol | CompositeSymbol | BaseFnCheck,
        default: Any | None = None
    ) -> FnDef | dict[BaseFnCheck, FnDef] | None:
        match fn_entry:
            case Symbol() | CompositeSymbol():
                return self.table.get(fn_entry, default)

            case BaseFnCheck():
                if fn_entry.name in self.table:
                    return self.table[fn_entry.name].get(fn_entry, default)

        raise ValueError(f"cannot retrieve fn {fn_entry}")

    def __hash__(self) -> int:
        return hash(self.table)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, FnTable):
            return hash(self) == hash(other)

        return False

    def __len__(self) -> int:
        return sum(len(k) for k in self.table.values())

    def __iter__(self) -> Iterable:
        for v in self.table.values():
            for p, q in v.items():
                yield p, q

    def __repr__(self) -> str:
        content = "\n      ".join(
            f"{k}:\n         {v}" for h in self.table.values() for k, v in h.items()
        )
        return f"\n  fns:\n      {content}\n"


class SymbolTable:
    """To store types and functions"""

    _types: TypeTable
    _fns: FnTable

    def __init__(self):
        self._types = TypeTable()
        self._fns = FnTable()

    @property
    def type(self) -> TypeTable:
        return self._types

    @property
    def fn(self) -> FnTable:
        return self._fns

    def __hash__(self) -> int:
        return hash((self._types, self._fns))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, SymbolTable):
            return hash(self) == hash(other)

        return False


#####################
# REFERENCE CLASSES #
#####################

class RefTypeTable:
    """Reference to types from another IR"""

    _table: dict[Symbol | CompositeSymbol, IRKey]

    def __init__(self):
        self._table = dict()

    def add_ref(
        self,
        type_name: Symbol | CompositeSymbol,
        ir_ref: IRKey
    ) -> None:
        if (
            isinstance(type_name, Symbol | CompositeSymbol)
            and isinstance(ir_ref, IRKey)
        ):
            self._table[type_name] = ir_ref

        else:
            raise ValueError(f"wrong reference type table input ({type_name})")

    def get_irkey(self, type_name: Symbol | CompositeSymbol) -> IRKey:
        return self._table[type_name]

    def __hash__(self) -> int:
        return hash(self._table)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, RefTypeTable):
            return hash(self) == hash(other)

        return False


class RefFnTable:
    """Reference to functions from another IR"""

    _table: dict[BaseFnKey, IRKey]

    def __init__(self):
        self._table = dict()

    def add_ref(self, fn_name: BaseFnKey, ir_ref: IRKey) -> None:
        if (
            isinstance(fn_name, BaseFnKey)
            and isinstance(ir_ref, IRKey)
        ):
            self._table[fn_name] = ir_ref

        else:
            raise ValueError(f"wrong reference type table input ({fn_name})")

    def get_irkey(self, fn_name: BaseFnKey) -> IRKey:
        return self._table[fn_name]

    def __hash__(self) -> int:
        return hash(self._table)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, RefFnTable):
            return hash(self) == hash(other)

        return False


class RefTable:
    """To store reference for types and functions from another IR"""

    _types: RefTypeTable
    _fns: RefFnTable

    def __init__(self):
        self._types = RefTypeTable()
        self._fns = RefFnTable()

    @property
    def types(self) -> RefTypeTable:
        return self._types

    @property
    def fns(self) -> RefFnTable:
        return self._fns

    def __hash__(self) -> int:
        return hash(hash(self._types) + hash(self._fns))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, RefTable):
            return hash(self) == hash(other)

        return False
