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

    @abstractmethod
    def add(self, block: Any) -> None:
        raise NotImplementedError()

    def __iter__(self) -> Iterable:
        yield from self.args

    @abstractmethod
    def __repr__(self) -> str:
        raise NotImplementedError()


class BaseIRBlockFlag(Enum):
    """
    Base for IR block flag classes. Should be used to define types of IR blocks.
    """
