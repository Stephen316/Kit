from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BundleCodec.Model.BundleFile import BundleFile
from convert.formats.Fusion.BundleCodec.Model.BundleModel import BundleModel


@MakeDataClass(frozen=True, slots=True)
class FusionBundle:
    Description: BundleModel
    Documents: tuple[BundleFile, ...]
