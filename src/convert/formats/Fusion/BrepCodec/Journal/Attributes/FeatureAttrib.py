from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger

KFeatureLayouts: dict[str, int] = {"feature_data": 2, "thread_face_data": 6}
KFeatureTypes: dict[str, int] = {"feature_data": 1902, "thread_face_data": 1901}
KFeatureFlags = 2097152


@MakeDataClass(frozen=True, slots=True)
class FeatureAttrib:
    Links: AttribLinks
    DataName: str
    FeatureTag: int
    Flags: int
    TypeCode: int
    Points: tuple[KJournalVector, ...] = ()
    TailCode: int | None = None

    def __post_init__(self) -> None:
        CheckInteger(
            self.FeatureTag, "feature attribute tag", Lower=0, Upper=(1 << 31) - 1
        )
