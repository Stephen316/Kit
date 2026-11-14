from convert.formats.Fusion.BrepCodec.Prism.Reading.PrismTokens import PrismTokens
from convert.formats.Fusion.BrepCodec.Reading.CheckTopology import CheckTopology
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.PrismSnapshot import (
    PrismSnapshot,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.MapRegion import (
    MapRegion,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.ReadRegion import (
    ReadRegion,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.ReadSnapWire import (
    ReadSnapWire,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Reading.ReadSolid import (
    ReadSolid,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Validation.CheckSnapshot import (
    CheckSnapshot,
)
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Writing.SnapRecords import (
    SnapRecords,
)
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody


def ReadPrismSnap(Payload: bytes) -> PrismSnapshot:
    WireValue = ReadSnapWire(Payload)
    Frame, TagSet, Mapping = ReadSolid(WireValue.Table)
    Mapping.update(MapRegion(WireValue.Table, 2, 88, 152))
    Mapping.update(MapRegion(WireValue.Table, 3, 113, 160))
    if set(Mapping) != set(range(168)) or set(Mapping.values()) != set(range(168)):
        raise ValueError("Unsupported cuboid snapshot inventory or aliases")
    Lower, Upper = Frame.CornersCm[0], Frame.CornersCm[7]
    Model = CuboidBody(
        (Upper[0] - Lower[0]) * 10,
        (Upper[1] - Lower[1]) * 10,
        (Upper[2] - Lower[2]) * 10,
        (Lower[0] * 10, Lower[1] * 10, Lower[2] * 10),
    )
    Value = PrismSnapshot(
        Model,
        TagSet,
        WireValue.Stamp,
        WireValue.Header,
        Frame,
        ReadRegion(WireValue.Table, Mapping, 88, 152),
        ReadRegion(WireValue.Table, Mapping, 113, 160),
    )
    CheckSnapshot(Value)
    CheckTopology(PrismTokens(SnapRecords(Value)), WireValue.Table, Mapping)
    return Value
