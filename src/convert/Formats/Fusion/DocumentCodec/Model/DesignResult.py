from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DocumentCodec.Materials.Model.AuthoredMat import AuthoredMat

from convert.Formats.Fusion.ContainerCodec.Model.SegmentStreams import SegmentStreams
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Schema.EntityProfile import EntityProfile


# design result needs an explicit state contract so model state retains its native feature and ownership relationships
@MakeDataClass(frozen=True, slots=True)
class DesignResult:
    Streams: SegmentStreams
    Records: tuple[EntityRecord, ...]
    Profile: EntityProfile
    Roles: dict[str, int]
    ComponentId: str
    InstanceId: str
    RevisionId: str
    AssetId: str
    NextId: int
    BrepPart: str | None
    BodyId: str | None
    Materials: AuthoredMat | None = None
