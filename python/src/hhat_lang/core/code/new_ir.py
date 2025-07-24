from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Iterable


class BaseIRBlock(ABC):
    """
    Base for IR block classes.
    """

    _name: BaseIRBlockFlag
    args: tuple

    @property
    def name(self) -> BaseIRBlockFlag:
        return self._name

    def __hash__(self) -> int:
        return hash((self._name, self.args))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BaseIRBlock):
            return hash(self) == hash(other)

        return False

    def __iter__(self) -> Iterable:
        yield from self.args

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError()


class BaseIRBlockFlag(Enum):
    """
    Base for IR block flag classes. Should be used to define types of IR blocks.
    """
