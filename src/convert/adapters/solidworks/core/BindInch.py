from __future__ import annotations as Annotations

from dataclasses import replace as Replace
from typing import TYPE_CHECKING as TypeChecking

from convert.adapters.solidworks.core.InchDecimal import InchDecimal
from convert.adapters.solidworks.core.InchScalar import IsRoundedInch
from interchange.features.DistanceParam import KLengthFactors

if TypeChecking:
    from convert.adapters.solidworks.core.Native import NativeDimension, NativeScalar

KUnresolvedInchDimension = "unresolved_inch_dimension"


def BindInch(
    Dimension: NativeDimension, Scalars: tuple[NativeScalar, ...], Decimals: int | None
) -> NativeDimension:
    Displayed = InchDecimal(Dimension.source_text)
    Unresolved = Replace(
        Dimension,
        value_mm=None,
        inch_display_value=Displayed[0] if Displayed is not None else None,
    )
    Named = [Scalar for Scalar in Scalars if Scalar.name == Dimension.name]
    if (
        not Dimension.name
        or Decimals is None
        or Displayed is None
        or Displayed[1] > Decimals
        or len(Named) != 1
    ):
        return Unresolved
    Scalar = Named[0]
    if (
        Scalar.object_id is None
        or Scalar.role not in {"driving", "native"}
        or not IsRoundedInch(Displayed[0], Scalar.value, Decimals)
    ):
        return Unresolved
    return Replace(
        Dimension,
        value_mm=Scalar.value * KLengthFactors["m"],
        native_value=Scalar.value,
        native_offset=Scalar.value_offset,
        native_role=Scalar.role,
        operands=Scalar.operands,
        inch_display_value=None,
    )
