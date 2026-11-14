from datetime import UTC, datetime as DateTime
from time import time_ns as ReadTimeNano

from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Prism.EmitPrismHist import EmitPrismHist
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.Rectangle.CuboidFrame import CuboidFrame
from convert.formats.Fusion.DocumentCodec.Rectangle.CuboidTags import CuboidTags
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody


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
