from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Round.SphereNode import SphereNode
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.formats.Fusion.BrepCodec.Journal.Validation.ReadLiveRef import ReadLiveRef
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def CheckWholeFace(
    FaceValue: AsmRecord, Surface: AsmRecord, Aliases: tuple[int, ...]
) -> None:
    Value = ReadEntityNode(Surface)
    if not isinstance(Value, (SphereNode, TorusNode)):
        raise ValueError(
            "Fusion face without loops requires a qualified closed periodic surface"
        )
    if any(
        Bound is not None
        for Bound in (Value.ULower, Value.UUpper, Value.VLower, Value.VUpper)
    ):
        raise ValueError("Fusion face without loops cannot retain surface bounds")
    if ReadLiveRef(FaceValue, 3, Aliases) != -1 or FaceValue.Tokens[9] != (11, None):
        raise ValueError(
            "Fusion whole periodic face must terminate its single-sided shell"
        )
