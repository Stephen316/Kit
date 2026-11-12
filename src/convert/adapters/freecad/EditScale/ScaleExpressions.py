from interchange.geometry.models.VectorSpace import SpaceVector


# native placement encodes the affine translation around the independently owned center
def ScaleOffset(Center: SpaceVector, Factors: SpaceVector) -> SpaceVector:
    return SpaceVector(
        (1.0 - Factors.x) * Center.x,
        (1.0 - Factors.y) * Center.y,
        (1.0 - Factors.z) * Center.z,
    )


# active factor axes and any point placement share the same spreadsheet dependencies
def ScaleExprs(References: tuple[str, ...], PointName: str) -> list[tuple[str, str]]:
    Uniform = len(References) == 1
    Names = ("UniformScale",) if Uniform else ("XScale", "YScale", "ZScale")
    Result: list[tuple[str, str]] = list(zip(Names, References, strict=True))
    if PointName:
        AxisValues = References * 3 if Uniform else References
        Terms = "; ".join(
            f"{PointName}.Placement.Base.{AxisValue} * (1 - {ReferenceValue})"
            for AxisValue, ReferenceValue in zip("xyz", AxisValues, strict=True)
        )
        Result.append(
            (
                "Placement",
                f"placement(vector({Terms}); rotation(vector(0; 0; 1); 0 deg))",
            )
        )
    return Result
