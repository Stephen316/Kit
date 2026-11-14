from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgPackPlan import DwgPackPlan

KFarLimit = 0x7FFE


def FindMatch(
    DataValue: bytes, Position: int, Recent: dict[bytes, int]
) -> tuple[int, int]:
    Source = Recent.get(DataValue[Position : Position + 3])
    if Source is None or Position + 3 > len(DataValue):
        return 0, 0
    Length = 0
    Limit = len(DataValue) - Position
    while Length < Limit and DataValue[Source + Length] == DataValue[Position + Length]:
        Length += 1
    Distance = Position - Source - 1
    if Distance > KFarLimit or (Distance > 0x3FFF and Length < 4):
        return 0, 0
    return Length, Distance


def PlanPage(DataValue: bytes) -> DwgPackPlan:
    LeadCount = min(4, len(DataValue))
    Recent: dict[bytes, int] = {}
    PackSteps: list[list[int]] = []
    Position = 0
    while Position < len(DataValue):
        Length, Distance = (
            (0, 0) if Position < 4 else FindMatch(DataValue, Position, Recent)
        )
        Advance = max(Length, 1)
        for Index in range(Position, Position + Advance):
            Recent[DataValue[Index : Index + 3]] = Index
        if Length:
            PackSteps.append([Length, Distance, 0])
        elif PackSteps:
            PackSteps[-1][2] += 1
        elif Position >= 4:
            LeadCount += 1
        Position += Advance
    return DwgPackPlan(
        LeadCount,
        tuple((PackStep[0], PackStep[1], PackStep[2]) for PackStep in PackSteps),
    )
