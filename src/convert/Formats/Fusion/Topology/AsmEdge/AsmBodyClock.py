from convert.Formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.Formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import (
    ReadEntityNode,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import (
    ReadAsmInt,
    ReadAsmPtr,
    ReadAsmText,
    RequireAsm,
)
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# a timestamp qualifies only when its body and naming attribute reciprocate the same chain
def ReadBodyClock(Table: AsmTable, BodyIndex: int, Handle: int) -> int:
    BodyValue = RequireAsm(Table, BodyIndex, "body", 6)
    ClockIndex = ReadAsmPtr(BodyValue, 0)
    Clock = ReadEntityNode(RequireAsm(Table, ClockIndex, "ATTRIB_CUSTOM-attrib", 8))
    if (
        ReadAsmInt(BodyValue, 1) != Handle
        or not isinstance(Clock, TimeAttrib)
        or Clock.Links.OwnerRef != BodyIndex
        or Clock.Links.PriorAttrib != -1
        or not Clock.UnixMicros.is_integer()
        or not 0 < Clock.UnixMicros < (1 << 53)
    ):
        raise ValueError("Fusion ASM body timestamp disagrees with its owner")
    NameValue = RequireAsm(Table, Clock.Links.NextAttrib, "ATTRIB_CUSTOM-attrib")
    if ReadAsmText(NameValue, 5) != "generic_tag_attrib_def" or tuple(
        ReadAsmPtr(NameValue, Index) for Index in (2, 3, 4)
    ) != (-1, ClockIndex, BodyIndex):
        raise ValueError("Fusion ASM body timestamp chain does not close")
    return int(Clock.UnixMicros)
