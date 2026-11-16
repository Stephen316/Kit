from convert.Formats.Fusion.BrepCodec.Prism.PrismLayout import KSketchOwners
from convert.Formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr, RequireAsm
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# map solid tags must resolve unambiguously so supporting records retain their owning document relationships
def MapSolidTags(Table: AsmTable, Mapping: dict[int, int]) -> dict[int, int]:
    TagValues = {
        88 + Index: ReadAsmPtr(RequireAsm(Table, Mapping[4 + Index], "face", 10), 0)
        for Index in range(6)
    }
    for Index, Owners in enumerate(KSketchOwners):
        for Offset, Owner in enumerate(Owners):
            TagValues[94 + 2 * Index + Offset] = ReadAsmPtr(
                RequireAsm(Table, Mapping[Owner], "coedge", 11), 0
            )
    return TagValues
