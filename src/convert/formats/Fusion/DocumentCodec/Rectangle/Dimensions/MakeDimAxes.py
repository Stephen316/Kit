from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.Rectangle.Dimensions.Model.DimensionAxis import (
    DimensionAxis,
)


def MakeDimAxes(SpecValue: DocumentSpec) -> tuple[DimensionAxis, ...]:
    return (
        DimensionAxis(
            "width",
            SpecValue.WidthParamName,
            SpecValue.WidthMm,
            ("corner_a", "corner_b"),
            (0.0, 0.0, 0.0),
            (SpecValue.WidthMm / 10.0, 0.0, 0.0),
            (0.0, -0.5, 0.0),
            1 << 22,
        ),
        DimensionAxis(
            "depth",
            SpecValue.DepthParamName,
            SpecValue.DepthMm,
            ("corner_d", "corner_a"),
            (0.0, SpecValue.DepthMm / 10.0, 0.0),
            (0.0, 0.0, 0.0),
            (-0.5, 0.0, 0.0),
            1 << 23,
        ),
    )
