from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.BrepCodec.Reading.ReadFeatureTag import ReadFeatureTag
from convert.Formats.Fusion.BrepCodec.Reading.ReadSketchLink import ReadSketchLink
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# the tag set operation needs a distinct decoding boundary so topology identity survives native history reconstruction
def ReadTagSet(
    Table: AsmTable, Mapping: dict[int, int], HasHistory: bool
) -> TopologyTags:
    Offset = 28 if HasHistory else 48
    Faces = tuple(
        ReadFeatureTag(Table, Mapping[Index]) for Index in range(Offset, Offset + 5)
    )
    return TopologyTags(
        Faces[0],
        Faces[1],
        Faces[2],
        Faces[3],
        Faces[4],
        ReadSketchLink(Table, Mapping[Offset + 5]),
    )
