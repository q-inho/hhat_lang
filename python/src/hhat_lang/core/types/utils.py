from __future__ import annotations

from enum import Enum, auto


class BaseTypeEnum(Enum):
    """Enum data type structures for ``BaseTypeDataStructure`` instances"""

    SINGLE = auto()
    STRUCT = auto()
    ENUM = auto()
    UNION = auto()

    REMOTE_UNION = auto()
    """
    ``REMOTE_UNION``: a new data structure to be used in the future to handle remote 
    quantum data; name yet to be settled
    """
