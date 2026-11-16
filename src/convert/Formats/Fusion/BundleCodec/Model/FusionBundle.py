from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BundleCodec.Model.BundleFile import BundleFile
from convert.Formats.Fusion.BundleCodec.Model.BundleModel import BundleModel


# fusion bundle needs an explicit state contract so linked archive members retain their document relationships
@MakeDataClass(frozen=True, slots=True)
class FusionBundle:
    Description: BundleModel
    Documents: tuple[BundleFile, ...]
