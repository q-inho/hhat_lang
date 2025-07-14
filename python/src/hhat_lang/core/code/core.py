from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Iterable

from hhat_lang.core.code.new_ir import BaseIRBlock
from hhat_lang.core.data.core import WorkingData, CompositeWorkingData
from hhat_lang.core.memory.core import TypeTable, FnTable


class BaseIR(ABC):
    main: BaseIRBlock | None
    types: TypeTable | None
    fns: FnTable | None

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

    def __iter__(self) -> Iterable:
        yield from self.args

    @abstractmethod
    def resolve(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError()
