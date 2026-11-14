from datetime import UTC, datetime as DateTime
from time import time_ns as ReadTimeNano

from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.DocumentCodec.PartFeatures.BuildPartBody import (
    BuildPartBody,
)
from convert.formats.Fusion.DocumentCodec.Rectangle.BuildPrismPart import BuildPrismPart
from convert.formats.Fusion.DocumentCodec.Tapered.BuildTaperPart import BuildTaperPart


def BuildBodyPart(
    SpecValue: DocumentSpec, Design: DesignResult
) -> tuple[ContainerPart, ...]:
    if SpecValue.ProfileKind in ("cuboid", "part") and SpecValue.Features:
        return BuildPartBody(SpecValue, Design)
    if SpecValue.ProfileKind == "cuboid":
        return BuildPrismPart(SpecValue, Design)
    if SpecValue.ProfileKind == "frustum":
        return BuildTaperPart(SpecValue, Design)
    if SpecValue.ProfileKind != "extrusion":
        return ()
    if Design.BrepPart is None:
        raise ValueError("Extrusion authoring requires a BRep part identity")
    Policy = AuthorPolicy()
    Operations = (Policy.FirstOperationId + 1,)
    SketchId = Policy.FirstSketchTag + 2
    TagSet = TopologyTags(
        FeatureTag(Policy.SideFaceLabel, Operations),
        FeatureTag(Policy.TopFaceLabel, Operations),
        FeatureTag(Policy.BottomFaceLabel, Operations),
        FeatureTag(Policy.TopEdgeLabel, Operations),
        FeatureTag("-" + str(SketchId), Operations),
        SketchLink(SketchId, 0, 0, 1, 1),
    )
    Identity = BodyIdentity(
        Policy.BodyKey, Operations[0], Policy.BodyProgenitorTag, ReadTimeNano() // 1000
    )
    History = HistoryState(
        Policy.HistoryCurrentId,
        Policy.HistoryInitialId,
        Policy.HistoryCurrentStateId,
        Policy.HistoryNextEntityTag,
        Policy.HistoryBoardStatus,
        Policy.HistoryMaxStateId,
    )
    Stamp = GeometryStamp(
        "Kit", "Fusion native document codec", DateTime.now(UTC).isoformat()
    )
    Payload = EmitHistory(
        CylinderBody(SpecValue.RadiusMm, SpecValue.LengthMm, (0.0, 0.0, 0.0)),
        Identity,
        TagSet,
        History,
        Stamp,
    )
    return (ContainerPart("Breps.BlobParts/" + Design.BrepPart, Payload),)
