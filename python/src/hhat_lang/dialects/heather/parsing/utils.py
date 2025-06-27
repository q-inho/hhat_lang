from __future__ import annotations

from collections.abc import Mapping
from typing import Iterable, Iterator

from hhat_lang.core.data.core import CompositeSymbol
from hhat_lang.core.data.fn_def import BaseFnKey
from hhat_lang.core.types.abstract_base import BaseTypeDataStructure
from hhat_lang.dialects.heather.code.simple_ir_builder.ir import IRBlock


class ImportDicts:
    def __init__(self, types: TypesDict, fns: FnsDict):
        if isinstance(types, TypesDict) and isinstance(fns, FnsDict):
            self.types = types
            self.fns = fns


class TypesDict(Mapping):
    """
    A special dict-like class that holds types definitions, with key as
    ``CompositeSymbol`` and value as ``BaseTypeDataStructure`` object.
    """

    _data: dict[CompositeSymbol, BaseTypeDataStructure]

    def __init__(self, data: dict | None = None):
        self._data = data if isinstance(data, dict) else dict()

    def __setitem__(self, key: CompositeSymbol, value: BaseTypeDataStructure) -> None:
        if isinstance(key, CompositeSymbol) and isinstance(value, BaseTypeDataStructure):
            self._data[key] = value

        else:
            raise ValueError(f"{key} ({type(key)}) is not valid key for types")

    def __getitem__(self, key: CompositeSymbol, /) -> BaseTypeDataStructure:
        if isinstance(key, CompositeSymbol):
            return self._data[key]

        raise KeyError(key)

    def __len__(self) -> int:
        return len(self._data)

    def items(self) -> Iterator:
        yield from self._data.items()

    def keys(self) -> Iterator:
        yield from self._data.keys()

    def values(self) -> Iterator:
        yield from self._data.values()

    def __iter__(self) -> Iterable:
        yield from self._data.keys()

    def __repr__(self) -> str:
        return str(self._data)


class FnsDict(Mapping):
    """
    A special dict-like class that holds functions definitions, with key
    as ``BaseFnKey`` and value as ``IRBlock`` object.
    """

    _data: dict[BaseFnKey, IRBlock]

    def __init__(self, data: dict | None = None):
        self._data = data if isinstance(data, dict) else dict()

    def __setitem__(self, key: BaseFnKey, value: IRBlock) -> None:
        if isinstance(key, BaseFnKey) and isinstance(value, IRBlock):
            self._data[key] = value

        else:
            raise ValueError(f"{key} ({type(key)}) is not valid key for types")

    def __getitem__(self, key: BaseFnKey, /) -> IRBlock:
        if isinstance(key, BaseFnKey):
            return self._data[key]

        raise KeyError(key)

    def __len__(self) -> int:
        return len(self._data)

    def items(self) -> Iterator:
        yield from self._data.items()

    def keys(self) -> Iterator:
        yield from self._data.keys()

    def values(self) -> Iterator:
        yield from self._data.values()

    def __iter__(self) -> Iterable:
        yield from self._data.keys()

    def __repr__(self) -> str:
        return str(self._data)


