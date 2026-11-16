from datetime import UTC, datetime as DateTime
from time import time_ns as ReadTimeNano

from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.BrepCodec.Prism.EmitPrismHist import EmitPrismHist
from convert.Formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.Formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy
from convert.Formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.Rectangle.CuboidFrame import CuboidFrame
from convert.Formats.Fusion.DocumentCodec.Rectangle.CuboidTags import CuboidTags
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.Formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody


# the prism part operation needs a consistent construction rule so model state retains its native feature and ownership relationships
def BuildPrismPart(
    SpecValue: DocumentSpec, Design: DesignResult
) -> tuple[ContainerPart, ...]:
    if Design.BrepPart is None:
        raise ValueError("Cuboid authoring requires a BRep part identity")
    Policy = AuthorPolicy()
    Model = CuboidBody(
        SpecValue.WidthMm, SpecValue.DepthMm, SpecValue.LengthMm, (0.0, 0.0, 0.0)
    )
    Identity = BodyIdentity(
        Policy.BodyKey,
        Policy.FirstOperationId + 1,
        Policy.CurveProgenitorTag + 4,
        ReadTimeNano() // 1000,
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
    Payload = EmitPrismHist(
        Model, Identity, CuboidTags(Policy), History, Stamp, CuboidFrame(Model)
    )
    return (ContainerPart("Breps.BlobParts/" + Design.BrepPart, Payload),)
