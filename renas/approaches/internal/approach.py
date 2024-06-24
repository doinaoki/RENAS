from abc import ABCMeta, abstractmethod

from renas.approaches.util.rename import Rename

_RELATION_LIST = [
    "subclass",
    "subsubclass",
    "parents",
    "ancestor",
    "methods",
    "fields",
    "siblings",
    "comemnt",
    "type",
    "enclosingCLass",
    "assignment",
    "methodInvocated",
    "parameterArgument",
    "parameter",
    "enclosingMethod",
    "argument",
    "parameterOverload",
]

_RELATION_COST = {
    "subclass": 3.0,
    "subsubclass": 3.0,
    "parents": 3.0,
    "ancestor": 3.0,
    "methods": 4.0,
    "fields": 4.0,
    "siblings": 1.0,
    "comemnt": 2.0,
    "type": 3.0,
    "enclosingCLass": 4.0,
    "assignment": 1.0,
    "methodInvocated": 3.0,
    "parameterArgument": 2.0,
    "parameter": 3.0,
    "enclosingMethod": 3.0,
    "argument": 2.0,
    "parameterOverload": 1.0,
}

_IDENTIFIER_LIST = [
    "id",
    "name",
    "line",
    "files",
    "typeOfIdentifier",
    "split",
    "case",
    "pattern",
    "delimiter",
]


class Approach(metaclass=ABCMeta):

    def __init__(self):
        self.rename: Rename = None
        self.RELATION_LIST = _RELATION_LIST
        self.RELATION_COST = _RELATION_COST
        self.IDENTIFIER_LIST = _IDENTIFIER_LIST

    @abstractmethod
    def recommend(self):
        pass

    @abstractmethod
    def get_approach_name(self):
        return ""

    def get_operation(self):
        if self.rename is None:
            return []
        return self.rename.get_operation()

    def get_old_normalized(self):
        if self.rename is None:
            return []
        return self.rename.get_old_normalize()

    def get_id(self):
        if self.rename is None:
            return []
        return self.rename.get_id()
