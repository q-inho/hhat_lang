from __future__ import annotations

from hhat_lang.core.data.core import Symbol
from hhat_lang.core.types import POINTER_SIZE
from hhat_lang.core.types.abstract_base import QSize, Size
from hhat_lang.core.types.builtin_base import BuiltinSingleDS

#######################
# BUILT-IN DATA TYPES #
#######################

# ---------- #
# classical  #
# ---------- #

Int = BuiltinSingleDS(Symbol("int"), Size(64))
Bool = BuiltinSingleDS(Symbol("bool"), Size(8))
U16 = BuiltinSingleDS(Symbol("u16"), Size(16))
U32 = BuiltinSingleDS(Symbol("u32"), Size(32))
U64 = BuiltinSingleDS(Symbol("u64"), Size(64))
I16 = BuiltinSingleDS(Symbol("i16"), Size(16))
I32 = BuiltinSingleDS(Symbol("i32"), Size(32))
I64 = BuiltinSingleDS(Symbol("i64"), Size(64))
Float = BuiltinSingleDS(Symbol("float"), Size(64))
F32 = BuiltinSingleDS(Symbol("f32"), Size(32))
F64 = BuiltinSingleDS(Symbol("f64"), Size(64))


# -------- #
# quantum  #
# -------- #

QBool = BuiltinSingleDS(Symbol("@bool"), Size(POINTER_SIZE), qsize=QSize(1))
QU2 = BuiltinSingleDS(Symbol("@u2"), Size(POINTER_SIZE), qsize=QSize(2))
QU3 = BuiltinSingleDS(Symbol("@u3"), Size(POINTER_SIZE), qsize=QSize(3))
QU4 = BuiltinSingleDS(Symbol("@u4"), Size(POINTER_SIZE), qsize=QSize(4))


# ---------------------------------- #
# list with all built-in data types  #
# ---------------------------------- #

builtins_types = {
    # classical
    "int": Int,
    "float": Float,
    "bool": Bool,
    "u16": U16,
    "u32": U32,
    "u64": U64,
    "i16": I16,
    "i32": I32,
    "i64": I64,
    "f32": F32,
    "f64": F64,

    # quantum
    "@bool": QBool,
    "@u2": QU2,
    "@u3": QU3,
    "@u4": QU4,
}
