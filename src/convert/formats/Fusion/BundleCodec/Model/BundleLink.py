from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BundleCodec.Model.BundleText import BundleText


@MakeDataClass(frozen=True, slots=True)
class BundleLink:
    TargetId: int
    Metadata: tuple[BundleText, ...]
