from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.Formats.Fusion.BrepCodec.Prism.PrismLayout import (
    KFirstFaceTag,
    KFirstSketchTag,
)
from convert.Formats.Fusion.BrepCodec.Reading.ReadFeatureTag import ReadFeatureTag
from convert.Formats.Fusion.BrepCodec.Reading.ReadSketchLink import ReadSketchLink
from convert.Formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# the prism tags operation needs a distinct decoding boundary so profile topology remains connected to its extrusion history
def ReadPrismTags(Table: AsmTable, Mapping: dict[int, int]) -> PrismTags:
    Faces = tuple(
        ReadFeatureTag(Table, Mapping[KFirstFaceTag + Index]) for Index in range(6)
    )
    Sketches = tuple(
        ReadSketchLink(Table, Mapping[KFirstSketchTag + 2 * Index])
        for Index in range(4)
    )
    for Index, Value in enumerate(Sketches):
        if ReadSketchLink(Table, Mapping[KFirstSketchTag + 2 * Index + 1]) != Value:
            raise ValueError("Prism paired coedge sketch links disagree")
    return PrismTags(Faces, Sketches)
