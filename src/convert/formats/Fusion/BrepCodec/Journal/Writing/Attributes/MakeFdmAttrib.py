from math import isfinite as IsFinite

from convert.formats.Fusion.BrepCodec.Journal.Attributes.FeatureAttrib import (
    FeatureAttrib,
    KFeatureFlags,
    KFeatureLayouts,
    KFeatureTypes,
)
from convert.formats.Fusion.BrepCodec.Journal.Writing.Attributes.MakeAttribHead import (
    MakeAttribHead,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, KAsmToken


def MakeFdmAttrib(Value: FeatureAttrib) -> AsmRecord:
    if Value.DataName not in KFeatureLayouts:
        raise ValueError("Unsupported Fusion feature attribute data")
    Detailed = Value.DataName == "thread_face_data"
    Complete = len(Value.Points) == 3 and Value.TailCode is not None
    Empty = not Value.Points and Value.TailCode is None
    if (Detailed and not Complete) or (not Detailed and not Empty):
        raise ValueError("Fusion feature attribute layout disagrees with its data")
    if (
        Value.Flags != KFeatureFlags
        or Value.TypeCode != KFeatureTypes[Value.DataName]
        or Value.TailCode not in (None, 0, 1)
    ):
        raise ValueError("Unsupported Fusion feature attribute data")
    if not all(IsFinite(Number) for Point in Value.Points for Number in Point):
        raise ValueError("Fusion feature attribute points must be finite")
    Trailing: tuple[KAsmToken, ...] = ()
    if Value.TailCode is not None:
        Trailing = (*((19, Point) for Point in Value.Points), (4, Value.TailCode))
    return AsmRecord(
        "ATTRIB_CUSTOM-attrib",
        (
            *MakeAttribHead(Value.Links, "FDM_feature_attrib_def"),
            (4, 2),
            (4, 2),
            (7, Value.DataName),
            (4, 3),
            (4, Value.FeatureTag),
            (4, Value.Flags),
            (4, KFeatureLayouts[Value.DataName]),
            (4, Value.TypeCode),
            *Trailing,
        ),
    )
