from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.Formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger

# the feature layouts vocabulary must stay centralized so journal reconstruction agrees on supported native identities
KFeatureLayouts: dict[str, int] = {"feature_data": 2, "thread_face_data": 6}

# the feature types vocabulary must stay centralized so journal reconstruction agrees on supported native identities
KFeatureTypes: dict[str, int] = {"feature_data": 1902, "thread_face_data": 1901}

# feature flags must remain consistent across callers so topology changes retain their native revision relationships
KFeatureFlags = 2097152


# feature attribute needs an explicit state contract so topology changes retain their native revision relationships
@MakeDataClass(frozen=True, slots=True)
class FeatureAttrib:
    Links: AttribLinks
    DataName: str
    FeatureTag: int
    Flags: int
    TypeCode: int
    Points: tuple[KJournalVector, ...] = ()
    TailCode: int | None = None

    # invalid feature attribute state must fail at construction so journal reconstruction never receives an inconsistent contract
    def __post_init__(self) -> None:
        CheckInteger(
            self.FeatureTag, "feature attribute tag", Lower=0, Upper=(1 << 31) - 1
        )
