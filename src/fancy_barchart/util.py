from typing import TypeVar


A: TypeVar = TypeVar("A")
B: TypeVar = TypeVar("B")


def alternate(a: A, b: A, /, *, num: int) -> list[A | B]:
    """Return ``a`` and ``b`` as an ``num``-element alternated list: ``[a, b, a, b, a, …]``"""
    return ([a, b] * ((num + 1) // 2))[:num]
