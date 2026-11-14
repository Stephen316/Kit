from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue


@MakeDataClass(frozen=True, slots=True)
class EntityFrame:
    RootId: str
    Subjects: tuple[SubjectValue, ...] | None
    Metadata: tuple[NamedMetadata, ...] | None
