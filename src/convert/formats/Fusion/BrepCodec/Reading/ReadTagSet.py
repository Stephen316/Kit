from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.BrepCodec.Reading.ReadFeatureTag import ReadFeatureTag
from convert.formats.Fusion.BrepCodec.Reading.ReadSketchLink import ReadSketchLink
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


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
