from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from tests.convert.formats.FusionCodec.Documents.Dimensions.DimensionFields import (
    DimensionRows,
)


def CheckDimSlots(Model: DocumentModel) -> None:
    Settings = DimensionRows(Model, "AssetSettings")[0].ObjectId
    Indices: list[int] = []
    for Segment in Model.Segments:
        for Record in Segment.Records:
            for Subject in Record.Frame.Subjects or ():
                Target = Subject.Target
                if isinstance(Target, LocalRef):
                    IsDesign = Segment.Metadata.Header.SegmentId == 0
                elif isinstance(Target, SegmentRef):
                    IsDesign = Target.SegmentId == 0
                else:
                    continue
                if IsDesign and Target.ObjectId == Settings:
                    Indices.append(Subject.ObserverIndex)
    assert sorted(Indices) == [0, 1, 2, 3]
    Dimensions = DimensionRows(Model, "FusionSketchLinearDim")
    assert Dimensions[0].Frame.Subjects is not None
    assert Dimensions[1].Frame.Subjects is not None
    assert tuple(Subject.ObserverIndex for Subject in Dimensions[0].Frame.Subjects) == (
        0,
        0,
        0,
    )
    assert tuple(Subject.ObserverIndex for Subject in Dimensions[1].Frame.Subjects) == (
        1,
        1,
        0,
    )
