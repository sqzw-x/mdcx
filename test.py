from dataclasses import dataclass
from typing import Literal


@dataclass
class Test:
    a: int
    b: str
    c: Literal[0, 1] = 0

    def __str__(self):
        return f"Test(a={self.a}, b='{self.b}', c={self.c})"
