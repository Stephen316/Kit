from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.PartTopology import (
    MeasurePart,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart
from interchange.Features.FeatureBody import DesignBody
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordTopology import TopologyCounts


# the part body operation needs a consistent construction rule so public document claims remain grounded in native records
def MakePartBody(SpecValue: DocumentSpec) -> DesignBody:
    _, Stages = SolvePart(SpecValue)
    if not Stages:
        raise ValueError("Fusion part body requires at least one feature")
    Measured = MeasurePart(Stages[-1].After)
    Lower = tuple(Value * 10.0 for Value in Measured.LowerCm)
    Upper = tuple(Value * 10.0 for Value in Measured.UpperCm)
    Counts = TopologyCounts(
        1,
        1,
        Measured.FaceCount,
        Measured.EdgeCount,
        Measured.VertexCount,
        Measured.VolumeCm * 1000.0,
        Measured.AreaCm * 100.0,
        BoundingBox(SpaceVector(*Lower), SpaceVector(*Upper)),
        True,
    )
    return DesignBody(
        "body",
        SpecValue.BodyName,
        "feature" + str(len(Stages)),
        Counts,
        "material",
    )
