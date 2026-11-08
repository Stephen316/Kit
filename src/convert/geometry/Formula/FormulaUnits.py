# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose as IsClose, isfinite as IsFinite, pi as HalfTurn

from interchange.enums.EnumValues import ValueKind
from interchange.features.DistanceParam import KLengthFactors
from interchange.records.RecordParameter import ParameterValue

# independent exponents keep angles distinct from lengths and unitless scalars
KDimension = tuple[int, int]

# internal canonical magnitudes remain independent of spreadsheet display units
KQuantity = tuple[float, KDimension]

# native arithmetic accepts only units with a known physical conversion factor
KFormulaUnits: dict[str, KQuantity] = {
    **{UnitName: (Factor, (1, 0)) for UnitName, Factor in KLengthFactors.items()},
    "rad": (1.0, (0, 1)),
    "deg": (HalfTurn / 180.0, (0, 1)),
    "": (1.0, (0, 0)),
}

# quantity kinds must agree with the physical meaning of their declared unit
KFormulaKinds: dict[ValueKind, KDimension] = {
    ValueKind.KLength: (1, 0),
    ValueKind.KAngle: (0, 1),
    ValueKind.KNumber: (0, 0),
    ValueKind.KInteger: (0, 0),
}


# interpreting each stored value before evaluation prevents dimensionless coercion
def GetQuantity(Value: ParameterValue) -> KQuantity | None:
    UnitData = KFormulaUnits.get(Value.unit)
    if UnitData is None or KFormulaKinds.get(Value.kind) != UnitData[1]:
        return None
    Magnitude = Value.value
    if type(Magnitude) not in (int, float):
        return None
    try:
        Scalar = Magnitude * UnitData[0]
    except OverflowError:
        return None
    return (Scalar, UnitData[1]) if IsFinite(Scalar) else None


# stored native values corroborate both arithmetic and units before links are trusted
def MatchQuantity(Result: KQuantity, Expected: ParameterValue) -> bool:
    Stored = GetQuantity(Expected)
    return (
        Stored is not None
        and Stored[1] == Result[1]
        and IsClose(Stored[0], Result[0], rel_tol=1e-12, abs_tol=1e-12)
    )
