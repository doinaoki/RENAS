from enum import Enum, auto
class RelationType(Enum):
    BelongsC = auto()
    BelongsM = auto()
    BelongsF = auto()
    BelongsA = auto()
    BelongsL = auto()
    CoOccursM = auto()
    Extends = auto()
    Implements = auto()
    TypeM = auto()
    TypeV = auto()
    Invokes = auto()
    Accesses = auto()
    Assigns = auto()
    Passes = auto()
