from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import KEdgeCorners


# the curves operation needs a consistent construction rule so geometric values retain their native record boundaries
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
