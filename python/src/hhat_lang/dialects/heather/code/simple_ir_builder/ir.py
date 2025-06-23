"""
Define the classes to handle ``IR`` structure, from instructions, instructions
blocks, to the ``IR`` holder.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from enum import Enum, auto
from typing import Any, Iterable

from hhat_lang.core.data.core import Symbol, WorkingData, CompositeSymbol


# FIXME: quick fix for now, before the new IR is ready
class FnIR(): pass
class IRInstr(): pass


class IRFlag(Enum):
    """
    Used to identify the ``IRBaseInstr`` child class purpose. Ex: a ``CallInstr``
    class is defined with its name as ``IRFlag.CALL``.
    """

    NULL = auto()
    CALL = auto()
    CAST = auto()
    ASSIGN = auto()
    DECLARE = auto()
    DECLARE_ASSIGN = auto()
    ARGS = auto()
    OPTION = auto()
    COND = auto()
    MATCH = auto()
    CALL_WITH_BODY = auto()
    CALL_WITH_OPTION = auto()
    RETURN = auto()


class BlockRef:
    """
    Define a block reference to be used by the ``IR`` object on lookups for existing
    or new blocks.
    """

    name: str

    def __init__(self, *instrs: Any):
        self.name = str(hash(instrs))

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BlockRef | IRBlock):
            return self.name == other.name

        if isinstance(other, str):
            return self.name == other

        return False

    def __repr__(self) -> str:
        return f"#{self.name[-8:]}"


class IRBlock:
    """
    It contains a tuple with instructions (``IRBaseInstr`` child classes) and
    block references (``BlockRef``). Use it to aggregate multiple instructions or
    references.
    """

    instrs: tuple | tuple[IRBaseInstr | BlockRef, ...]
    name: BlockRef

    def __init__(self, *instrs: IRBaseInstr | BlockRef):
        self.instrs = instrs
        self.name = BlockRef(*instrs)

    @classmethod
    def gen_block(cls, *instrs: IRBaseInstr | IRBlock) -> tuple[BlockRef, IRBlock]:
        """Generate a new block, returning new block's name (BlockRef) and new block's object"""

        new_block = IRBlock(*instrs)
        return new_block.name, new_block

    def add_instrs(self, *instrs: IRBaseInstr | IRBlock) -> None:
        self.instrs += instrs

    def __hash__(self) -> int:
        return hash((self.name, self.instrs))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, IRBlock):
            return self.instrs == other.instrs and self.name == other.name

        return False

    def __len__(self) -> int:
        return len(self.instrs)

    def __iter__(self) -> Iterable:
        yield from self.instrs

    def __repr__(self) -> str:
        content = ""
        total_instrs = len(str(len(self)))

        for n, k in enumerate(self.instrs):
            content += f"\n      {'0' * (total_instrs - len(str(n)) + 1) + str(n+1)} {k}"

        return f"      block:{content}\n"


##############################
# IR INSTRUCTION DEFINITIONS #
##############################

class IRBaseInstr(ABC):
    """
    Abstract class to create instructions. It must contain a name (str or
    ``IRFlag`` attribute), and arguments that may vary according to child
    instruction. A block reference dictionary is created to hold every new
    block creation, so the IR can account for it later.
    """

    INSTR: IRFlag
    name: str
    args: tuple | tuple[WorkingData | BlockRef | IRBaseInstr, ...]
    block_refs: dict | dict[BlockRef, IRBlock]

    def __init__(
        self,
        *args: WorkingData | IRBlock | BlockRef | IRBaseInstr,
        name: str | IRFlag
    ):
        self.name = name.name if isinstance(name, IRFlag) else name
        self.args = ()
        self.block_refs = dict()

        for k in args:
            self.add(k)

    @property
    def instr(self) -> IRFlag:
        return self.INSTR

    @property
    def get_refs(self) -> dict[BlockRef, IRBlock]:
        return deepcopy(self.block_refs)

    def add(self, data: WorkingData | IRBlock | BlockRef | IRBaseInstr) -> None:
        match data:
            case WorkingData() | BlockRef():
                self.args += data,

            case IRBaseInstr():
                ref, block = IRBlock.gen_block(data)
                self.block_refs[ref] = block
                self.args += ref,

            case IRBlock():
                self.args += data.name,

                if data.name not in self.block_refs:
                    self.block_refs[data.name] = data

            case _:
                raise ValueError(
                    f"something went wrong when adding IR instruction for {data} ({type(data)})"
                )

    def __hash__(self) -> int:
        return hash((self.name, self.args))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, IRBaseInstr):
            return self.args == other.args and self.name == other.name

        return False

    def __iter__(self) -> Iterable:
        yield from self.args

    def __repr__(self):
        content = ", ".join(str(k) for k in self)
        return f"{self.name}({content})"

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class IRArgs(IRBaseInstr):
    INSTR = IRFlag.ARGS

    def __init__(self, *args: WorkingData | IRBlock | BlockRef):
        super().__init__(*args, name=IRFlag.ARGS)

    def __call__(self, *args, **kwargs):
        pass


class IRCall(IRBaseInstr):
    INSTR = IRFlag.CALL

    def __init__(
        self,
        caller: Symbol | CompositeSymbol,
        args: IRArgs,
    ):
        super().__init__(caller, args, name=IRFlag.CALL)

    def __call__(self, *args, **kwargs):
        pass


class IRCast(IRBaseInstr):
    INSTR = IRFlag.CAST

    def __init__(
        self,
        cast_data: WorkingData | IRBlock | BlockRef,
        to_type: Symbol | CompositeSymbol
    ):
        super().__init__(cast_data, to_type, name=IRFlag.CAST)

    def __call__(self, *args, **kwargs):
        pass


class IRAssign(IRBaseInstr):
    INSTR = IRFlag.ASSIGN

    def __init__(self, var: Symbol, value: WorkingData | IRBlock | BlockRef):
        super().__init__(var, value, name=IRFlag.ASSIGN)

    def __call__(self, *args, **kwargs):
        pass


class IRDeclare(IRBaseInstr):
    INSTR = IRFlag.DECLARE

    def __init__(self, var: Symbol, var_type: Symbol | CompositeSymbol):
        super().__init__(var, var_type, name=IRFlag.DECLARE)

    def __call__(self, *args, **kwargs):
        pass


class IRDeclareAssign(IRBaseInstr):
    INSTR = IRFlag.DECLARE_ASSIGN

    def __init__(
        self,
        var: Symbol,
        var_type: Symbol | CompositeSymbol,
        value: WorkingData
    ):
        super().__init__(var, var_type, value, name=IRFlag.DECLARE_ASSIGN)

    def __call__(self, *args, **kwargs):
        pass


class IRCallWithBody(IRBaseInstr):
    INSTR = IRFlag.CALL_WITH_BODY

    def __init__(
        self,
        caller: Symbol | CompositeSymbol,
        args: IRArgs,
        body: IRBlock | BlockRef
    ):
        super().__init__(caller, args, body, name=IRFlag.CALL_WITH_BODY)

    def __call__(self, *args, **kwargs):
        pass


class IROption(IRBaseInstr):
    INSTR = IRFlag.OPTION

    def __init__(
        self,
        option: WorkingData | IRBlock | BlockRef,
        body: WorkingData | IRBlock | BlockRef,
    ):
        super().__init__(option, body, name=IRFlag.OPTION)

    def __call__(self, *args, **kwargs):
        pass


class IRCallWithOption(IRBaseInstr):
    INSTR = IRFlag.CALL_WITH_OPTION

    def __init__(
        self,
        caller: Symbol | CompositeSymbol,
        args: IRArgs,
        *options: tuple[IROption, ...]
    ):
        super().__init__(caller, args, *options, name=IRFlag.CALL_WITH_BODY)

    def __call__(self, *args, **kwargs):
        pass


#################
# IR ROOT CLASS #
#################

class IR:
    """
    This class creates a new intermediate representation object that should
    hold the whole program code. The code can be only in terms of ``WorkingData``
    and ``IRBlock`` objects. An interpreter or compiler should evaluate its content.

    **Note**: function definitions must be created as separate ``IRBlock`` objects
    and populated in ``MemoryManager`` for further call/reference during evaluation.

    **Note2**: type definitions must be transformed from AST directly into
    ``BaseTypeDataStructure``.
    """

    table: dict[BlockRef, IRBlock]

    def __init__(self):
        self.table = dict()

    def add_ref(self, ref: BlockRef, code: IRBlock) -> None:
        self.table[ref] = code

    def add_new_block(self, block: IRBlock) -> None:
        if block.name not in self.table:
            self.add_ref(block.name, block)

            # iterate over each instruction to check for new blocks
            for k in block:

                match k:

                    # blocks will have the same check as above
                    case IRBlock():
                        if k.name not in self.table:
                            self.add_ref(k.name, k)

                    # instructions will have a check on their block_refs
                    case IRBaseInstr():

                        # iterating over all the blocks in the instruction
                        for p, q in k.block_refs.items():

                            if p not in self.table:
                                self.add_ref(p, q)

    def __iter__(self) -> Iterable:
        yield from self.table.items()

    def __repr__(self) -> str:
        content = ""
        for k, v in self:
            content += f"  {k}\n{v}\n"
        return f"[\n{content}]"
