from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import KEdgeCorners


def BuildCurves(
    Corners: tuple[tuple[float, float, float], ...],
) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "straight-curve",
            (
                Corners[Start],
                (
                    Corners[Finish][0] - Corners[Start][0],
                    Corners[Finish][1] - Corners[Start][1],
                    Corners[Finish][2] - Corners[Start][2],
                ),
                KeywordToken("I"),
                KeywordToken("I"),
            ),
        )
        for Start, Finish in KEdgeCorners
    )
