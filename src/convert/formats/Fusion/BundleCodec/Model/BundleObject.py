from dataclasses import dataclass as MakeDataClass
from typing import Literal

from convert.formats.Fusion.BundleCodec.Model.BundleRefs import BundleRefs
from convert.formats.Fusion.BundleCodec.Model.BundleText import BundleText


@MakeDataClass(frozen=True, slots=True)
class BundleObject:
    ObjectId: int
    Version: int
    VersionUrn: str
    LineageUrn: str
    StorageUrn: str
    MemberPath: str
    DownloadAs: str
    FriendlyName: str
    DisplayName: str
    ContentType: Literal["f3d", "f2d"]
    References: tuple[BundleRefs, ...]
    Metadata: tuple[BundleText, ...]
    CreatedAt: str | None
