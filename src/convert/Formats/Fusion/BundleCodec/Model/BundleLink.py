from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BundleCodec.Model.BundleText import BundleText


# bundle link needs an explicit state contract so linked archive members retain their document relationships
@MakeDataClass(frozen=True, slots=True)
class BundleLink:
    TargetId: int
    Metadata: tuple[BundleText, ...]
