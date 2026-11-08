# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.geometry.models.VectorSpace import SpaceVector


# native placement encodes the affine translation around the independently owned center
def ScaleOffset(Center: SpaceVector, Factors: SpaceVector) -> SpaceVector:
    return SpaceVector(
        (1.0 - Factors.x) * Center.x,
        (1.0 - Factors.y) * Center.y,
        (1.0 - Factors.z) * Center.z,
    )


# active factor axes and any point placement share the same spreadsheet dependencies
def ScaleExprs(Refs: tuple[str, ...], PointName: str) -> list[tuple[str, str]]:
    Uniform = len(Refs) == 1
    Names = ("UniformScale",) if Uniform else ("XScale", "YScale", "ZScale")
    Result = list(zip(Names, Refs, strict=True))
    if PointName:
        Axes = Refs * 3 if Uniform else Refs
        Terms = "; ".join(
            f"{PointName}.Placement.Base.{Axis} * (1 - {Ref})"
            for Axis, Ref in zip("xyz", Axes, strict=True)
        )
        Result.append(
            (
                "Placement",
                f"placement(vector({Terms}); rotation(vector(0; 0; 1); 0 deg))",
            )
        )
    return Result
