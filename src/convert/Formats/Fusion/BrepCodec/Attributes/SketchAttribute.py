from convert.Formats.Fusion.BrepCodec.Attributes.MakeAttribute import MakeAttribute
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.Formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the sketch tag operation needs a consistent construction rule so native topology can resolve its owning modeling operation
def MakeSketchTag(Owner: int, Sketch: SketchLink) -> GeometryRecord:
    TextValue = f"{Sketch.PrimaryId} {Sketch.SecondaryId} {Sketch.Direction} {Sketch.TopologyRoleFlags} {Sketch.SplitSequenceId} {Sketch.SplitTotalNumber}"
    return MakeAttribute(Owner, "sketch_attrib_def", (1, 1, 3, CountedText(TextValue)))
