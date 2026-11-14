from math import isfinite as IsFinite

from convert.formats.Fusion.MeshCodec.Model.ParaMesh import ParaMesh


def CheckGeometry(Value: ParaMesh) -> None:
    Count = len(Value.Positions)
    if not Count or not Value.Corners or len(Value.Corners) % 3:
        raise ValueError("Fusion mesh requires positions and triangle corners")
    if Count * 12 + len(Value.Corners) * 4 > 64 * 1024 * 1024:
        raise ValueError("Fusion mesh geometry allocation exceeds limit")
    if any(type(Index) is not int or not 0 <= Index < Count for Index in Value.Corners):
        raise ValueError("Fusion mesh corner references a missing vertex")
    if min(Value.Corners) != 0 or max(Value.Corners) != Count - 1:
        raise ValueError(
            "Fusion mesh corner range does not identify its initial vertex"
        )
    for Point in Value.Positions:
        if any(
            type(Number) is not float
            or not IsFinite(Number)
            or abs(Number) > 3.4028234663852886e38
            for Number in (Point.XCoord, Point.YCoord, Point.ZCoord)
        ):
            raise ValueError("Fusion mesh position is not a finite float32")
    if (
        type(Value.TerminalWord) is not int
        or not -(1 << 31) <= Value.TerminalWord < 1 << 31
    ):
        raise ValueError("Fusion mesh terminal corner word exceeds int32")
