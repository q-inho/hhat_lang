from __future__ import annotations

from typing import Any, Iterable

from hhat_lang.core.data.core import Symbol, CompositeSymbol


class BaseFnKey:
    """
    Base class for functions definition on memory's SymbolTable.
    Provide functions a signature.

    Given a function:

    ```
    fn sum (a:u64 b:u64) u64 { ::add(a b) }
    ```

    The function key object is as follows:

    ```
    BaseFnKey(
        name=Symbol("sum"),
        type=Symbol("u64"),
        args_names=(Symbol("a"), Symbol("b"),),
        args_types=(Symbol("u64"), Symbol("u64"),)
    )
    ```

    When trying to retrieve the function data, use `BaseFnCheck`
    parent instance instead:


    """

    _name: Symbol
    _type: Symbol | CompositeSymbol
    _args_types: tuple | tuple[Symbol | CompositeSymbol, ...]
    _args_names: tuple | tuple[Symbol, ...]

    # TODO: implement code for comparison of out of order args_names

    def __init__(
        self,
        fn_name: Symbol,
        fn_type: Symbol | CompositeSymbol,
        args_names: tuple | tuple[Symbol, ...],
        args_types: tuple | tuple[Symbol | CompositeSymbol, ...],
    ):

        # check correct types for each argument before proceeding
        assert (
            isinstance(fn_name, Symbol)
            and isinstance(fn_type, Symbol | CompositeSymbol)
            and all(isinstance(k, Symbol) for k in args_names)
            and all(isinstance(p, Symbol | CompositeSymbol) for p in args_types),
            f"Wrong types provided for function definition on SymbolTable:\n"
            f"  name: {fn_name}\n  type: {fn_type}\n  args types: {args_types}\n"
            f"  args names: {args_names}\n",
        )

        self._name = fn_name
        self._type = fn_type
        self._args_names = args_names
        self._args_types = args_types

    @property
    def name(self) -> Symbol:
        return self._name

    @property
    def type(self) -> Symbol | CompositeSymbol:
        return self._type

    @property
    def args_types(self) -> tuple | tuple[Symbol | CompositeSymbol, ...]:
        return self._args_types

    @property
    def args_names(self) -> tuple | tuple[Symbol, ...]:
        return self._args_names

    def __hash__(self) -> int:
        return hash((self._name, self._type, self._args_types))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BaseFnKey | BaseFnCheck):
            return (
                self._name == other._name
                and self._type == other._type
                and self._args_types == other._args_types
            )

        return False

    def has_args(self, args: tuple[Symbol, ...]) -> bool:
        return set(self._args_names) == set(args)

    def __iter__(self) -> Iterable:
        yield from zip(self.args_names, self.args_types)

    def __repr__(self) -> str:
        return (
            f"{self.name}:{self.type}("
            f"{' '.join(f'{k}:{v}' for k, v in zip(self.args_names, self.args_types))})"
        )


class BaseFnCheck:
    """
    Base function class to check and retrieve a given function from the SymbolTable.
    """

    _name: Symbol
    _type: Symbol | CompositeSymbol
    _args_types: tuple | tuple[Symbol | CompositeSymbol, ...]
    _args_names: tuple | tuple[Symbol, ...]

    def __init__(
        self,
        fn_name: Symbol,
        fn_type: Symbol | CompositeSymbol,
        args_types: tuple | tuple[Symbol | CompositeSymbol, ...],
    ):

        # checks types correctness
        assert (
            isinstance(fn_name, Symbol)
            and isinstance(fn_type, Symbol | CompositeSymbol)
            and all(isinstance(p, Symbol | CompositeSymbol) for p in args_types),
            f"Wrong types provided for function retrieval on SymbolTable:\n"
            f"  name: {fn_name}\n  type: {fn_type}\n  args types: {args_types}\n",
        )

        self._name = fn_name
        self._type = fn_type
        self._args_types = args_types

    def __hash__(self) -> int:
        return hash((self._name, self._type, self._args_types))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BaseFnKey | BaseFnCheck):
            return (
                self._name == other._name
                and self._type == other._type
                and self._args_types == other._args_types
            )

        return False
