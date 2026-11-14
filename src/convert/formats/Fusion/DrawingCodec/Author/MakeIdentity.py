from base64 import urlsafe_b64encode as EncodeSafe
from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingIdentity import (
    DrawingIdentity,
)


def MakeIdentity() -> DrawingIdentity:
    return DrawingIdentity(
        DocumentId=FreshGuid(),
        VersionId=FreshGuid(),
        AssetId=FreshGuid(),
        RevisionId=FreshGuid(),
        LinkRole=FreshGuid(),
        ComponentGuid=FreshGuid(),
        ComponentRevision=FreshGuid(),
        InstanceGuid=FreshGuid(),
        DrawingToken=FreshToken(),
        DesignToken=FreshToken(),
        DrawingFile=FreshGuid(),
        DesignFile=FreshGuid(),
    )


def FreshGuid() -> str:
    return str(MakeUuid())


def FreshToken() -> str:
    return EncodeSafe(MakeUuid().bytes).decode("ascii").rstrip("=")
