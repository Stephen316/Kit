from dataclasses import dataclass as MakeDataClass
from typing import Literal

from convert.formats.Fusion.BundleCodec.Model.BundleLink import BundleLink


# bundle references needs an explicit state contract so linked archive members retain their document relationships
@MakeDataClass(frozen=True, slots=True)
class BundleRefs:
    KindValue: Literal["XREF", "DERIVED"]
    Targets: tuple[int, ...]
    Relations: tuple[BundleLink, ...]
