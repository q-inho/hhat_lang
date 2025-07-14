from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from hhat_lang.core.memory.core import MemoryManager


class BaseInterpreter(ABC):
    """
    An abstract interpreter class. The interpreter class must hold basic interpreter
    attributes and functionalities, such as parsing and evaluating code.

    Each interpreter object holds information regarding available quantum devices specs,
    quantum target backend and its quantum language as well as their specs, and the H-hat
    dialect specs to parse the code and to evaluate it.
    """

    _depth_counter: int
    """to count code depth, for memory and scope management; it must be >= 0"""

    @property
    def depth_counter(self) -> int:
        """
        To count code depth, especially on recursive function calls.

        Returns:
            The current integer of the depth counter
        """

        return self._depth_counter

    def inc_depth_counter(self) -> None:
        self._depth_counter += 1

    def dec_depth_counter(self) -> None:
        self._depth_counter -= 1
        if self._depth_counter < 0:
            raise ValueError("interpreter depth counter is < 0")

    @abstractmethod
    def parse(self, *args: Any, code: str, **kwargs: Any) -> Any:
        """
        Parsing the source code to some intermediate representation,
        e.g. AST, IR, etc.
        """

        raise NotImplementedError()

    @abstractmethod
    def evaluate(self, *args: Any, **kwargs: Any) -> Any:
        """
        Evaluates the code using the evaluator instance defined by the
        interpreter specs.
        """

        raise NotImplementedError()


class BaseEvaluator(ABC):
    """
    An abstract evaluator class.
    """

    @abstractmethod
    def run(self, *, code: Any, mem: MemoryManager, **kwargs: Any) -> Any:
        """To run only once, when calling the evaluator to execute the code."""

        raise NotImplementedError()

    @abstractmethod
    def walk(self, code: Any, mem: MemoryManager, **kwargs: Any) -> Any:
        """
        To run recursively and evaluate the code. Should not be called directly be
        the user, but rather through `run` and internal methods.
        """

        raise NotImplementedError()

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any):
        raise NotImplementedError()
