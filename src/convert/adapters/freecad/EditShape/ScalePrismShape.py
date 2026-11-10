# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.adapters.freecad.EditShape.Prism.PrismRaw import ReadPrismRaw
from convert.adapters.freecad.EditShape.PrismShape import IsPrismMatch, KMaxPrismBytes
from convert.adapters.freecad.EditShape.Scale.ScaleExpected import ScaleExpected
from convert.adapters.freecad.EditShape.Scale.ScalePlaces import CheckScaleRoot
from convert.adapters.freecad.EditShape.Scale.ScaleSplineRaw import ReadScaleSpline
from convert.geometry.Opencascade import DecodeFailure
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.VectorSpace import SpaceVector


# scale readback needs independent proof for both native carrier forms and kit seeds
def IsScalePrism(ShapeData: bytes, Expected: BrepModel, RootShift: SpaceVector) -> bool:
    if not ShapeData or len(ShapeData) > KMaxPrismBytes:
        return False
    try:
        ExpectedValue = ScaleExpected(Expected)
        Sides = len(ExpectedValue.Points) // 2
        try:
            RawValue = ReadPrismRaw(ShapeData, Sides, AllowRootTrim=True)
        except DecodeFailure:
            RawValue = ReadScaleSpline(ShapeData, Sides)
        CheckScaleRoot(RawValue, RootShift)
        return IsPrismMatch(RawValue, ExpectedValue)
    except (KeyError, OverflowError, ValueError):
        return False
