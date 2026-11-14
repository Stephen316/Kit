from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NoMergeAttrib import (
    NoMergeAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.StitchAttrib import (
    StitchAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.VertedgeAttrib import (
    KVertedgeCap,
    VertedgeAttrib,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord, KAsmToken


def MakeSysLinks(Links: AttribLinks) -> tuple[KAsmToken, ...]:
    return (
        (12, -1),
        (4, -1),
        (12, Links.NextAttrib),
        (12, Links.PriorAttrib),
        (12, Links.OwnerRef),
    )


def MakeStitchNode(Value: StitchAttrib) -> AsmRecord:
    if len(Value.HintValues) != 3:
        raise ValueError("Fusion stitch hint requires three doubles")
    return AsmRecord(
        "stitch_hint-sys-attrib",
        (*MakeSysLinks(Value.Links), *((6, Number) for Number in Value.HintValues)),
    )


def MakeVertedge(Value: VertedgeAttrib) -> AsmRecord:
    if not 0 <= len(Value.EdgeSlots) <= KVertedgeCap:
        raise ValueError("Fusion vertex edge list exceeds its bounds")
    Slots = tuple(
        Token
        for EdgeRef, SlotValue in Value.EdgeSlots
        for Token in ((12, EdgeRef), (4, SlotValue))
    )
    return AsmRecord(
        "vertedge-sys-attrib",
        (*MakeSysLinks(Value.Links), (4, len(Value.EdgeSlots)), *Slots),
    )


def MakeNoMerge(Value: NoMergeAttrib) -> AsmRecord:
    return AsmRecord("no_merge_attribute-st-attrib", MakeSysLinks(Value.Links))
