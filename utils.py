from enum import Enum
from typing import Dict

class FlattenableEnum(Enum):
    """An enumerations which can be flattened to a dictionary of strings.

    This class extends the standard Enum type, adding an as_flat_dict() method 
    which exports the enum values to a dictionary of strings.

    Example:
        >>> class Color(FlattenableEnum):
        ...     RED = 1
        ...     GREEN = 2
        ...     BLUE = 3
        >>> Color.as_flat_dict()
        {'Color.RED': '1', 'Color.GREEN': '2', 'Color.BLUE': '3'}
    """
    @classmethod
    def as_flat_dict(cls) -> Dict[str, str]:
        res = {}
        for item in cls:
            res[str(item)] = str(item.value)
        return res
