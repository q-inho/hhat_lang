from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections import deque, OrderedDict
from queue import LifoQueue
from typing import Any, Hashable
from uuid import UUID

from hhat_lang.core.code.ir import BlockIR
from hhat_lang.core.data.core import (
    CompositeLiteral,
    CompositeMixData,
    CoreLiteral,
    Symbol,
    WorkingData, CompositeWorkingData,
)
from hhat_lang.core.data.fn_def import BaseFnKey, BaseFnCheck
from hhat_lang.core.data.variable import BaseDataContainer
from hhat_lang.core.error_handlers.errors import (
    ErrorHandler,
    HeapInvalidKeyError,
    IndexAllocationError,
    IndexInvalidVarError,
    IndexUnknownError,
    IndexVarHasIndexesError,
    SymbolTableInvalidKeyError,
)
from hhat_lang.core.types.abstract_base import BaseTypeDataStructure


class PIDManager:
    """
    Manages the PID for H-hat language, including all the dialects.
    """

    def new(self) -> UUID:
        raise NotImplementedError()

    def list(self) -> list[UUID]:
        raise NotImplementedError()


class IndexManager:
    """
    Holds and manages information about the indexes (qubits) availability and allocation.

    Properties
        - `max_number`: maximum number of allowed indexes
        - `available`: deque with all the available indexes
        - `allocated`: deque with all the allocated indexes
        - `in_use_by`: dictionary containing the allocator variable as key and
        deque with allocated indexes as value

    Methods
        - `request`: given a variable (`Symbol`) and the number of indexes (`int`),
        allocate the number if it has enough space
        - `free`: given a variable (`Symbol`), free all the allocated indexes
    """

    _max_num_index: int
    _num_allocated: int
    _available: deque
    _allocated: deque
    _resources: dict[WorkingData, int]
    _in_use_by: dict[WorkingData, deque]

    def __init__(self, max_num_index: int):
        self._max_num_index = max_num_index
        self._num_allocated = 0
        self._available = deque(
            iterable=tuple(k for k in range(0, self._max_num_index)),
            maxlen=self._max_num_index,
        )
        self._allocated = deque(maxlen=self._max_num_index)
        self._resources = dict()
        self._in_use_by = dict()

    @property
    def max_number(self) -> int:
        return self._max_num_index

    @property
    def available(self) -> deque:
        return self._available

    @property
    def allocated(self) -> deque:
        return self._allocated

    @property
    def resources(self) -> dict[WorkingData, int]:
        """
        Dictionary containing the variable(s)/literal(s) and
        the index amount requested.
        """

        return self._resources

    @property
    def in_use_by(self) -> dict[WorkingData, deque]:
        """
        Dictionary containing the variable(s)/literal(s) with
        the deque of indexes provided.
        """

        return self._in_use_by

    def __getitem__(self, item: WorkingData) -> deque | IndexInvalidVarError:
        """Return the deque of indexes from a quantum data."""

        if res := self._in_use_by.get(item, False):
            return res

        return IndexInvalidVarError(var_name=item)

    def __contains__(self, item: WorkingData) -> bool:
        """Checks whether there is item in the IndexManager."""

        return item in self._in_use_by

    def _alloc_idxs(self, num_idxs: int) -> deque | IndexAllocationError:
        available = self._max_num_index - self._num_allocated

        if available >= num_idxs:
            _data: tuple = tuple()

            for _ in range(0, num_idxs):
                _data += (self._available.popleft(),)
                self._num_allocated += 1

            return deque(
                iterable=_data,
                maxlen=num_idxs,
            )

        return IndexAllocationError(requested_idxs=num_idxs, max_idxs=available)

    def _alloc_var(self, var_name: WorkingData, idxs_deque: deque) -> None:
        self._in_use_by[var_name] = idxs_deque
        self._allocated.extend(idxs_deque)

    def _has_var(self, var_name: WorkingData) -> bool:
        return var_name in self._resources

    def _free_var(self, var_name: WorkingData) -> deque:
        """
        Free variable's indexes and allocated deque with those indexes.
        """

        idxs = self._in_use_by.pop(var_name)

        for k in idxs:
            self._allocated.remove(k)

        return idxs

    def add(self, var_name: WorkingData, num_idxs: int) -> None | ErrorHandler:
        """
        Add a variable/literal with a given number of indexes required for it.
        The amount will be used upon request through the `request` method.
        """

        if (self._num_allocated + num_idxs) <= self._max_num_index:
            if var_name not in self._resources:
                self._resources[var_name] = num_idxs
                return None

            return IndexVarHasIndexesError(var_name)

        return IndexAllocationError(
            requested_idxs=num_idxs, max_idxs=self._num_allocated
        )

    def request(self, var_name: WorkingData) -> deque | ErrorHandler:
        """
        Request a number of indexes given by the `resources` property for
        a variable `var_name`.
        """

        if not (num_idxs := self._resources.get(var_name, False)):
            return IndexInvalidVarError(var_name)

        match x := self._alloc_idxs(num_idxs):
            case deque():
                if not self._has_var(var_name):
                    return IndexInvalidVarError(var_name=var_name)

                self._alloc_var(var_name, x)
                return x

            case IndexAllocationError():
                return x

        return IndexUnknownError()

    def free(self, var_name: WorkingData) -> None:
        """
        Free indexes from a given variable `var_name`.
        """

        idxs = self._free_var(var_name)
        self._available.extend(idxs)
        self._num_allocated -= len(idxs)


#########################
# DATA STORAGE MANAGERS #
#########################


class BaseStack(ABC):
    _data: LifoQueue

    @abstractmethod
    def push(self, data: MemoryDataTypes) -> None:
        pass

    @abstractmethod
    def pop(self) -> MemoryDataTypes:
        pass

    @abstractmethod
    def peek(self) -> MemoryDataTypes:
        pass


class Stack(BaseStack):
    def __init__(self):
        self._data = LifoQueue()

    def push(self, data: MemoryDataTypes) -> None:
        """Push ``data`` into stack as its new last item"""

        self._data.put(data)

    def pop(self) -> MemoryDataTypes:
        """Pop last item from stack"""

        return self._data.get()

    def peek(self) -> MemoryDataTypes:
        """Expensive method to 'peek' the last item from the stack."""

        last_item = self._data.get()
        self._data.put(last_item)
        return last_item


class BaseHeap(ABC):
    # TODO: modify if to account for scope heap

    _data: dict[Symbol, BaseDataContainer]

    @abstractmethod
    def set(self, key: Symbol, value: BaseDataContainer) -> None:
        pass

    @abstractmethod
    def get(self, key: Symbol) -> BaseDataContainer:
        pass

    def __getitem__(self, item: Symbol) -> BaseDataContainer:
        return self.get(item)


class Heap(BaseHeap):
    # TODO: it must be used for scopes

    def __init__(self):
        self._data = dict()

    def set(self, key: Symbol, value: BaseDataContainer) -> None | HeapInvalidKeyError:
        if not (isinstance(key, Symbol) and isinstance(value, BaseDataContainer)):
            return HeapInvalidKeyError(key=key)

        self._data[key] = value
        return None

    def get(
        self,
        key: Symbol
    ) -> BaseDataContainer | WorkingData | CompositeWorkingData | HeapInvalidKeyError:
        """
        Given a key, returns its data which can be a variable container (variable content),
        a working data (symbol, literal) or composite working data.
        """

        if not (var_data := self._data.get(key, None)):
            return HeapInvalidKeyError(key=key)

        return var_data  # type: ignore [return-value]

    def free(self, key: Symbol) -> HeapInvalidKeyError | None:
        """
        To free a given key from the heap. It must be called every time the heap goes out of scope
        """

        if not self._data.pop(key, False):
            return HeapInvalidKeyError(key=key)

        return None

    def __contains__(self, item: Symbol) -> bool:
        return item in self._data


class ScopeValue:
    """Holds a value for scopes"""

    _value: int

    def __init__(self, obj: Hashable, *, counter: int):
        """
       Hold a value for scope.

        Args:
            obj: object must be hashable
            counter: from the interpreter counter, to keep track of scope nesting
        """

        self._value = hash(hash(obj) + counter)

    @property
    def value(self) -> int:
        return self._value

    def __hash__(self) -> int:
        return self._value

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ScopeValue):
            return self._value == other._value

        if isinstance(other, int):
            return self._value == other

        return False

    def __repr__(self) -> str:
        return f"S#{self._value}"


class Scope:
    """Defines a scope for stack and heap memory allocation"""

    _stack: OrderedDict[ScopeValue, Stack]
    _heap: dict[ScopeValue, Heap]

    def __init__(self):
        self._stack = OrderedDict()
        self._heap = dict()

    @property
    def stack(self) -> OrderedDict[ScopeValue, Stack]:
        return self._stack

    @property
    def heap(self) -> dict[ScopeValue, Heap]:
        return self._heap

    def new(self, scope: ScopeValue) -> Any:
        """Define a new scope"""
        if isinstance(scope, ScopeValue):
            self._stack[scope] = Stack()
            self._heap[scope] = Heap()

        else:
            # TODO: maybe create a error handler for it?
            raise ValueError(f"value scope must be ScopeValue, got {type(scope)}")

    def free(self, scope: ScopeValue, to_return: bool = False) -> Any:
        """
        Free scope data, i.e. stack and heap memory. Must be called every time
        the scope is finished.
        """

        # if the scope is a function that is returning some value, the last value from stack
        # will be popped out to be consumed by another scope
        if to_return:
            # for now, trying to place item into the last stack scope; if that works, keep as is
            cur_stack_item = self._stack[scope].pop()
            last_scope, last_stack = self._stack.popitem()
            last_stack.push(cur_stack_item)
            self._stack[last_scope] = last_stack
            return None

        self._stack[scope].pop()
        return None


class SymbolTable:
    """To store types and functions"""

    _types: dict[WorkingData, BaseTypeDataStructure]
    _fns: dict[BaseFnKey, BlockIR]

    def __init__(self):
        self._types = dict()
        self._fns = dict()

    def add_type(self, item: WorkingData, type_def: BaseTypeDataStructure) -> None:
        if item not in self._types and isinstance(type_def, BaseTypeDataStructure):
            self._types[item] = type_def

    def add_fn(self, fn: BaseFnKey, fn_def: BlockIR) -> None:
        if fn not in self._fns:  # and isinstance(fn_def, BlockIR):
            self._fns[fn] = fn_def

    def get_type(self, item: WorkingData) -> BaseTypeDataStructure | SymbolTableInvalidKeyError:
        if item in self._types:
            return self._types[item]

        return SymbolTableInvalidKeyError(item, SymbolTableInvalidKeyError.Type())

    def get_fn(self, item: BaseFnCheck) -> BlockIR | SymbolTableInvalidKeyError:
        if item in self._fns:
            return self._fns[item]

        return SymbolTableInvalidKeyError(item, SymbolTableInvalidKeyError.Fn())


########################
# MEMORY MANAGER CLASS #
########################


class BaseMemoryManager(ABC):
    _idx: IndexManager
    _stack: BaseStack
    _heap: BaseHeap
    _pid: PIDManager
    _symbol: SymbolTable

    @property
    def idx(self) -> IndexManager:
        return self._idx

    @property
    def stack(self) -> BaseStack:
        return self._stack

    @property
    def heap(self) -> BaseHeap:
        return self._heap

    @property
    def symbol(self) -> SymbolTable:
        return self._symbol

    @property
    def pid(self) -> PIDManager:
        return self._pid


class MemoryManager(BaseMemoryManager):
    """Manages the stack, heap, symbol table, pid, and index."""

    def __init__(self, max_num_index: int):
        self._stack = Stack()
        self._heap = Heap()
        self._symbol = SymbolTable()
        self._pid = PIDManager()
        self._idx = IndexManager(max_num_index)


MemoryDataTypes = (
    BaseDataContainer | CoreLiteral | CompositeLiteral | Symbol | CompositeMixData
)
"""
- BaseDataContainer
- CoreLiteral
- CompositeLiteral
- Symbol
- CompositeMixData
"""
