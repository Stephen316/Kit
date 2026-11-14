from convert.formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.formats.Fusion.BrepCodec.Prism.PrismLayout import (
    KFirstFaceTag,
    KFirstSketchTag,
)
from convert.formats.Fusion.BrepCodec.Reading.ReadFeatureTag import ReadFeatureTag
from convert.formats.Fusion.BrepCodec.Reading.ReadSketchLink import ReadSketchLink
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


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
