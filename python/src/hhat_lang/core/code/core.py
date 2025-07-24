from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Iterable

from hhat_lang.core.code.new_ir import BaseIRBlock
from hhat_lang.core.data.core import WorkingData, CompositeWorkingData
from hhat_lang.core.code.symbol_table import SymbolTable, RefTable


class BaseIR(ABC):
    """
    Base class for the IR.

    IR holds information about the main code execution (as an IR block), or a symbol
    table containing type definitions or function definitions, and a reference table
    to point the definitions of types or functions from other IRs.
    """

    _ref_table: RefTable
    _symbol_table: SymbolTable | None
    _main: BaseIRBlock | None

    @property
    def main(self) -> BaseIRBlock | None:
        return self._main

    @property
    def symbol_table(self) -> SymbolTable | None:
        return self._symbol_table

    @property
    def ref_table(self) -> RefTable:
        return self._ref_table

    def __hash__(self) -> int:
        return hash(hash(self._symbol_table) + hash(self._main))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BaseIR):
            return hash(self) == hash(other)

        return False

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError()


class BaseIRFlag(Enum):
    """
    Base for IR flag classes. It should be used to create enums for instructions,
    such as ``CALL``, ``DECLARE``, ``ASSIGN``, ``RETURN``, etc.
    """


class BaseIRInstr(ABC):
    """
    Base IR instruction classes.
    """

    _name: BaseIRFlag
    args: tuple[BaseIR | WorkingData | CompositeWorkingData, ...] | tuple

    @property
    def name(self) -> Any:
        return self._name

    @abstractmethod
    def resolve(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    def __hash__(self) -> int:
        return hash((self.name, self.args))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BaseIRInstr):
            return hash(self) == hash(other)

        return False

    def __iter__(self) -> Iterable:
        yield from self.args

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError()
