import random
from typing import Any, List, Iterable


def reservoir(stream: Iterable[Any], sample_size: int) -> List[Any]:
    result = []
    for i, tu in enumerate(stream):
        if i < sample_size:
            result.append(tu)
        else:
            j = random.randint(0, i)
            if j < sample_size:
                result[j] = tu

    return result
