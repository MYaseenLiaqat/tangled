from collections.abc import Callable
from typing import Protocol


class Jobs(Protocol):
    def enqueue(self, function: Callable, *args, **kwargs) -> None: ...
