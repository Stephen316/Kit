from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgPackPlan import DwgPackPlan
from convert.formats.Fusion.DrawingCodec.Dwg.Pack.EncodeLong import EncodeCount
from convert.formats.Fusion.DrawingCodec.Dwg.Pack.EncodeMatch import EncodeMatch


def IsMatchValid(DataValue: bytes, Position: int, Length: int, Distance: int) -> bool:
    Source = Position - Distance - 1
    if Source < 0 or Position + Length > len(DataValue):
        return False
    return all(
        DataValue[Source + Index] == DataValue[Position + Index]
        for Index in range(Length)
    )


def PackPage(DataValue: bytes, PackPlan: DwgPackPlan) -> bytes:
    Output = bytearray()
    Position = PackPlan.LeadCount
    if Position:
        Output += EncodeCount(Position) + DataValue[:Position]
    for Length, Distance, Literal in PackPlan.PackSteps:
        if not IsMatchValid(DataValue, Position, Length, Distance):
            raise ValueError("DWG pack plan match does not reproduce the page data")
        Output += EncodeMatch(Length, Distance, Literal if Literal <= 3 else 0)
        Position += Length
        if Literal > 3:
            Output += EncodeCount(Literal)
        Output += DataValue[Position : Position + Literal]
        Position += Literal
    if Position != len(DataValue):
        raise ValueError("DWG pack plan does not cover the page data")
    return bytes(Output) + b"\x11\x00\x00"
