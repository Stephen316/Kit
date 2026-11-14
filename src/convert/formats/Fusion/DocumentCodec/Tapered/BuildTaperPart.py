from datetime import UTC, datetime as DateTime
from time import time_ns as ReadTimeNano

from convert.formats.Fusion.BrepCodec.Frustum.EmitFrustumHist import EmitFrustumHist
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.Tapered.TaperModel import TaperModel
from convert.formats.Fusion.DocumentCodec.Tapered.TaperTags import TaperTags
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


def BuildTaperPart(
    SpecValue: DocumentSpec, Design: DesignResult
) -> tuple[ContainerPart, ...]:
    if Design.BrepPart is None:
        raise ValueError("Frustum authoring requires a BRep part identity")
    Policy = AuthorPolicy()
    Identity = BodyIdentity(
        Policy.BodyKey,
        Policy.FirstOperationId + 1,
        Policy.BodyProgenitorTag,
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
    Payload = EmitFrustumHist(
        TaperModel(SpecValue), Identity, TaperTags(Policy), History, Stamp
    )
    return (ContainerPart("Breps.BlobParts/" + Design.BrepPart, Payload),)
