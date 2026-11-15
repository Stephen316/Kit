from base64 import urlsafe_b64encode as EncodeSafe
from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.DrawingCodec.Author.Model.DrawingIdentity import (
    DrawingIdentity,
)


# the identity operation needs a consistent construction rule so sheet objects retain their intended document relationships
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


# the fresh guid contract needs a shared interpretation so sheet objects retain their intended document relationships
def FreshGuid() -> str:
    return str(MakeUuid())


# the fresh token contract needs a shared interpretation so sheet objects retain their intended document relationships
def FreshToken() -> str:
    return EncodeSafe(MakeUuid().bytes).decode("ascii").rstrip("=")
