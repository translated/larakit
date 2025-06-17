import math
from dataclasses import dataclass, field
from typing import Tuple


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

    def compute(self) -> Tuple[float, float]:
        if self.length == 0:
            return math.nan, math.nan
        if self.length == 1:
            return self.sum, math.nan

        avg = self.sum / self.length
        stddev = math.sqrt((self.sum2 / self.length) - (avg ** 2))
        return avg, stddev
