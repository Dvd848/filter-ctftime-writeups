from enum import Enum

def enum_to_dict(enumeration: Enum):
    res = {}
    for item in enumeration:
        res[str(item).replace(".", "_")] = item.value
    return res