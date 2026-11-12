from convert.formats.Fusion.Assembly.AssemblyGraph import VerifyAsmGraph
from convert.formats.Fusion.Assembly.AssemblyLinks import LinkOccurrences
from convert.formats.Fusion.Assembly.AssemblyModel import NativeAssembly
from convert.formats.Fusion.Assembly.AssemblyRecords import ReadAsmRecords
from convert.formats.Fusion.Assembly.AssemblyRoot import ResolveAsmRoot
from convert.formats.Fusion.RecordSpan import RecordSpan


# only a verified local occurrence graph can justify a native assembly projection
def ReadNativeAsm(
    BulkData: bytes, Spans: tuple[RecordSpan, ...]
) -> NativeAssembly | None:
    IndexValue = ReadAsmRecords(BulkData, Spans)
    if not (IndexValue.Components or IndexValue.Occurrences or IndexValue.Collections):
        return None
    RootValue = ResolveAsmRoot(IndexValue)
    Components = tuple(Entry.Component for Entry in IndexValue.Components.values())
    if len({Value.NativeGuid.casefold() for Value in Components}) != len(Components):
        raise ValueError("Duplicate Fusion component native guid")
    OccurrenceIds = {
        Value.NativeGuid.casefold() for Value in IndexValue.Occurrences.values()
    }
    if len(OccurrenceIds) != len(IndexValue.Occurrences):
        raise ValueError("Duplicate Fusion occurrence native guid")
    Linked = LinkOccurrences(IndexValue)
    VerifyAsmGraph(RootValue.ComponentId, set(IndexValue.Components), Linked)
    if not Linked:
        return None
    return NativeAssembly(
        RootValue.ComponentId,
        RootValue.Transform,
        Components,
        Linked,
    )
