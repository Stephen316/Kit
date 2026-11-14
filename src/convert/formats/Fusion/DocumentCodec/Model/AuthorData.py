from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DocumentCodec.Materials.Model.AuthoredMat import AuthoredMat

from convert.formats.Fusion.DocumentCodec.Model.AuthorPolicy import AuthorPolicy
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.Model.DraftEntity import DraftEntity
from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema


@MakeDataClass(slots=True)
class AuthorData:
    SpecValue: DocumentSpec
    Policy: AuthorPolicy
    AssetId: str
    Schemas: tuple[NativeSchema, ...]
    ByName: dict[str, NativeSchema]
    ByGuid: dict[str, NativeSchema]
    Defaults: dict[str, dict[str, object]]
    Roles: dict[str, int]
    Entities: list[DraftEntity]
    NextId: int
    RevisionId: str
    ComponentId: str
    InstanceId: str
    BodyId: str
    BrepPart: str
    Materials: AuthoredMat | None = None
    FocusOrdinal: int = 1
