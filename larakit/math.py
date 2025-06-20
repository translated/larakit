import math
import random
from dataclasses import dataclass, field
from typing import Iterable, Any, List


@dataclass
class Sequence:
    sum: float = field(init=False, default=0.0)
    sum2: float = field(init=False, default=0.0)
    length: int = field(init=False, default=0)

    def add(self, value: float) -> None:
        self.sum += value
        self.sum2 += value ** 2
        self.length += 1

    def merge(self, other: "Sequence") -> None:
        self.sum += other.sum
        self.sum2 += other.sum2
        self.length += other.length

    @property
    def mean(self) -> float:
        if self.length == 0:
            return math.nan
        return self.sum / self.length

    @property
    def stddev(self) -> float:
        if self.length <= 1:
            return math.nan

        avg = self.sum / self.length
        stddev = math.sqrt((self.sum2 / self.length) - (avg ** 2))
        return stddev


def reservoir_sampling(stream: Iterable[Any], size: int) -> List[Any]:
    result = []
    for i, tu in enumerate(stream):
        if i < size:
            result.append(tu)
        else:
            j = random.randint(0, i)
            if j < size:
                result[j] = tu

    return result
