from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Iterable

from hhat_lang.core.data.core import WorkingData, CompositeWorkingData


class BaseIRFlag(Enum):
    """
    Base for IR flag classes. It should be used to create enums for instructions,
    such as ``CALL``, ``DECLARE``, ``ASSIGN``, ``RETURN``, etc.
    """


class BaseIRBlockFlag(Enum):
    """
    Base for IR block flag classes. Should be used to define types of IR blocks.
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
        ...

    @abstractmethod
    def __repr__(self) -> str:
        ...


class BaseIRBlock(ABC):
    """
    Base for IR block classes.
    """

    _name: BaseIRBlockFlag
    args: tuple

    @property
    def name(self) -> BaseIRBlockFlag:
        return self._name

    def __iter__(self) -> Iterable:
        yield from self.args

    @abstractmethod
    def __repr__(self) -> str:
        ...


class BaseIR(ABC):
    pass
