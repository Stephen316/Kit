from __future__ import annotations as Annotations

from typing import TYPE_CHECKING as TypeChecking

if TypeChecking:
    from convert.adapters.solidworks.core.Native import NativeScalar


# feature owned name indexing preserves ambiguity checks across many dimensions
def IndexInch(Scalars: tuple[NativeScalar, ...]) -> dict[str, tuple[NativeScalar, ...]]:
    NamedScalars: dict[str, list[NativeScalar]] = {}
    for Scalar in Scalars:
        NamedScalars.setdefault(Scalar.name, []).append(Scalar)
    return {NameValue: tuple(Values) for NameValue, Values in NamedScalars.items()}
