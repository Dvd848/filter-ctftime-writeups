from enum import Enum

class FlattenableEnum(Enum):
    @classmethod
    def as_flat_dict(cls):
        res = {}
        for item in cls:
            res[str(item).replace(".", "_")] = item.value
        return res
