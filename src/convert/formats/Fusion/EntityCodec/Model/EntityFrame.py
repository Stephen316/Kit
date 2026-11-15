from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue


# entity frame needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class EntityFrame:
    RootId: str
    Subjects: tuple[SubjectValue, ...] | None
    Metadata: tuple[NamedMetadata, ...] | None
