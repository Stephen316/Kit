from convert.formats.Fusion.BrepCodec.Attributes.MakeAttribute import MakeAttribute
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def MakeSketchTag(Owner: int, Sketch: SketchLink) -> GeometryRecord:
    TextValue = f"{Sketch.PrimaryId} {Sketch.SecondaryId} {Sketch.Direction} {Sketch.TopologyRoleFlags} {Sketch.SplitSequenceId} {Sketch.SplitTotalNumber}"
    return MakeAttribute(Owner, "sketch_attrib_def", (1, 1, 3, CountedText(TextValue)))
